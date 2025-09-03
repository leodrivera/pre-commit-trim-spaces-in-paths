import pytest

from trim_spaces_in_paths import trim_spaces_in_paths as mod


def test_parse_args_default():
    """Test default argument parsing with no options."""
    f = mod.parse_args
    internal_style, files = f(["script.py"])
    assert internal_style == "none"
    assert files == []


def test_parse_args_with_files():
    """Test argument parsing with file arguments."""
    f = mod.parse_args
    internal_style, files = f(["script.py", "file1.txt", "file2.txt"])
    assert internal_style == "none"
    assert files == ["file1.txt", "file2.txt"]


def test_parse_args_collapse_style():
    """Test argument parsing with collapse internal style."""
    f = mod.parse_args
    internal_style, files = f(["script.py", "--internal-style=collapse", "file.txt"])
    assert internal_style == "collapse"
    assert files == ["file.txt"]


def test_parse_args_underscore_style():
    """Test argument parsing with underscore internal style."""
    f = mod.parse_args
    internal_style, files = f(["script.py", "--internal-style=underscore", "file.txt"])
    assert internal_style == "underscore"
    assert files == ["file.txt"]


def test_parse_args_remove_style():
    """Test argument parsing with remove internal style."""
    f = mod.parse_args
    internal_style, files = f(["script.py", "--internal-style=remove", "file.txt"])
    assert internal_style == "remove"
    assert files == ["file.txt"]


def test_parse_args_multiple_files_with_style():
    """Test argument parsing with multiple files and internal style."""
    f = mod.parse_args
    internal_style, files = f(
        [
            "script.py",
            "--internal-style=collapse",
            "file1.txt",
            "file2.txt",
            "dir/file3.txt",
        ]
    )
    assert internal_style == "collapse"
    assert files == ["file1.txt", "file2.txt", "dir/file3.txt"]


def test_parse_args_style_before_files():
    """Test argument parsing with style option before files."""
    f = mod.parse_args
    internal_style, files = f(
        ["script.py", "--internal-style=underscore", "file1.txt", "file2.txt"]
    )
    assert internal_style == "underscore"
    assert files == ["file1.txt", "file2.txt"]


def test_parse_args_style_after_files():
    """Test argument parsing with style option after files."""
    f = mod.parse_args
    internal_style, files = f(
        ["script.py", "file1.txt", "file2.txt", "--internal-style=remove"]
    )
    assert internal_style == "remove"
    assert files == ["file1.txt", "file2.txt"]


def test_parse_args_invalid_style():
    """Test argument parsing with invalid internal style (should exit with code 2)."""
    from unittest.mock import patch

    f = mod.parse_args
    with patch("sys.exit") as mock_exit, patch("builtins.print") as mock_print:
        # This should trigger sys.exit(2) due to invalid style
        f(["script.py", "--internal-style=invalid", "file.txt"])
        mock_exit.assert_called_once_with(2)
        # Check that error message was printed to stderr
        mock_print.assert_called_once()
        call_args = mock_print.call_args
        assert "Invalid --internal-style option: invalid" in str(call_args)


def test_parse_args_invalid_style_stderr():
    """Test parse_args with invalid internal style using stderr."""
    from unittest.mock import patch

    f = mod.parse_args
    with patch("sys.stderr") as mock_stderr:
        with pytest.raises(SystemExit) as exc_info:
            f(["script", "--internal-style=invalid"])
        assert exc_info.value.code == 2
        # Check that error message was printed
        mock_stderr.write.assert_called()
