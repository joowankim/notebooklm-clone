"""CLI error handling utilities."""

import functools
from collections.abc import Callable, Coroutine
from typing import Any, TypeVar

import rich.console
import typer

from src import exceptions as exceptions_module

console = rich.console.Console()

T = TypeVar("T")


def handle_domain_errors(
    func: Callable[..., Coroutine[Any, Any, T]],
) -> Callable[..., Coroutine[Any, Any, T]]:
    """Decorator that converts domain exceptions to CLI error output."""

    @functools.wraps(func)
    async def wrapper(*args: Any, **kwargs: Any) -> T:
        try:
            return await func(*args, **kwargs)
        except exceptions_module.NotFoundError as exc:
            console.print(f"[red]Not found:[/red] {exc.message}")
            raise typer.Exit(1) from exc
        except exceptions_module.ValidationError as exc:
            console.print(f"[red]Validation error:[/red] {exc.message}")
            raise typer.Exit(1) from exc
        except exceptions_module.InvalidStateError as exc:
            console.print(f"[red]Invalid state:[/red] {exc.message}")
            raise typer.Exit(1) from exc
        except exceptions_module.ExternalServiceError as exc:
            console.print(f"[red]External service error:[/red] {exc.message}")
            raise typer.Exit(1) from exc

    return wrapper
