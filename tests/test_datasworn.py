from pysworn.datasworn.cli import app
from typer.testing import CliRunner

runner = CliRunner()


def test_cli_shows_help():
    result = runner.invoke(app)
    # print(result.output)
    assert "Usage: " in result.output


def test_ids():
    res = runner.invoke(app, ["ids"])
    assert res.exit_code == 0
    assert len(res.output.splitlines()) == 27334


def test_types():
    res = runner.invoke(app, ["types"])
    assert res.exit_code == 0
    assert len(res.output.splitlines()) == 36


def test_rules():
    res = runner.invoke(app, ["rules"])
    assert res.exit_code == 0
    assert len(res.output.splitlines()) == 774
