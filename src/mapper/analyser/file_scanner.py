"""File scanning for Python projects."""

from pathlib import Path


class FileScanner:
    """Scans directories for Python files."""

    def __init__(self, root_path: Path, exclude_patterns: list[str] | None = None):
        """Initialize scanner.

        Args:
            root_path: Root directory to scan
            exclude_patterns: List of glob patterns to exclude
        """
        self.root_path = Path(root_path)
        self.exclude_patterns = exclude_patterns or []

    def scan(self) -> list[Path]:
        """Scan directory for Python files.

        Returns:
            List of Python file paths found

        Raises:
            FileNotFoundError: If root path doesn't exist
        """
        if not self.root_path.exists():
            raise FileNotFoundError(f"Directory not found: {self.root_path}")

        files = []
        for path in self.root_path.rglob("*.py"):
            if self._should_include(path):
                files.append(path)

        return sorted(files)

    def _should_include(self, path: Path) -> bool:
        """Check if file should be included based on exclusion patterns.

        Args:
            path: File path to check

        Returns:
            True if file should be included
        """
        for pattern in self.exclude_patterns:
            if path.match(pattern):
                return False
        return True
