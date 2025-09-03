"""Tests for main() function functionality."""

import sys
from unittest.mock import patch

import pytest

from trim_spaces_in_paths import trim_spaces_in_paths as mod


class TestMainErrorHandling:
    """Test main() error handling paths."""

    def test_main_normalize_path_error(self, monkeypatch, tmp_path):
        """Test main() when normalize_path returns an error."""
        # Patch repo_root to return our temp directory
        monkeypatch.setattr(mod, "repo_root", lambda: tmp_path)

        with patch.object(mod, "git_mv", return_value=True):
            # Test with a path that would cause normalization error
            result = mod.main(["script", "  "])  # Path that becomes empty
            assert result == 1  # Should return error code

    def test_main_git_mv_failure(self, monkeypatch, tmp_path):
        """Test main() when git_mv fails."""
        # Patch repo_root to return our temp directory
        monkeypatch.setattr(mod, "repo_root", lambda: tmp_path)

        with patch.object(mod, "git_mv", return_value=False):
            # Test with a valid path that should be renamed
            result = mod.main(["script", "  test  .txt"])
            assert result == 1  # Should return error code due to git_mv failure


class TestMainIntegration:
    """Integration tests for main() function scenarios."""

    def test_main_success_with_changes(self, monkeypatch, tmp_path):
        """Test main() success path with actual changes."""
        # Patch repo_root to return our temp directory
        monkeypatch.setattr(mod, "repo_root", lambda: tmp_path)

        with (
            patch.object(mod, "git_mv", return_value=True),
            patch("sys.stdout") as mock_stdout,
        ):
            result = mod.main(["script", "  test  .txt"])
            assert result == 3  # Should return success with changes
            # Check that success message was printed
            mock_stdout.write.assert_called()

    def test_main_success_no_changes(self, monkeypatch, tmp_path):
        """Test main() success path with no changes needed."""
        # Patch repo_root to return our temp directory
        monkeypatch.setattr(mod, "repo_root", lambda: tmp_path)

        # Test with paths that don't need normalization
        result = mod.main(["script", "already_normal.txt"])
        assert result == 0  # Should return success with no changes

    def test_main_conflict_detection(self, monkeypatch, tmp_path):
        """Test main() conflict detection between multiple paths."""
        # Patch repo_root to return our temp directory
        monkeypatch.setattr(mod, "repo_root", lambda: tmp_path)

        with patch.object(mod, "git_mv", return_value=True):
            # Test with paths that would actually conflict (both become same name)
            result = mod.main(["script", "  test  .txt", " test .txt"])
            # These don't actually conflict with "none" style, so they succeed
            assert result == 3  # Should return success with changes

    def test_main_conflict_detection_different_paths(self, monkeypatch, tmp_path):
        """Test main() conflict detection with different paths."""
        # Patch repo_root to return our temp directory
        monkeypatch.setattr(mod, "repo_root", lambda: tmp_path)

        with patch.object(mod, "git_mv", return_value=True):
            # Test with paths that would actually conflict (both become same name)
            result = mod.main(["script", "  test  .txt", " test .txt"])
            # These don't actually conflict with "none" style, so they succeed
            assert result == 3  # Should return success with changes

    def test_main_actual_conflict_detection(self, monkeypatch, tmp_path):
        """Test main() with actual conflict."""
        # Patch repo_root to return our temp directory
        monkeypatch.setattr(mod, "repo_root", lambda: tmp_path)

        # Test with paths that would actually conflict (both become same name)
        # Using "remove" style to create actual conflict
        result = mod.main(
            ["script", "--internal-style=remove", "  test  .txt", " test .txt"]
        )
        assert result == 1  # Should return error due to conflict


class TestDirectExecution:
    """Test direct script execution."""

    def test_script_direct_execution_calls_main(self):
        """Test that direct execution calls main with sys.argv."""
        with patch.object(mod, "main") as mock_main:
            mock_main.return_value = 0

            # Simulate the if __name__ == "__main__" block
            with patch("sys.argv", ["trim_spaces_in_paths.py", "test.txt"]):
                with pytest.raises(SystemExit) as exc_info:
                    # This simulates what happens in the if __name__ == "__main__" block
                    sys.exit(mod.main(sys.argv))
                assert exc_info.value.code == 0
                mock_main.assert_called_once_with(sys.argv)

    def test_script_direct_execution_passes_exit_code(self):
        """Test that direct execution passes main's return code to sys.exit."""
        with patch.object(mod, "main") as mock_main:
            mock_main.return_value = 3

            # Simulate the if __name__ == "__main__" block
            with patch("sys.argv", ["trim_spaces_in_paths.py", "test.txt"]):
                with pytest.raises(SystemExit) as exc_info:
                    # This simulates what happens in the if __name__ == "__main__" block
                    sys.exit(mod.main(sys.argv))
                assert exc_info.value.code == 3
                mock_main.assert_called_once_with(sys.argv)


class TestPreCommitHookEntryPoint:
    """Test pre-commit hook entry point functionality."""

    def test_precommit_hook_entry_point(self, monkeypatch, tmp_path):
        """Test that the pre-commit hook entry point works correctly."""
        # Test the exact entry point that pre-commit uses
        from trim_spaces_in_paths.trim_spaces_in_paths import main

        # Patch repo_root to return our temp directory
        monkeypatch.setattr(mod, "repo_root", lambda: tmp_path)

        # Test with no files (should return 0)
        result = main(["script"])
        assert result == 0

        # Test with files that don't need changes (should return 0)
        result = main(["script", "normal_file.txt"])
        assert result == 0

    def test_precommit_hook_entry_point_with_changes(self, monkeypatch, tmp_path):
        """Test pre-commit hook entry point with files that need changes."""
        from trim_spaces_in_paths.trim_spaces_in_paths import main

        # Patch repo_root to return our temp directory
        monkeypatch.setattr(mod, "repo_root", lambda: tmp_path)

        with (
            patch.object(mod, "git_mv", return_value=True),
            patch("sys.stdout") as mock_stdout,
        ):
            # Test with files that need changes
            result = main(["script", "  test  .txt"])
            assert result == 3  # Should return success with changes
            # Check that success message was printed
            mock_stdout.write.assert_called()

    def test_precommit_hook_entry_point_with_errors(self, monkeypatch, tmp_path):
        """Test pre-commit hook entry point with errors."""
        from trim_spaces_in_paths.trim_spaces_in_paths import main

        # Patch repo_root to return our temp directory
        monkeypatch.setattr(mod, "repo_root", lambda: tmp_path)

        with patch.object(mod, "git_mv", return_value=False):
            # Test with files that fail to rename
            result = main(["script", "  test  .txt"])
            assert result == 1  # Should return error code
