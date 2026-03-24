"""Main analyser orchestrator."""

from collections.abc import Callable
from pathlib import Path

from mapper import ast_parser, graph_loader, type_inference
from mapper.analyser import file_scanner, models


class Analyser:
    """Orchestrates code analysis workflow."""

    def __init__(
        self,
        root_path: Path,
        exclude_patterns: list[str] | None = None,
        loader: graph_loader.GraphLoader | None = None,
    ):
        """Initialize analyser.

        Args:
            root_path: Root directory to analyse
            exclude_patterns: List of glob patterns to exclude
            loader: Optional GraphLoader for storing results in Neo4j.
                    If None, analysis results are returned but not persisted.
                    This is useful for testing (mock the loader) and supports
                    future alternative storage backends.
        """
        self.root_path = Path(root_path)
        self.exclude_patterns = exclude_patterns or []
        self.loader = loader

    def analyse(
        self, progress_callback: Callable[[int, int, str], None] | None = None
    ) -> models.AnalyseResult:
        """Analyse codebase.

        Args:
            progress_callback: Optional callback for progress updates (current, total, filename)

        Returns:
            Analysis results
        """
        # Scan for files
        scanner = file_scanner.FileScanner(self.root_path, self.exclude_patterns)
        files = scanner.scan()

        result = models.AnalyseResult(success=True)

        # Process each file
        for i, file_path in enumerate(files, 1):
            if progress_callback:
                progress_callback(i, len(files), str(file_path.name))

            try:
                self._analyse_file(file_path, result)
            except SyntaxError as e:
                result.errors.append(f"{file_path.name}: {e}")
            except Exception as e:
                result.errors.append(f"{file_path.name}: {e}")

        # Finalize graph relationships if loader provided
        if self.loader:
            self.loader.finalize()

        return result

    def _analyse_file(self, file_path: Path, result: models.AnalyseResult) -> None:
        """Analyse a single file.

        Args:
            file_path: Path to file to analyse
            result: Result object to update
        """
        code = file_path.read_text()

        # Extract AST information (parses once)
        extractor = ast_parser.ASTExtractor(code, str(file_path))
        extraction = extractor.extract()

        # Count elements
        result.modules_count += 1
        result.classes_count += len(extraction.classes)
        result.functions_count += len(extraction.functions)

        # Track relationships from function calls
        for func in extraction.functions:
            result.relationships_count += len(func.calls)

        # Load into graph database if loader provided
        if self.loader:
            self.loader.load_extraction(extraction)
            # Count nodes created: module + classes + functions + methods in classes
            result.nodes_created += 1  # module
            result.nodes_created += len(extraction.classes)
            result.nodes_created += len(extraction.functions)
            for class_info in extraction.classes:
                result.nodes_created += len(class_info.methods)

        # Type inference and validation (reuses parsed tree)
        if extractor.tree:
            inferrer = type_inference.TypeInferrer(extraction, extractor.tree)
            for func in extraction.functions:
                if func.return_type:  # Has type annotation
                    validation = inferrer.validate_function(func.name)
                    if validation.matches is False:
                        result.warnings.append(
                            f"{file_path.name}:{func.name} - Type mismatch: "
                            f"expected {func.return_type}, inferred {validation.inferred_type}"
                        )
