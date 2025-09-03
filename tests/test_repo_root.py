"""Tests for repo_root() functionality."""

from unittest.mock import Mock, patch

import pytest

from trim_spaces_in_paths import trim_spaces_in_paths as mod


class TestRepoRootError:
    """Test repo_root() error handling."""

    def test_repo_root_not_git_repo(self):
        """Test repo_root() when not in a git repository."""
        with patch.object(mod, "run") as mock_run:
            # Mock git command failure
            mock_run.return_value = Mock(
                returncode=1,
                stderr=b"fatal: not a git repository (or any of the parent directories): .git\n",
            )

            with pytest.raises(SystemExit) as exc_info:
                mod.repo_root()

            assert exc_info.value.code == 2

    def test_repo_root_git_error_no_stderr(self):
        """Test repo_root() when git command fails with no stderr."""
        with patch.object(mod, "run") as mock_run:
            # Mock git command failure with no stderr
            mock_run.return_value = Mock(returncode=1, stderr=b"")

            with pytest.raises(SystemExit) as exc_info:
                mod.repo_root()

            assert exc_info.value.code == 2
