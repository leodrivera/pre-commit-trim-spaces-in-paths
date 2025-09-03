from trim_spaces_in_paths import trim_spaces_in_paths as mod


def test_normalize_component_none():
    f = mod.normalize_component
    assert f("  My  Report .txt  ", "none") == "My  Report .txt"


def test_normalize_component_collapse():
    f = mod.normalize_component
    assert f("  My   Report   .txt  ", "collapse") == "My Report .txt"


def test_normalize_component_underscore():
    f = mod.normalize_component
    assert f("  My  Report .txt  ", "underscore") == "My__Report_.txt"


def test_normalize_component_remove():
    f = mod.normalize_component
    assert f("  My  Report .txt  ", "remove") == "MyReport.txt"


def test_normalize_path_trims_edges():
    f = mod.normalize_path
    out, err = f("  dir  /  subdir  /  file .txt  ", "none")
    assert err is None
    assert out == "dir/subdir/file .txt"


def test_normalize_path_empty_component_error():
    f = mod.normalize_path
    out, err = f("dir/   /file.txt", "none")  # middle component is only spaces
    assert out is None
    assert "become empty" in err


class TestNormalizeComponentEdgeCases:
    """Test normalize_component edge cases."""

    def test_normalize_component_unknown_style(self):
        """Test normalize_component with unknown internal_style."""
        # This should trigger the fallback return
        result = mod.normalize_component("  test  ", "unknown_style")
        assert result == "test"  # Should return trimmed (spaces are always trimmed)

    def test_normalize_component_collapse_logic(self):
        """Test normalize_component collapse logic."""
        # Test collapse with multiple spaces
        result = mod.normalize_component("  a   b  c  ", "collapse")
        assert result == "a b c"  # Leading/trailing spaces are trimmed first

        # Test collapse with single spaces (should remain unchanged)
        result = mod.normalize_component(" a b c ", "collapse")
        assert result == "a b c"  # Leading/trailing spaces are trimmed first

    def test_normalize_component_underscore_edge_case(self):
        """Test normalize_component underscore style edge case."""
        result = mod.normalize_component("  a b c  ", "underscore")
        assert result == "a_b_c"

    def test_normalize_component_remove_edge_case(self):
        """Test normalize_component remove style edge case."""
        result = mod.normalize_component("  a b c  ", "remove")
        assert result == "abc"
