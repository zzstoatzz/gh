import inspect
from typing import Any, Callable


def get_functions_from_module(module: Any) -> list[Callable]:
    return [
        fn
        for fn_name in dir(module)
        if inspect.isfunction(fn := getattr(module, fn_name))
        and fn.__module__ == module.__name__
    ]
