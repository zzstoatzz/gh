import inspect
from typing import Any, Callable, Literal, TypeVar, get_origin

from pydantic import TypeAdapter

T = TypeVar("T")


def parse_as(
    type_: type[T],
    data: Any,
    mode: Literal["python", "json", "strings"] = "python",
) -> T:
    """Parse a given data structure as a Pydantic model via `TypeAdapter`.

    Read more about `TypeAdapter` [here](https://docs.pydantic.dev/latest/concepts/type_adapter/).

    Args:
        type_: The type to parse the data as.
        data: The data to be parsed.
        mode: The mode to use for parsing, either `python`, `json`, or `strings`.
            Defaults to `python`, where `data` should be a Python object (e.g. `dict`).

    Returns:
        The parsed `data` as the given `type_`.

    Example:
        ```python
        from gh.types import GitHubIssue
        from gh.utils import parse_as

        issue = parse_as(GitHubIssue, {"title": "Test Issue"})
        print(issue.title)
        # => "Test Issue"
        ```
    """
    adapter = TypeAdapter(type_)

    parser: Callable[[Any], T] = getattr(adapter, f"validate_{mode}")

    if get_origin(type_) is list and isinstance(data, dict):
        data = next(iter(data.values()))

    return parser(data)


def get_functions_from_module(module: Any) -> list[Callable]:
    return [
        fn
        for fn_name in dir(module)
        if inspect.isfunction(fn := getattr(module, fn_name))
        and fn.__module__ == module.__name__
    ]
