"""Pytest configuration and shared fixtures."""

import subprocess
from pathlib import Path

import pytest


@pytest.fixture(scope="session")
def package_path():
    """Get the path to the package directory."""
    import trim_spaces_in_paths

    return Path(trim_spaces_in_paths.__file__).parent


@pytest.fixture(scope="session")
def script_path():
    """Get the path to the main script."""
    import trim_spaces_in_paths.trim_spaces_in_paths

    return Path(trim_spaces_in_paths.trim_spaces_in_paths.__file__)


@pytest.fixture(scope="session")
def project_root(package_path):
    """Get the project root directory."""
    return package_path.parent


def _run_command(cmd, cwd=None, check=True):
    """Run a command and return the result."""
    result = subprocess.run(cmd, capture_output=True, text=True, check=check, cwd=cwd)
    return result


@pytest.fixture
def run_command():
    """Provide the run_command function as a fixture."""
    return _run_command


@pytest.fixture
def git_repo(tmp_path, run_command):
    """Create a temporary git repository with basic configuration."""
    # Initialize git repo
    run_command(["git", "init"], cwd=tmp_path)
    run_command(["git", "config", "user.name", "Test"], cwd=tmp_path)
    run_command(["git", "config", "user.email", "test@example.com"], cwd=tmp_path)

    return tmp_path
