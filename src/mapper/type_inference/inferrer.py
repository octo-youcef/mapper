"""Type inference for Python code."""

import ast

from mapper import ast_parser
from mapper.type_inference import models


class TypeInferrer:
    """Infers types from Python code using pre-extracted AST data."""

    def __init__(self, extraction: ast_parser.models.ExtractionResult, tree: ast.Module):
        """Initialize inferrer with extracted AST data.

        Args:
            extraction: Pre-extracted code structure from ASTExtractor
            tree: Parsed AST tree (to avoid re-parsing)
        """
        self.extraction = extraction
        self.tree = tree
        self._function_nodes: dict[str, ast.FunctionDef] = {}
        self._function_info: dict[str, ast_parser.models.FunctionInfo] = {}
        self._build_function_index()

    def _build_function_index(self) -> None:
        """Build index of function nodes and info by name."""
        # Index AST nodes for return statement analysis
        for node in ast.walk(self.tree):
            if isinstance(node, ast.FunctionDef):
                self._function_nodes[node.name] = node

        # Index extracted function info for annotations
        for func in self.extraction.functions:
            self._function_info[func.name] = func

    def infer_function_return(
        self, function_name: str, use_annotation: bool = True
    ) -> models.InferenceResult:
        """Infer return type of a function.

        Args:
            function_name: Name of function to analyze
            use_annotation: Whether to use type annotation if present

        Returns:
            Inference result with type and confidence
        """
        func_info = self._function_info.get(function_name)
        func_node = self._function_nodes.get(function_name)

        if func_info is None or func_node is None:
            return models.InferenceResult(inferred_type="Unknown", confidence="low")

        # Check if function has explicit return annotation (only if use_annotation=True)
        if use_annotation and func_info.return_type:
            return models.InferenceResult(inferred_type=func_info.return_type, confidence="high")

        # Analyze return statements
        return_types = set()
        has_explicit_return = False
        has_unknown_return = False

        for node in ast.walk(func_node):
            if isinstance(node, ast.Return):
                has_explicit_return = True
                if node.value:  # Has return value
                    inferred = self._infer_from_expression(node.value)
                    if inferred:
                        return_types.add(inferred)
                    else:
                        # Could not infer type from expression
                        has_unknown_return = True
                else:  # Bare "return" statement returns None
                    return_types.add("None")

        # No explicit return statements means implicit return None
        if not has_explicit_return:
            return models.InferenceResult(inferred_type="None", confidence="high")

        # Has returns but couldn't infer any types (all were unknown)
        if not return_types and has_unknown_return:
            return models.InferenceResult(inferred_type="Unknown", confidence="low")

        # Has returns with only None (explicit bare returns)
        if not return_types:
            return models.InferenceResult(inferred_type="None", confidence="high")

        # If all returns are the same type
        if len(return_types) == 1:
            return models.InferenceResult(inferred_type=list(return_types)[0], confidence="high")

        # Multiple return types - use union type
        return models.InferenceResult(
            inferred_type=" | ".join(sorted(return_types)), confidence="medium"
        )

    def validate_function(self, function_name: str) -> models.ValidationResult:
        """Validate function return type against annotation.

        Args:
            function_name: Name of function to validate

        Returns:
            Validation result
        """
        if function_name not in self._function_info:
            return models.ValidationResult(matches=None)

        func_info = self._function_info[function_name]

        # No annotation to validate against
        if not func_info.return_type:
            inference = self.infer_function_return(function_name)
            return models.ValidationResult(matches=None, inferred_type=inference.inferred_type)

        # Get annotated type from extracted info
        annotated_type = func_info.return_type

        # Infer actual type from code (ignore annotation for validation)
        inference = self.infer_function_return(function_name, use_annotation=False)

        # Compare
        if inference.inferred_type == annotated_type:
            return models.ValidationResult(matches=True, inferred_type=inference.inferred_type)

        # Type mismatch
        warnings = [
            f"Type mismatch: annotated as {annotated_type}, but inferred {inference.inferred_type}"
        ]
        return models.ValidationResult(
            matches=False, inferred_type=inference.inferred_type, warnings=warnings
        )

    def _infer_from_expression(self, node: ast.expr) -> str | None:
        """Infer type from an expression.

        Args:
            node: AST expression node

        Returns:
            Inferred type name or None
        """
        # Constructor call or function call: return User() or return create_user()
        if isinstance(node, ast.Call):
            if isinstance(node.func, ast.Name):
                func_name = node.func.id
                # Check if it's a known function - if so, infer its return type
                if func_name in self._function_nodes:
                    result = self.infer_function_return(func_name)
                    return result.inferred_type
                # Otherwise assume it's a constructor (class name)
                return func_name

        # Literal values
        elif isinstance(node, ast.Constant):
            value_type = type(node.value).__name__
            # Handle None separately
            if node.value is None:
                return "None"
            return value_type

        # String literal (deprecated but still used in older Python versions)
        elif isinstance(node, ast.Str):
            return "str"

        # Number literal (deprecated but still used in older Python versions)
        elif isinstance(node, ast.Num):
            return type(node.n).__name__

        # List literal
        elif isinstance(node, ast.List):
            return "list"

        # Dict literal
        elif isinstance(node, ast.Dict):
            return "dict"

        # None (deprecated but still used in older Python versions)
        elif isinstance(node, ast.NameConstant) and node.value is None:
            return "None"

        # Name reference (variable)
        elif isinstance(node, ast.Name):
            if node.id == "None":
                return "None"

        return None

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
