"""Tests for CLI error handling decorator."""

import click.exceptions
import pytest
import typer

from src import exceptions as exceptions_module
from src.cli.error_handling import handle_domain_errors


class TestHandleDomainErrors:
    """Tests for handle_domain_errors decorator."""

    @pytest.mark.asyncio
    async def test_not_found_error_exits_with_code_1(self) -> None:
        """NotFoundError should print message and exit with code 1."""

        @handle_domain_errors
        async def failing_func() -> None:
            raise exceptions_module.NotFoundError("Notebook not found: abc123")

        with pytest.raises(click.exceptions.Exit) as exc_info:
            await failing_func()

        assert exc_info.value.exit_code == 1

    @pytest.mark.asyncio
    async def test_validation_error_exits_with_code_1(self) -> None:
        """ValidationError should exit with code 1."""

        @handle_domain_errors
        async def failing_func() -> None:
            raise exceptions_module.ValidationError("URL already exists")

        with pytest.raises(click.exceptions.Exit) as exc_info:
            await failing_func()

        assert exc_info.value.exit_code == 1

    @pytest.mark.asyncio
    async def test_invalid_state_error_exits_with_code_1(self) -> None:
        """InvalidStateError should exit with code 1."""

        @handle_domain_errors
        async def failing_func() -> None:
            raise exceptions_module.InvalidStateError("Cannot cancel completed job")

        with pytest.raises(click.exceptions.Exit) as exc_info:
            await failing_func()

        assert exc_info.value.exit_code == 1

    @pytest.mark.asyncio
    async def test_external_service_error_exits_with_code_1(self) -> None:
        """ExternalServiceError should exit with code 1."""

        @handle_domain_errors
        async def failing_func() -> None:
            raise exceptions_module.ExternalServiceError("OpenAI API timeout")

        with pytest.raises(click.exceptions.Exit) as exc_info:
            await failing_func()

        assert exc_info.value.exit_code == 1

    @pytest.mark.asyncio
    async def test_successful_call_returns_result(self) -> None:
        """Successful call should return normally."""

        @handle_domain_errors
        async def success_func() -> str:
            return "ok"

        result = await success_func()
        assert result == "ok"

    @pytest.mark.asyncio
    async def test_non_domain_errors_propagate(self) -> None:
        """Non-domain errors should not be caught."""

        @handle_domain_errors
        async def failing_func() -> None:
            raise ValueError("unexpected")

        with pytest.raises(ValueError, match="unexpected"):
            await failing_func()

    @pytest.mark.asyncio
    async def test_typer_exit_propagates(self) -> None:
        """typer.Exit should propagate through the decorator."""

        @handle_domain_errors
        async def exiting_func() -> None:
            raise typer.Exit(0)

        with pytest.raises(click.exceptions.Exit):
            await exiting_func()
