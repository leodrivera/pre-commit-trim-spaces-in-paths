import platform
import shutil
import sys

import pytest


def test_script_is_executable(script_path):
    """Test that the script is executable and has correct shebang."""
    # Check that the script file exists
    assert script_path.exists(), f"Script not found at {script_path}"

    # Check that the script has executable permissions (Unix only)
    if platform.system() != "Windows":
        assert script_path.stat().st_mode & 0o111, "Script is not executable"

    # Check that the script has the correct shebang
    with open(script_path, encoding="utf-8") as f:
        first_line = f.readline().strip()
        assert first_line == "#!/usr/bin/env python3", (
            f"Expected shebang, got: {first_line}"
        )


def test_script_can_be_executed_directly(script_path, project_root, run_command):
    """Test that the script can be executed directly without python prefix."""
    # This test only works on Unix-like systems
    if platform.system() == "Windows":
        pytest.skip("Direct execution test not applicable on Windows")

    # Try to execute the script directly
    result = run_command([str(script_path), "--help"], cwd=project_root)
    # The script doesn't have --help, so it should exit with code 0 (no args)
    assert result.returncode == 0, f"Script execution failed: {result.stderr}"


def test_precommit_environment_simulation(script_path, git_repo, run_command):
    """Test that simulates the pre-commit environment to catch executable issues."""
    # This test simulates how pre-commit calls the script
    if platform.system() == "Windows":
        pytest.skip("Pre-commit simulation test not applicable on Windows")

    # Copy the script to the temp directory (simulating pre-commit's behavior)
    temp_script = git_repo / "temp_trim_spaces_script.py"
    shutil.copy2(script_path, temp_script)

    # Make sure it's executable
    temp_script.chmod(0o755)

    # Test that the script can be found and executed from the temp directory
    result = run_command([str(temp_script)], cwd=git_repo)
    # Should exit with code 0 (no arguments provided)
    assert result.returncode == 0, f"Script not executable in temp dir: {result.stderr}"

    # Test with a simple argument
    result = run_command([str(temp_script), "--internal-style=none"], cwd=git_repo)
    # Should exit with code 0 (no files to process)
    assert result.returncode == 0, f"Script failed with arguments: {result.stderr}"


@pytest.mark.skipif(
    platform.system() == "Windows",
    reason="Filesystem spacing edge-cases not portable on Windows",
)
def test_rename_with_internal_collapse_and_leading_space(
    git_repo, script_path, run_command
):
    # Create a path with leading space in directory and multiple internal spaces in filename
    # e.g., " dir/ my  file .txt" -> "dir/my file .txt"
    (git_repo / " dir").mkdir(parents=True, exist_ok=True)
    (git_repo / " dir" / " my  file .txt").write_text("hello", encoding="utf-8")

    # Stage it with the original (weird) paths
    run_command(["git", "add", "--", " dir/ my  file .txt"], cwd=git_repo)

    # Call the hook script with collapse mode and the staged filename
    cmd = [
        sys.executable,
        str(script_path),
        "--internal-style=collapse",
        " dir/ my  file .txt",
    ]
    p = run_command(cmd, cwd=git_repo, check=False)

    # The script should return 3 (changed) or 0 (if it was a no-op); but here it should change
    assert p.returncode in (0, 3, 1)
    out = p.stdout
    assert "internal-style=collapse" in out

    # After rename, check file exists at normalized path
    assert (git_repo / "dir" / "my file .txt").exists()

    # Ensure git sees the normalized file staged
    status = run_command(["git", "status", "--porcelain"], cwd=git_repo).stdout
    assert "dir/my file .txt" in status


@pytest.mark.skipif(
    platform.system() == "Windows",
    reason="Filesystem spacing edge-cases not portable on Windows",
)
def test_conflict_detection_many_to_one(git_repo, script_path, run_command):
    # Two files that would collapse to the same target with collapse mode:
    # "dir/A  file.txt" and "dir/A   file.txt" -> both become "dir/A file.txt"
    (git_repo / "dir").mkdir(parents=True, exist_ok=True)
    (git_repo / "dir" / "A  file.txt").write_text("1", encoding="utf-8")
    (git_repo / "dir" / "A   file.txt").write_text("2", encoding="utf-8")

    run_command(
        ["git", "add", "--", "dir/A  file.txt", "dir/A   file.txt"], cwd=git_repo
    )

    cmd = [
        sys.executable,
        str(script_path),
        "--internal-style=collapse",
        "dir/A  file.txt",
        "dir/A   file.txt",
    ]
    p = run_command(cmd, cwd=git_repo, check=False)
    # Expect a failure (conflict)
    assert p.returncode == 1
    assert "Conflict:" in p.stderr
