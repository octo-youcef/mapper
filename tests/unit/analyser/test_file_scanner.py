"""Tests for file scanner."""

import pytest

from mapper.analyser import file_scanner


class TestFileScanner:
    """Tests for FileScanner class."""

    def test_scan_nonexistent_directory(self, tmp_path):
        """Test scanning a directory that doesn't exist raises FileNotFoundError."""
        nonexistent = tmp_path / "does_not_exist"
        scanner = file_scanner.FileScanner(nonexistent)

        with pytest.raises(FileNotFoundError, match="Directory not found"):
            scanner.scan()

    def test_scan_empty_directory(self, tmp_path):
        """Test scanning an empty directory returns empty list."""
        scanner = file_scanner.FileScanner(tmp_path)
        result = scanner.scan()
        assert result == []

    def test_scan_with_python_files(self, tmp_path):
        """Test scanning directory with Python files."""
        # Create test files
        (tmp_path / "test1.py").write_text("# test")
        (tmp_path / "test2.py").write_text("# test")
        (tmp_path / "not_python.txt").write_text("# test")

        scanner = file_scanner.FileScanner(tmp_path)
        result = scanner.scan()

        assert len(result) == 2
        assert all(p.suffix == ".py" for p in result)
        assert all(p.name in ["test1.py", "test2.py"] for p in result)

    def test_scan_with_exclusion_patterns(self, tmp_path):
        """Test scanning with exclusion patterns."""
        # Create test files
        (tmp_path / "include.py").write_text("# test")
        (tmp_path / "exclude.py").write_text("# test")

        scanner = file_scanner.FileScanner(tmp_path, exclude_patterns=["**/exclude.py"])
        result = scanner.scan()

        assert len(result) == 1
        assert result[0].name == "include.py"

    def test_scan_recursive(self, tmp_path):
        """Test scanning finds files in subdirectories."""
        # Create nested structure
        subdir = tmp_path / "subdir"
        subdir.mkdir()
        (tmp_path / "root.py").write_text("# test")
        (subdir / "nested.py").write_text("# test")

        scanner = file_scanner.FileScanner(tmp_path)
        result = scanner.scan()

        assert len(result) == 2
        assert any(p.name == "root.py" for p in result)
        assert any(p.name == "nested.py" for p in result)
