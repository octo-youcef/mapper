"""AST extraction for Python code."""

import ast
import inspect
from pathlib import Path

from mapper import name_resolver
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

    @staticmethod
    def _is_public(name: str) -> bool:
        """Determine if a name is public based on Python naming conventions.

        Args:
            name: Name to check

        Returns:
            True if public, False if private
        """
        # Dunder methods (__init__, __str__, etc.) are public
        if name.startswith("__") and name.endswith("__"):
            return True
        # Single underscore prefix indicates private
        if name.startswith("_"):
            return False
        # Everything else is public
        return True

    @staticmethod
    def _extract_all_exports(tree: ast.Module) -> list[str]:
        """Extract names from __all__ assignment.

        Args:
            tree: AST module tree

        Returns:
            List of exported names, empty if no __all__ defined
        """
        for node in tree.body:
            if isinstance(node, ast.Assign):
                for target in node.targets:
                    if isinstance(target, ast.Name) and target.id == "__all__":
                        # Found __all__ assignment
                        if isinstance(node.value, ast.List):
                            # __all__ = ["name1", "name2"]
                            names = []
                            for elt in node.value.elts:
                                if isinstance(elt, ast.Constant) and isinstance(elt.value, str):
                                    names.append(elt.value)
                            return names
        return []

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
        exported_names = self._extract_all_exports(self.tree)
        module = models.ModuleInfo(
            path=self.file_path,
            name=module_name,
            docstring=docstring,
            exported_names=exported_names,
        )

        result = models.ExtractionResult(module=module)

        # Extract top-level elements
        for node in ast.walk(self.tree):
            if isinstance(node, ast.Import):
                # import pandas as pd -> ImportInfo(module="pandas", names=["pandas"], alias="pd")
                # import pandas -> ImportInfo(module="pandas", names=["pandas"], alias=None)
                for alias in node.names:
                    result.imports.append(
                        models.ImportInfo(
                            module=alias.name,
                            names=[alias.name],
                            alias=alias.asname if alias.asname else None,
                        )
                    )
            elif isinstance(node, ast.ImportFrom):
                # from typing import Optional as Opt
                # -> ImportInfo(module="typing", names=["Optional"], aliases={"Optional": "Opt"})
                if node.module:
                    names = [alias.name for alias in node.names]
                    aliases = {alias.name: alias.asname for alias in node.names if alias.asname}
                    result.imports.append(
                        models.ImportInfo(
                            module=node.module, names=names, aliases=aliases if aliases else {}
                        )
                    )

        # Extract classes and functions from top level
        for node in self.tree.body:
            if isinstance(node, ast.ClassDef):
                result.classes.append(self._extract_class(node))
            elif isinstance(node, ast.FunctionDef):
                result.functions.append(self._extract_function(node))

        # Post-extraction: resolve names to FQNs
        resolver = name_resolver.NameResolver(result.imports, module_name)
        result, unresolved = resolver.resolve_extraction_result(result)
        result.unresolved_names = unresolved

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

        # Extract decorators
        decorators = self._extract_decorators(node.decorator_list)

        methods = []
        for item in node.body:
            if isinstance(item, ast.FunctionDef):
                methods.append(self._extract_function(item))

        return models.ClassInfo(
            name=node.name,
            is_public=self._is_public(node.name),
            docstring=ast.get_docstring(node),
            bases=bases,
            decorators=decorators,
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
        parameters = self._extract_parameters(node.args)

        # Extract return type
        return_type = None
        if node.returns:
            return_type = self._get_type_string(node.returns)

        # Extract decorators
        decorators = self._extract_decorators(node.decorator_list)

        # Extract function calls
        calls = []
        for child in ast.walk(node):
            if isinstance(child, ast.Call):
                call_info = self._extract_call(child)
                if call_info:
                    calls.append(call_info)

        return models.FunctionInfo(
            name=node.name,
            is_public=self._is_public(node.name),
            docstring=ast.get_docstring(node),
            parameters=parameters,
            return_type=return_type,
            decorators=decorators,
            calls=calls,
        )

    def _extract_parameters(self, args: ast.arguments) -> list[models.ParameterInfo]:
        """Extract parameter information from function arguments.

        Args:
            args: AST arguments node

        Returns:
            List of ParameterInfo instances
        """
        parameters: list[models.ParameterInfo] = []
        position = 0

        # Positional-only parameters (before /) - Python 3.8+
        for arg in args.posonlyargs:
            type_hint = self._get_type_string(arg.annotation) if arg.annotation else None

            # Get default value if exists (defaults are right-aligned with parameters)
            # For def f(a, b, c=1, d=2, /): defaults=[1, 2] applies to params c and d
            # Calculate offset: if 4 params and 2 defaults, offset=2, so params at index 2+ have defaults
            default = None
            default_offset = len(args.posonlyargs) - len(args.defaults)
            param_index = args.posonlyargs.index(arg)
            if param_index >= default_offset and args.defaults:
                default_node = args.defaults[param_index - default_offset]
                default = ast.unparse(default_node)

            parameters.append(
                models.ParameterInfo(
                    name=arg.arg,
                    type_hint=type_hint,
                    has_type_hint=type_hint is not None,
                    default=default,
                    position=position,
                    kind=models.ParameterKind.POSITIONAL_ONLY,
                )
            )
            position += 1

        # Positional-or-keyword parameters (normal parameters)
        for arg in args.args:
            type_hint = self._get_type_string(arg.annotation) if arg.annotation else None
            # Get default value if exists (defaults are right-aligned)
            default = None
            num_defaults = len(args.defaults)
            num_params = len(args.posonlyargs) + len(args.args)
            defaults_start = num_params - num_defaults
            if position >= defaults_start and args.defaults:
                default_index = position - defaults_start
                default_node = args.defaults[default_index]
                default = ast.unparse(default_node)

            parameters.append(
                models.ParameterInfo(
                    name=arg.arg,
                    type_hint=type_hint,
                    has_type_hint=type_hint is not None,
                    default=default,
                    position=position,
                    kind=models.ParameterKind.POSITIONAL_OR_KEYWORD,
                )
            )
            position += 1

        # *args (vararg)
        if args.vararg:
            type_hint = self._get_type_string(args.vararg.annotation) if args.vararg.annotation else None
            parameters.append(
                models.ParameterInfo(
                    name=args.vararg.arg,
                    type_hint=type_hint,
                    has_type_hint=type_hint is not None,
                    default=None,  # *args cannot have defaults
                    position=position,
                    kind=models.ParameterKind.VAR_POSITIONAL,
                )
            )
            position += 1

        # Keyword-only parameters (after *)
        for i, arg in enumerate(args.kwonlyargs):
            type_hint = self._get_type_string(arg.annotation) if arg.annotation else None
            # kw_defaults is aligned with kwonlyargs (not right-aligned)
            default = None
            if i < len(args.kw_defaults) and args.kw_defaults[i] is not None:
                default = ast.unparse(args.kw_defaults[i])

            parameters.append(
                models.ParameterInfo(
                    name=arg.arg,
                    type_hint=type_hint,
                    has_type_hint=type_hint is not None,
                    default=default,
                    position=position,
                    kind=models.ParameterKind.KEYWORD_ONLY,
                )
            )
            position += 1

        # **kwargs (kwarg)
        if args.kwarg:
            type_hint = self._get_type_string(args.kwarg.annotation) if args.kwarg.annotation else None
            parameters.append(
                models.ParameterInfo(
                    name=args.kwarg.arg,
                    type_hint=type_hint,
                    has_type_hint=type_hint is not None,
                    default=None,  # **kwargs cannot have defaults
                    position=position,
                    kind=models.ParameterKind.VAR_KEYWORD,
                )
            )
            position += 1

        return parameters

    def _extract_decorators(self, decorator_list: list[ast.expr]) -> list[models.DecoratorInfo]:
        """Extract decorator information from decorator list.

        Args:
            decorator_list: List of AST decorator nodes

        Returns:
            List of DecoratorInfo instances
        """
        decorators: list[models.DecoratorInfo] = []

        for dec in decorator_list:
            # Get full text with @ symbol
            full_text = "@" + ast.unparse(dec)

            # Extract decorator name
            if isinstance(dec, ast.Name):
                # Simple decorator: @property
                name = dec.id
                args = None
            elif isinstance(dec, ast.Call):
                # Decorator with arguments: @rate_limit(10)
                if isinstance(dec.func, ast.Name):
                    name = dec.func.id
                elif isinstance(dec.func, ast.Attribute):
                    name = ast.unparse(dec.func)
                else:
                    name = "unknown"
                # Extract args as string including parentheses
                args_str = ast.unparse(dec)
                # Remove the function name part to get just the args
                if "(" in args_str:
                    args = "(" + args_str.split("(", 1)[1]
                else:
                    args = "()"
            elif isinstance(dec, ast.Attribute):
                # Decorator with attribute access: @app.route
                name = ast.unparse(dec)
                args = None
            else:
                name = "unknown"
                args = None

            decorators.append(
                models.DecoratorInfo(
                    name=name,
                    args=args,
                    full_text=full_text,
                )
            )

        return decorators

    def _extract_call(self, node: ast.Call) -> models.CallInfo | None:
        """Extract call information from a Call node.

        Args:
            node: AST Call node

        Returns:
            CallInfo with structured call data, or None if call cannot be parsed
        """
        if isinstance(node.func, ast.Name):
            # Simple call: foo()
            return models.CallInfo(
                name=node.func.id,
                call_type=models.CallType.SIMPLE,
                full_name=node.func.id,
                qualifier=None,
            )
        elif isinstance(node.func, ast.Attribute):
            # Attribute call: obj.method() or module.function()
            full_name = self._get_attribute_string(node.func)

            # Parse the qualifier (what comes before the dot)
            qualifier: str | None
            if isinstance(node.func.value, ast.Name):
                qualifier = node.func.value.id
            else:
                # Complex expressions like obj.attr.method() - use full prefix
                qualifier = (
                    self._get_attribute_string(node.func.value)
                    if isinstance(node.func.value, ast.Attribute)
                    else None
                )

            return models.CallInfo(
                name=node.func.attr,
                call_type=models.CallType.ATTRIBUTE,
                full_name=full_name,
                qualifier=qualifier,
            )
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
