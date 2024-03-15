import asyncio
import os
import signal
import subprocess
import sys
from contextlib import asynccontextmanager
from dataclasses import dataclass
from typing import (
    IO,
    Any,
    Callable,
    Iterable,
    Mapping,
    Sequence,
    TextIO,
)

import anyio
import anyio.abc
from anyio.streams.text import TextReceiveStream, TextSendStream
from rich.console import Console
from rich.status import Status

TextSink = anyio.AsyncFile | TextIO | TextSendStream

console = Console()

if sys.platform == "win32":
    from ctypes import WINFUNCTYPE, c_int, c_uint, windll

    _windows_process_group_pids = set()

    @WINFUNCTYPE(c_int, c_uint)
    def _win32_ctrl_handler(dwCtrlType):
        """
        A callback function for handling CTRL events cleanly on Windows. When called,
        this function will terminate all running win32 subprocesses the current
        process started in new process groups.
        """
        for pid in _windows_process_group_pids:
            try:
                os.kill(pid, signal.CTRL_BREAK_EVENT)
            except OSError:
                # process is already terminated
                pass

        # returning 0 lets the next handler in the chain handle the signal
        return 0

    # anyio process wrapper classes
    @dataclass(eq=False)
    class StreamReaderWrapper(anyio.abc.ByteReceiveStream):
        _stream: asyncio.StreamReader

        async def receive(self, max_bytes: int = 65536) -> bytes:
            data = await self._stream.read(max_bytes)
            if data:
                return data
            else:
                raise anyio.EndOfStream

        async def aclose(self) -> None:
            self._stream.feed_eof()

    @dataclass(eq=False)
    class StreamWriterWrapper(anyio.abc.ByteSendStream):
        _stream: asyncio.StreamWriter

        async def send(self, item: bytes) -> None:
            self._stream.write(item)
            await self._stream.drain()

        async def aclose(self) -> None:
            self._stream.close()

    @dataclass(eq=False)
    class Process(anyio.abc.Process):
        _process: asyncio.subprocess.Process
        _stdin: StreamWriterWrapper | None
        _stdout: StreamReaderWrapper | None
        _stderr: StreamReaderWrapper | None

        async def aclose(self) -> None:
            if self._stdin:
                await self._stdin.aclose()
            if self._stdout:
                await self._stdout.aclose()
            if self._stderr:
                await self._stderr.aclose()

            await self.wait()

        async def wait(self) -> int:
            return await self._process.wait()

        def terminate(self) -> None:
            self._process.terminate()

        def kill(self) -> None:
            self._process.kill()

        def send_signal(self, signal: int) -> None:
            self._process.send_signal(signal)

        @property
        def pid(self) -> int:
            return self._process.pid

        @property
        def returncode(self) -> int | None:
            return self._process.returncode

        @property
        def stdin(self) -> anyio.abc.ByteSendStream | None:
            return self._stdin

        @property
        def stdout(self) -> anyio.abc.ByteReceiveStream | None:
            return self._stdout

        @property
        def stderr(self) -> anyio.abc.ByteReceiveStream | None:
            return self._stderr

    async def _open_anyio_process(
        command: str | bytes | Sequence[str | bytes],
        *,
        stdin: int | IO[Any] | None,
        stdout: int | IO[Any] | None = None,
        stderr: int | IO[Any] | None = None,
        cwd: str | bytes | anyio.Path | None = None,
        env: Mapping[str, str] | None = None,
        start_new_session: bool = False,
        **kwargs,
    ):
        """
        Open a subprocess and return a `Process` object.

        Args:
            command: The command to run
            kwargs: Additional arguments to pass to `asyncio.create_subprocess_exec`

        Returns:
            A `Process` object
        """
        # call either asyncio.create_subprocess_exec or asyncio.create_subprocess_shell
        # depending on whether the command is a list or a string
        if isinstance(command, list):
            process = await asyncio.create_subprocess_exec(
                *command,
                stdin=stdin,
                stdout=stdout,
                stderr=stderr,
                cwd=cwd,
                env=env,
                start_new_session=start_new_session,
                **kwargs,
            )
        else:
            process = await asyncio.create_subprocess_shell(
                command,
                stdin=stdin,
                stdout=stdout,
                stderr=stderr,
                cwd=cwd,
                env=env,
                start_new_session=start_new_session,
                **kwargs,
            )

        return Process(
            process,
            StreamWriterWrapper(process.stdin) if process.stdin else None,
            StreamReaderWrapper(process.stdout) if process.stdout else None,
            StreamReaderWrapper(process.stderr) if process.stderr else None,
        )


@asynccontextmanager
async def open_process(command: list[str], **kwargs):
    """
    Like `anyio.open_process` but with:
    - Support for Windows command joining
    - Termination of the process on exception during yield
    - Forced cleanup of process resources during cancellation
    """
    # Passing a string to open_process is equivalent to shell=True which is
    # generally necessary for Unix-like commands on Windows but otherwise should
    # be avoided
    if not isinstance(command, list):
        raise TypeError(
            "The command passed to open process must be a list. You passed the command"
            f"'{command}', which is type '{type(command)}'."
        )

    if sys.platform == "win32":
        command = " ".join(command)
        process = await _open_anyio_process(command, **kwargs)
    else:
        process = await anyio.open_process(command, **kwargs)

    # if there's a creationflags kwarg and it contains CREATE_NEW_PROCESS_GROUP,
    # use SetConsoleCtrlHandler to handle CTRL-C
    win32_process_group = False
    if (
        sys.platform == "win32"
        and "creationflags" in kwargs
        and kwargs["creationflags"] & subprocess.CREATE_NEW_PROCESS_GROUP
    ):
        win32_process_group = True
        _windows_process_group_pids.add(process.pid)
        # Add a handler for CTRL-C. Re-adding the handler is safe as Windows
        # will not add a duplicate handler if _win32_ctrl_handler is
        # already registered.
        windll.kernel32.SetConsoleCtrlHandler(_win32_ctrl_handler, 1)

    try:
        async with process:
            yield process
    finally:
        try:
            process.terminate()
            if win32_process_group:
                _windows_process_group_pids.remove(process.pid)

        except OSError:
            # Occurs if the process is already terminated
            pass

        # Ensure the process resource is closed. If not shielded from cancellation,
        # this resource can be left open and the subprocess output can appear after
        # the parent process has exited.
        with anyio.CancelScope(shield=True):
            await process.aclose()


async def run_process(
    command: Iterable[str],
    stream_output: bool | tuple[TextSink | None] | TextSink | None = False,
    task_status: anyio.abc.TaskStatus | None = None,
    task_status_handler: Callable[[anyio.abc.Process], Any] | None = None,
    **kwargs,
) -> anyio.abc.Process:
    """
    Like `anyio.run_process` but with:

    - Use of our `open_process` utility to ensure resources are cleaned up
    - Simple `stream_output` support to connect the subprocess to the parent stdout/err
    - Support for submission with `TaskGroup.start` marking as 'started' after the
        process has been created. When used, the PID is returned to the task status.

    """

    if stream_output is True:
        stream_output = (sys.stdout, sys.stderr)

    async with open_process(
        command,
        stdout=subprocess.PIPE if stream_output else subprocess.DEVNULL,
        stderr=subprocess.PIPE if stream_output else subprocess.DEVNULL,
        **kwargs,
    ) as process:
        if task_status is not None:
            if not task_status_handler:

                def task_status_handler(process):
                    return process.pid

            task_status.started(task_status_handler(process))

        if stream_output:
            await consume_process_output(
                process, stdout_sink=stream_output[0], stderr_sink=stream_output[1]
            )

        await process.wait()

    return process


async def consume_process_output(
    process,
    stdout_sink: TextSink | None = None,
    stderr_sink: TextSink | None = None,
):
    async with anyio.create_task_group() as tg:
        tg.start_soon(
            stream_text,
            TextReceiveStream(process.stdout),
            stdout_sink,
        )
        tg.start_soon(
            stream_text,
            TextReceiveStream(process.stderr),
            stderr_sink,
        )


async def stream_text(source: TextReceiveStream, *sinks: TextSink):
    wrapped_sinks = [
        (
            anyio.wrap_file(sink)
            if hasattr(sink, "write") and hasattr(sink, "flush")
            else sink
        )
        for sink in sinks
    ]
    async for item in source:
        for sink in wrapped_sinks:
            if isinstance(sink, TextSendStream):
                await sink.send(item)
            elif isinstance(sink, anyio.AsyncFile):
                await sink.write(item)
                await sink.flush()
            elif sink is None:
                pass  # Consume the item but perform no action
            else:
                raise TypeError(f"Unsupported sink type {type(sink).__name__}")


async def run_command_with_status(
    *args: str,
    cwd: str | anyio.Path | None = None,
    stdout_sink: TextIO | None = None,
    stderr_sink: TextIO | None = None,
) -> int:
    command = " ".join(args)
    with Status(f"Running command: {command}", console=console) as status:
        try:
            process = await run_process(
                list(args),
                stream_output=(stdout_sink, stderr_sink),
                cwd=str(cwd) if cwd else ".",
            )

            if process.returncode != 0:
                err_message = (
                    f"Command failed: {command}"
                    if not stderr_sink
                    else f"Command failed: {command}. Error output: {stderr_sink.seek(0).read()}"
                )
                status.update(err_message)
                raise RuntimeError(f"Command error: {command}")

            status.update(f"Command completed successfully: {command}")
            return process.returncode

        except FileNotFoundError as e:
            status.update(f"Command not found: {args[0]}")
            raise Exception(
                f"{args[0]} is not installed. Please install it and try again."
            ) from e


async def run_gh_command(
    *args: str,
    repo_path: str | anyio.Path | None = None,
    stdout_sink: TextIO | None = None,
    stderr_sink: TextIO | None = None,
) -> str:
    """Run a gh command asynchronously in a given repository path."""
    return await run_command_with_status(
        "gh", *args, cwd=repo_path, stdout_sink=stdout_sink, stderr_sink=stderr_sink
    )


async def run_git_command(
    *args: str,
    cwd: str | anyio.Path | None = None,
    stdout_sink: TextIO | None = None,
    stderr_sink: TextIO | None = None,
) -> str:
    """Run a git command asynchronously in a given repository path."""
    return await run_command_with_status(
        "git", *args, cwd=cwd, stdout_sink=stdout_sink, stderr_sink=stderr_sink
    )
