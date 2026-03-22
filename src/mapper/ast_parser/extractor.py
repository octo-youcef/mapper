"""AST extraction for Python code."""

import ast
from pathlib import Path

from mapper.ast_parser import models


class ASTExtractor:
    """Extracts information from Python AST."""

    def __init__(self, code: str, file_path: str):
        """Initialize extractor.

        Args:
            code: Python source code
            file_path: Path to the source file
        """
        self.code = code
        self.file_path = file_path
        self.tree: ast.Module | None = None

    def extract(self) -> models.ExtractionResult:
        """Extract information from code.

        Returns:
            Extraction result with all parsed information

        Raises:
            SyntaxError: If code has syntax errors
        """
        self.tree = ast.parse(self.code)

        # Extract module info
        module_name = Path(self.file_path).stem
        docstring = ast.get_docstring(self.tree)
        module = models.ModuleInfo(path=self.file_path, name=module_name, docstring=docstring)

        result = models.ExtractionResult(module=module)

        # Extract top-level elements
        for node in ast.walk(self.tree):
            if isinstance(node, ast.Import):
                for alias in node.names:
                    result.imports.append(models.ImportInfo(module=alias.name, names=[alias.name]))
            elif isinstance(node, ast.ImportFrom):
                if node.module:
                    names = [alias.name for alias in node.names]
                    result.imports.append(models.ImportInfo(module=node.module, names=names))

        # Extract classes and functions from top level
        for node in self.tree.body:
            if isinstance(node, ast.ClassDef):
                result.classes.append(self._extract_class(node))
            elif isinstance(node, ast.FunctionDef):
                result.functions.append(self._extract_function(node))

        return result

    def _extract_class(self, node: ast.ClassDef) -> models.ClassInfo:
        """Extract class information.

        Args:
            node: AST class definition node

        Returns:
            Class information
        """
        bases = []
        for base in node.bases:
            if isinstance(base, ast.Name):
                bases.append(base.id)

        methods = []
        for item in node.body:
            if isinstance(item, ast.FunctionDef):
                methods.append(self._extract_function(item))

        return models.ClassInfo(
            name=node.name,
            docstring=ast.get_docstring(node),
            bases=bases,
            methods=methods,
        )

    def _extract_function(self, node: ast.FunctionDef) -> models.FunctionInfo:
        """Extract function information.

        Args:
            node: AST function definition node

        Returns:
            Function information
        """
        # Extract parameters
        parameters = []
        for arg in node.args.args:
            param_type = None
            if arg.annotation:
                param_type = self._get_type_string(arg.annotation)
            parameters.append({"name": arg.arg, "type": param_type})

        # Extract return type
        return_type = None
        if node.returns:
            return_type = self._get_type_string(node.returns)

        # Extract decorators
        decorators = []
        for dec in node.decorator_list:
            dec_info = self._extract_decorator(dec)
            decorators.append(dec_info)

        # Extract function calls
        calls = []
        for child in ast.walk(node):
            if isinstance(child, ast.Call):
                if isinstance(child.func, ast.Name):
                    calls.append(child.func.id)
                elif isinstance(child.func, ast.Attribute):
                    calls.append(self._get_attribute_string(child.func))

        return models.FunctionInfo(
            name=node.name,
            docstring=ast.get_docstring(node),
            parameters=parameters,
            return_type=return_type,
            decorators=decorators,
            calls=calls,
        )

    def _extract_decorator(self, node: ast.expr) -> dict[str, str | list]:
        """Extract decorator information.

        Only extracts decorator names for structural analysis.
        Does not extract argument values (consistent with not storing
        function call arguments, parameter defaults, etc.).

        Args:
            node: AST decorator node

        Returns:
            Decorator information dict with name only
        """
        if isinstance(node, ast.Name):
            return {"name": node.id, "args": []}
        elif isinstance(node, ast.Call):
            # For decorators with arguments (e.g., @app.route("/users")),
            # extract only the decorator name, not the argument values
            if isinstance(node.func, ast.Name):
                return {"name": node.func.id, "args": []}
            elif isinstance(node.func, ast.Attribute):
                return {"name": self._get_attribute_string(node.func), "args": []}
        elif isinstance(node, ast.Attribute):
            return {"name": self._get_attribute_string(node), "args": []}
        return {"name": "unknown", "args": []}

    def _get_type_string(self, node: ast.expr) -> str:
        """Convert type annotation node to string.

        Args:
            node: AST type annotation node

        Returns:
            Type as string
        """
        if isinstance(node, ast.Name):
            return node.id
        elif isinstance(node, ast.Constant):
            return str(node.value)
        return "Unknown"

    def _get_attribute_string(self, node: ast.Attribute) -> str:
        """Convert attribute node to string.

        Args:
            node: AST attribute node

        Returns:
            Attribute as string (e.g., 'app.route')
        """
        parts = []
        current: ast.expr = node
        while isinstance(current, ast.Attribute):
            parts.append(current.attr)
            current = current.value
        if isinstance(current, ast.Name):
            parts.append(current.id)
        return ".".join(reversed(parts))
