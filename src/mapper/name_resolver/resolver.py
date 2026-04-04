"""Name resolution for Python code.

Note on Decorator Name Resolution:
    Decorator name resolution is currently disabled because DecoratorInfo is an immutable
    (frozen=True) attrs class. To resolve decorator names, we would need to create new
    DecoratorInfo instances with updated names, which adds complexity.

    Current behavior:
    - Decorator names are stored exactly as they appear in source code
    - No FQN resolution is performed (e.g., @dataclass stays as "dataclass", not "attrs.define")
    - This is acceptable because decorators are stored as structured nodes in Neo4j with full_text

    If FQN resolution becomes necessary:
    - Create new DecoratorInfo instances with resolved names during extraction result processing
    - Preserve original names in full_text for reference
    - Update tests in test_name_resolver/test_resolver.py to verify decorator resolution
"""

from mapper.ast_parser import models as ast_models
from mapper.name_resolver import models
from mapper.name_resolver.models import ResolutionFailureReason


class NameResolver:
    """Resolves local names to fully qualified names using import information.

    Handles four import patterns:
    - import X          -> X maps to X
    - import X as Y     -> Y maps to X
    - from X import Y   -> Y maps to X.Y
    - from X import Y as Z -> Z maps to X.Y
    """

    def _build_name_map(self) -> dict[str, str]:
        """Build mapping from local names to FQNs.

        Returns:
            Dictionary mapping local names to fully qualified names
        """
        name_map: dict[str, str] = {}

        for imp in self.imports:
            if imp.alias:
                # import pandas as pd -> pd maps to pandas
                name_map[imp.alias] = imp.module
            elif imp.module in imp.names:
                # import pandas -> pandas maps to pandas (not pandas.pandas)
                # This is the case where module and name are the same
                # Get the top-level module name for multi-part imports
                # e.g., import os.path -> os maps to os
                top_level = imp.module.split(".")[0]
                name_map[top_level] = top_level
            else:
                # from X import Y (no alias)
                # Y maps to X.Y
                for name in imp.names:
                    if name not in imp.aliases:  # Not aliased
                        fqn = f"{imp.module}.{name}"
                        name_map[name] = fqn

            # from X import Y as Z
            # Z maps to X.Y
            for original, alias in imp.aliases.items():
                fqn = f"{imp.module}.{original}"
                name_map[alias] = fqn

        return name_map

    def __init__(self, imports: list[ast_models.ImportInfo], module_name: str):
        """Initialize name resolver.

        Args:
            imports: List of imports from module
            module_name: Name of the module being analyzed (for internal resolution)
        """
        self.imports = imports
        self.module_name = module_name
        self._name_map = self._build_name_map()

    def resolve(self, name: str, context: str | None = None) -> str | models.UnresolvedName:
        """Resolve a local name to its FQN.

        Args:
            name: Local name to resolve (e.g., "pd", "DataFrame", "attrs.define")
            context: Context where name appears (for error reporting)

        Returns:
            FQN if resolved, UnresolvedName if not
        """
        # Handle attribute access: "pd.DataFrame" -> resolve "pd" first
        if "." in name:
            parts = name.split(".", 1)
            prefix = parts[0]
            suffix = parts[1]

            if prefix in self._name_map:
                # Resolve prefix and append suffix
                resolved_prefix = self._name_map[prefix]
                return f"{resolved_prefix}.{suffix}"
            else:
                # Prefix not in imports, could be:
                # - Module-local reference (self.method, ClassName.method)
                # - External name not imported
                return models.UnresolvedName(
                    original_name=name,
                    context=context,
                    reason=ResolutionFailureReason.NOT_IN_IMPORTS,
                )

        # Simple name: direct lookup
        if name in self._name_map:
            return self._name_map[name]

        # Not found in imports
        return models.UnresolvedName(
            original_name=name, context=context, reason=ResolutionFailureReason.NOT_IN_IMPORTS
        )

    def resolve_extraction_result(
        self, result: ast_models.ExtractionResult
    ) -> tuple[ast_models.ExtractionResult, list[models.UnresolvedName]]:
        """Resolve all names in extraction result.

        This is a post-extraction pass that resolves:
        - Decorator names on functions/methods
        - Function call names
        - Base class names in inheritance

        Args:
            result: Extraction result to resolve

        Returns:
            Tuple of (updated result, list of unresolved names)
        """
        unresolved: list[models.UnresolvedName] = []

        # Resolve decorator names in functions
        # NOTE: Decorator name resolution temporarily disabled since DecoratorInfo is frozen
        # TODO: If needed, implement by creating new DecoratorInfo instances with resolved names
        for func in result.functions:
            func_fqn = f"{result.module.name}.{func.name}"
            # for dec_info in func.decorators:
            #     decorator_name = dec_info.name
            #     resolved = self.resolve(decorator_name, context=func_fqn)
            #     if isinstance(resolved, models.UnresolvedName):
            #         unresolved.append(resolved)

            # Resolve function call names
            for call in func.calls:
                resolved = self.resolve(call.full_name, context=func_fqn)
                if isinstance(resolved, models.UnresolvedName):
                    unresolved.append(resolved)
                else:
                    # Update full_name with resolved FQN
                    object.__setattr__(call, "full_name", resolved)

        # Resolve base classes and method decorators in classes
        for class_info in result.classes:
            class_fqn = f"{result.module.name}.{class_info.name}"

            # Resolve base class names
            for i, base in enumerate(class_info.bases):
                resolved = self.resolve(base, context=class_fqn)
                if isinstance(resolved, models.UnresolvedName):
                    unresolved.append(resolved)
                else:
                    class_info.bases[i] = resolved  # Update with resolved FQN

            # Resolve method decorators
            # NOTE: Decorator name resolution temporarily disabled since DecoratorInfo is frozen
            # TODO: If needed, implement by creating new DecoratorInfo instances with resolved names
            for method in class_info.methods:
                method_fqn = f"{class_fqn}.{method.name}"
                # for dec_info in method.decorators:
                #     decorator_name = dec_info.name
                #     resolved = self.resolve(decorator_name, context=method_fqn)
                #     if isinstance(resolved, models.UnresolvedName):
                #         unresolved.append(resolved)

                # Resolve method call names
                for call in method.calls:
                    resolved = self.resolve(call.full_name, context=method_fqn)
                    if isinstance(resolved, models.UnresolvedName):
                        unresolved.append(resolved)
                    else:
                        # Update full_name with resolved FQN
                        object.__setattr__(call, "full_name", resolved)

        return result, unresolved
