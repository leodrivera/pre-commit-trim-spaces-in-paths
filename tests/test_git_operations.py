import os
import sys

import pytest

from trim_spaces_in_paths import trim_spaces_in_paths as mod


def test_is_tracked_file_exists(git_repo, run_command):
    """Test is_tracked() with a file that exists and is tracked by git."""
    # Create and add a file
    test_file = git_repo / "test.txt"
    test_file.write_text("content")
    run_command(["git", "add", "test.txt"], cwd=git_repo)

    # Test is_tracked - need to change to the git repo directory first
    original_cwd = os.getcwd()
    try:
        os.chdir(git_repo)
        f = mod.is_tracked
        assert f("test.txt") is True
    finally:
        os.chdir(original_cwd)


def test_is_tracked_file_not_tracked(git_repo):
    """Test is_tracked() with a file that exists but is not tracked by git."""
    # Create a file but don't add it
    test_file = git_repo / "test.txt"
    test_file.write_text("content")

    # Test is_tracked - need to change to the git repo directory first
    original_cwd = os.getcwd()
    try:
        os.chdir(git_repo)
        f = mod.is_tracked
        assert f("test.txt") is False
    finally:
        os.chdir(original_cwd)


def test_is_tracked_file_not_exists(git_repo):
    """Test is_tracked() with a file that doesn't exist."""
    # Test is_tracked with non-existent file - need to change to the git repo directory first
    original_cwd = os.getcwd()
    try:
        os.chdir(git_repo)
        f = mod.is_tracked
        assert f("nonexistent.txt") is False
    finally:
        os.chdir(original_cwd)


def test_ensure_parent_creates_directories(tmp_path):
    """Test ensure_parent() creates parent directories."""
    # Test ensure_parent with nested path
    f = mod.ensure_parent
    nested_path = tmp_path / "dir1" / "dir2" / "file.txt"
    f(str(nested_path))

    # Check that parent directories were created
    assert (tmp_path / "dir1").exists()
    assert (tmp_path / "dir1" / "dir2").exists()


def test_ensure_parent_existing_directories(tmp_path):
    """Test ensure_parent() with existing parent directories."""
    # Create parent directories manually
    (tmp_path / "existing_dir").mkdir()

    # Test ensure_parent with existing parent
    f = mod.ensure_parent
    file_path = tmp_path / "existing_dir" / "file.txt"
    f(str(file_path))

    # Should not raise an error
    assert (tmp_path / "existing_dir").exists()


@pytest.mark.skipif(
    sys.platform == "Windows",
    reason="Filesystem spacing edge-cases not portable on Windows",
)
def test_git_mv_same_source_destination(git_repo):
    """Test git_mv() with same source and destination (should return False)."""
    # Create a file
    test_file = git_repo / "test.txt"
    test_file.write_text("content")

    # Test git_mv with same source and destination - need to change to the git repo directory first
    original_cwd = os.getcwd()
    try:
        os.chdir(git_repo)
        f = mod.git_mv
        result = f("test.txt", "test.txt")
        assert result is False
    finally:
        os.chdir(original_cwd)


@pytest.mark.skipif(
    sys.platform == "Windows",
    reason="Filesystem spacing edge-cases not portable on Windows",
)
def test_git_mv_successful_rename(git_repo, run_command):
    """Test git_mv() with successful file rename."""
    # Create and add a file
    test_file = git_repo / "test.txt"
    test_file.write_text("content")
    run_command(["git", "add", "test.txt"], cwd=git_repo)

    # Test git_mv with successful rename - need to change to the git repo directory first
    original_cwd = os.getcwd()
    try:
        os.chdir(git_repo)
        f = mod.git_mv
        result = f("test.txt", "renamed.txt")
        assert result is True

        # Check that file was renamed
        assert not (git_repo / "test.txt").exists()
        assert (git_repo / "renamed.txt").exists()
        assert (git_repo / "renamed.txt").read_text() == "content"
    finally:
        os.chdir(original_cwd)


@pytest.mark.skipif(
    sys.platform == "Windows",
    reason="Filesystem spacing edge-cases not portable on Windows",
)
def test_git_mv_nonexistent_source(git_repo):
    """Test git_mv() with non-existent source file."""
    # Test git_mv with non-existent source - need to change to the git repo directory first
    original_cwd = os.getcwd()
    try:
        os.chdir(git_repo)
        f = mod.git_mv
        result = f("nonexistent.txt", "renamed.txt")
        # git mv with -k flag returns True (success) even when skipping non-existent files
        assert result is True
        # Verify that no destination file was created
        assert not (git_repo / "renamed.txt").exists()
    finally:
        os.chdir(original_cwd)


class TestGitMvErrorHandling:
    """Test git_mv error handling and file operations."""

    def test_git_mv_file_not_found(self):
        """Test git_mv when source file doesn't exist (FileNotFoundError)."""
        from unittest.mock import Mock, patch

        with patch.object(mod, "run") as mock_run:
            # Mock git mv failure
            mock_run.return_value = Mock(returncode=1)

            with patch("os.replace", side_effect=FileNotFoundError):
                result = mod.git_mv("nonexistent.txt", "new.txt")
                assert result is False

    def test_git_mv_os_replace_exception(self):
        """Test git_mv when os.replace raises an exception."""
        from unittest.mock import Mock, patch

        with patch.object(mod, "run") as mock_run:
            # Mock git mv failure
            mock_run.return_value = Mock(returncode=1)

            with (
                patch("os.replace", side_effect=OSError("Permission denied")),
                patch("sys.stderr") as mock_stderr,
            ):
                result = mod.git_mv("source.txt", "dest.txt")
                assert result is False
                # Check that error message was printed
                mock_stderr.write.assert_called()

    def test_git_mv_successful_os_replace(self):
        """Test git_mv when git mv fails but os.replace succeeds."""
        from unittest.mock import Mock, patch

        with patch.object(mod, "run") as mock_run:
            # Mock git mv failure
            mock_run.return_value = Mock(returncode=1)

            with (
                patch("os.replace") as mock_replace,
                patch.object(mod, "is_tracked", return_value=True),
            ):
                result = mod.git_mv("source.txt", "dest.txt")
                assert result is True
                mock_replace.assert_called_once_with("source.txt", "dest.txt")
                # Should call git add and git rm
                assert mock_run.call_count >= 3

    def test_git_mv_successful_os_replace_untracked_source(self):
        """Test git_mv when git mv fails, os.replace succeeds, and source is untracked."""
        from unittest.mock import Mock, patch

        with patch.object(mod, "run") as mock_run:
            # Mock git mv failure
            mock_run.return_value = Mock(returncode=1)

            with (
                patch("os.replace") as mock_replace,
                patch.object(mod, "is_tracked", return_value=False),
            ):
                result = mod.git_mv("source.txt", "dest.txt")
                assert result is True
                mock_replace.assert_called_once_with("source.txt", "dest.txt")
                # Should call git add but not git rm (since source is untracked)
                assert mock_run.call_count >= 2

    def test_git_mv_same_source_destination_mocked(self):
        """Test git_mv when source equals destination (mocked version)."""
        result = mod.git_mv("same.txt", "same.txt")
        assert result is False
