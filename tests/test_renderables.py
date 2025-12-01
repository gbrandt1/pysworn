from pysworn.renderables.__main__ import app
from typer.testing import CliRunner

runner = CliRunner()


def test_renderables():
    result = runner.invoke(app)
    assert len(result.output.splitlines()) == 89766
