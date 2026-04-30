"""Smoke tests for the pywfm CLI.

These run the CLI commands with --help to confirm they're reachable and
their option metadata parses cleanly. Doesn't exercise actual download
or DLL-version-fetch behavior — those would need network access and a
loaded DLL respectively.
"""
import pytest
from click.testing import CliRunner

from pywfm.cli import cli


@pytest.fixture
def runner():
    return CliRunner()


@pytest.mark.unit
def test_cli_help(runner):
    """`pywfm --help` lists the registered subcommands."""
    result = runner.invoke(cli, ["--help"])
    assert result.exit_code == 0
    assert "setup-pywfm" in result.output
    assert "get-api-version" in result.output


@pytest.mark.unit
def test_setup_pywfm_help(runner):
    """`pywfm setup-pywfm --help` shows --path and --version options."""
    result = runner.invoke(cli, ["setup-pywfm", "--help"])
    assert result.exit_code == 0
    assert "--path" in result.output
    assert "--version" in result.output


@pytest.mark.unit
def test_setup_pywfm_rejects_missing_path(runner, tmp_path):
    """Pointing --path at a directory without the DLL raises FileNotFoundError."""
    empty = tmp_path / "no_dll_here"
    empty.mkdir()
    result = runner.invoke(cli, ["setup-pywfm", "--path", str(empty)])
    # Click captures the exception in result.exception when not handled.
    assert result.exit_code != 0
    assert isinstance(result.exception, FileNotFoundError)


@pytest.mark.unit
def test_get_api_version_help(runner):
    """`pywfm get-api-version --help` is reachable."""
    result = runner.invoke(cli, ["get-api-version", "--help"])
    assert result.exit_code == 0
