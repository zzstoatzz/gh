import tempfile
from contextlib import asynccontextmanager
from pathlib import Path
from typing import AsyncGenerator

from gh_util.utils import run_git_command


@asynccontextmanager
async def clone_repo(
    owner: str, repo: str, path: Path | None = None
) -> AsyncGenerator[Path, None]:
    """Clone a repository to a specified path or a temporary directory.

    Args:
        owner: The owner of the repository.
        repo: The repository name.
        path: The path to clone the repository to. If not provided, a temporary directory will be used.

    Yields:
        Path: The path to the cloned repository.
    """
    repo_url = f"git@github.com:{owner}/{repo}.git"

    if path is None:
        with tempfile.TemporaryDirectory() as tmpdir:
            path = Path(tmpdir)
            await run_git_command("clone", repo_url, str(path))
            yield path
    else:
        await run_git_command("clone", repo_url, str(path))
        yield path
