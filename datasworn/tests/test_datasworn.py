import pytest
from typer.testing import CliRunner


# @pytest.mark.skip
def discover_typer_app():
    from pysworn.datasworn.main import app

    return app


# @pytest.mark.skip
def test_cli_shows_help():
    app = discover_typer_app()
    runner = CliRunner()
    result = runner.invoke(app, ["--help"])
    assert result.exit_code == 0
    assert "Usage" in result.output or "Usage:" in result.output


# @pytest.mark.skip
def test_all_commands_have_help():
    app = discover_typer_app()
    runner = CliRunner()

    # app.commands is a dict on Click groups / Typer apps; fall back to empty dict
    commands = getattr(app, "commands", {}) or {}
    # If there are no subcommands, at least invoking --help for the app above suffices.
    # if not commands:
    #     pytest.skip("No subcommands registered on the CLI to test")

    for name in sorted(commands):
        print(name)
        res = runner.invoke(app, [name, "--help"])
        assert res.exit_code == 0, (
            f"Subcommand {name} failed to show help: {res.output}"
        )
        assert "Usage" in res.output or "Usage:" in res.output


# @pytest.mark.skip
def test_unknown_command_returns_error():
    app = discover_typer_app()
    runner = CliRunner()
    res = runner.invoke(app, ["this-command-does-not-exist"])
    assert res.exit_code != 0
    # Click/Typer typically prints "Error" for unknown commands
    assert "Error" in res.output or "No such command" in res.output


def test_dump():
    print("TESTING DUMP")
    app = discover_typer_app()
    runner = CliRunner()
    res = runner.invoke(app, ["dump"])
    assert res.exit_code == 0
    print(res)


@pytest.mark.skip
def test_ids():
    app = discover_typer_app()
    runner = CliRunner()
    res = runner.invoke(app, ["ids"])
    assert res.exit_code == 0
    print(res.output)
