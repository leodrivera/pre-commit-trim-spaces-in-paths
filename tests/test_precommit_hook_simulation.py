"""Test pre-commit hook simulation."""

import platform

import pytest


class TestPreCommitHookSimulation:
    """Test pre-commit hook simulation from remote repository."""

    def test_precommit_hook_simulation_no_files(
        self, git_repo, project_root, run_command
    ):
        """Test pre-commit hook simulation with no files to check."""
        # Create a simple .pre-commit-config.yaml that uses our repo
        config_content = f"""repos:
  - repo: {project_root}
    rev: HEAD
    hooks:
      - id: trim-spaces-in-paths
        args: [--internal-style=none]
"""
        config_file = git_repo / ".pre-commit-config.yaml"
        config_file.write_text(config_content)

        # Run pre-commit
        result = run_command(
            ["pre-commit", "run", "--all-files"], cwd=git_repo, check=False
        )

        # Should pass with no files to check
        assert result.returncode == 0
        assert "Trim spaces in file and directory names" in result.stdout
        assert "(no files to check)Skipped" in result.stdout

    @pytest.mark.skipif(
        platform.system() == "Windows",
        reason="Cross-mount path issues on Windows CI",
    )
    def test_precommit_hook_simulation_with_files(
        self, git_repo, project_root, run_command
    ):
        """Test pre-commit hook simulation with files that need changes."""
        # Create a file with spaces in the name
        test_file = git_repo / "  test  file  .txt"
        test_file.write_text("content")

        # Add the file to git
        run_command(["git", "add", str(test_file)], cwd=git_repo)

        # Use pre-commit try-repo to test the hook
        result = run_command(
            [
                "pre-commit",
                "try-repo",
                str(project_root),
                "trim-spaces-in-paths",
                "--files",
                str(test_file),
            ],
            cwd=git_repo,
            check=False,
        )

        # Should pass and rename the file (exit code 3 means success with changes)
        # On Windows, pre-commit might return different exit codes
        assert result.returncode in (
            1,
            3,
        )  # Both are valid (1 = pre-commit failure, 3 = hook success with changes)
        assert "Trim spaces in file and directory names" in result.stdout
        assert "Renamed" in result.stdout

        # Check that the file was renamed (the hook trims leading/trailing spaces)
        renamed_file = (
            git_repo / "test  file  .txt"
        )  # Only leading/trailing spaces are trimmed
        assert renamed_file.exists()
        assert not test_file.exists()

    @pytest.mark.skipif(
        platform.system() == "Windows",
        reason="Cross-mount path issues on Windows CI",
    )
    def test_precommit_hook_simulation_multiple_files(
        self, git_repo, project_root, run_command
    ):
        """Test pre-commit hook simulation with multiple files."""
        # Create multiple files with spaces
        file1 = git_repo / "  file1  .txt"
        file2 = git_repo / "  file2  .txt"
        file1.write_text("content1")
        file2.write_text("content2")

        # Add the files to git
        run_command(["git", "add", str(file1), str(file2)], cwd=git_repo)

        # Use pre-commit try-repo to test the hook
        result = run_command(
            [
                "pre-commit",
                "try-repo",
                str(project_root),
                "trim-spaces-in-paths",
                "--files",
                str(file1),
                str(file2),
            ],
            cwd=git_repo,
            check=False,
        )

        # Should pass and rename the files (exit code 3 means success with changes)
        # On Windows, pre-commit might return different exit codes
        assert result.returncode in (
            1,
            3,
        )  # Both are valid (1 = pre-commit failure, 3 = hook success with changes)
        assert "Trim spaces in file and directory names" in result.stdout
        assert "Renamed" in result.stdout

        # Check that both files were renamed
        renamed_file1 = git_repo / "file1  .txt"
        renamed_file2 = git_repo / "file2  .txt"
        assert renamed_file1.exists()
        assert renamed_file2.exists()
        assert not file1.exists()
        assert not file2.exists()
