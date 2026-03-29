"""Tests for name resolver."""

from mapper import name_resolver
from mapper.ast_parser import models


class TestNameResolver:
    """Tests for NameResolver class."""

    def test_resolve_simple_import(self):
        """Test resolving names from 'import X' pattern."""
        imports = [models.ImportInfo(module="pandas", names=["pandas"])]
        resolver = name_resolver.NameResolver(imports, "test_module")

        # pandas -> pandas
        resolved = resolver.resolve("pandas")
        assert resolved == "pandas"

    def test_resolve_import_with_alias(self):
        """Test resolving names from 'import X as Y' pattern."""
        imports = [models.ImportInfo(module="pandas", names=["pandas"], alias="pd")]
        resolver = name_resolver.NameResolver(imports, "test_module")

        # pd -> pandas
        resolved = resolver.resolve("pd")
        assert resolved == "pandas"

        # pandas should not resolve (we imported as pd)
        resolved = resolver.resolve("pandas")
        assert isinstance(resolved, name_resolver.UnresolvedName)

    def test_resolve_from_import(self):
        """Test resolving names from 'from X import Y' pattern."""
        imports = [models.ImportInfo(module="typing", names=["Optional"])]
        resolver = name_resolver.NameResolver(imports, "test_module")

        # Optional -> typing.Optional
        resolved = resolver.resolve("Optional")
        assert resolved == "typing.Optional"

    def test_resolve_from_import_with_alias(self):
        """Test resolving names from 'from X import Y as Z' pattern."""
        imports = [
            models.ImportInfo(module="typing", names=["Optional"], aliases={"Optional": "Opt"})
        ]
        resolver = name_resolver.NameResolver(imports, "test_module")

        # Opt -> typing.Optional
        resolved = resolver.resolve("Opt")
        assert resolved == "typing.Optional"

        # Optional should not resolve (we imported as Opt)
        resolved = resolver.resolve("Optional")
        assert isinstance(resolved, name_resolver.UnresolvedName)

    def test_resolve_from_import_multiple(self):
        """Test resolving multiple names from same module."""
        imports = [models.ImportInfo(module="typing", names=["Optional", "Any", "List"])]
        resolver = name_resolver.NameResolver(imports, "test_module")

        assert resolver.resolve("Optional") == "typing.Optional"
        assert resolver.resolve("Any") == "typing.Any"
        assert resolver.resolve("List") == "typing.List"

    def test_resolve_attribute_access(self):
        """Test resolving attribute access like 'pd.DataFrame'."""
        imports = [models.ImportInfo(module="pandas", names=["pandas"], alias="pd")]
        resolver = name_resolver.NameResolver(imports, "test_module")

        # pd.DataFrame -> pandas.DataFrame
        resolved = resolver.resolve("pd.DataFrame")
        assert resolved == "pandas.DataFrame"

    def test_resolve_nested_attribute_access(self):
        """Test resolving nested attribute access like 'attrs.define'."""
        imports = [models.ImportInfo(module="attrs", names=["attrs"])]
        resolver = name_resolver.NameResolver(imports, "test_module")

        # attrs.define -> attrs.define
        resolved = resolver.resolve("attrs.define")
        assert resolved == "attrs.define"

    def test_resolve_multi_part_module_import(self):
        """Test resolving multi-part module imports like 'import os.path'."""
        imports = [models.ImportInfo(module="os.path", names=["os.path"])]
        resolver = name_resolver.NameResolver(imports, "test_module")

        # os should map to os (top-level)
        resolved = resolver.resolve("os")
        assert resolved == "os"

        # os.path should map to os.path
        resolved = resolver.resolve("os.path")
        assert resolved == "os.path"

    def test_unresolved_name_not_imported(self):
        """Test that unimported names return UnresolvedName."""
        imports = [models.ImportInfo(module="pandas", names=["pandas"])]
        resolver = name_resolver.NameResolver(imports, "test_module")

        resolved = resolver.resolve("numpy", context="test_func")
        assert isinstance(resolved, name_resolver.UnresolvedName)
        assert resolved.original_name == "numpy"
        assert resolved.context == "test_func"
        assert "not found in imports" in resolved.reason

    def test_unresolved_name_attribute_prefix_unknown(self):
        """Test that attribute access with unknown prefix returns UnresolvedName."""
        imports = [models.ImportInfo(module="pandas", names=["pandas"], alias="pd")]
        resolver = name_resolver.NameResolver(imports, "test_module")

        resolved = resolver.resolve("np.array")
        assert isinstance(resolved, name_resolver.UnresolvedName)
        assert resolved.original_name == "np.array"
        assert "prefix 'np' not in imports" in resolved.reason

    def test_resolve_mixed_imports(self):
        """Test resolving with mixed import patterns."""
        imports = [
            models.ImportInfo(module="pandas", names=["pandas"], alias="pd"),
            models.ImportInfo(module="numpy", names=["numpy"]),
            models.ImportInfo(module="typing", names=["Optional", "Any"]),
            models.ImportInfo(module="attrs", names=["define"], aliases={"define": "dataclass"}),
        ]
        resolver = name_resolver.NameResolver(imports, "test_module")

        assert resolver.resolve("pd") == "pandas"
        assert resolver.resolve("numpy") == "numpy"
        assert resolver.resolve("Optional") == "typing.Optional"
        assert resolver.resolve("Any") == "typing.Any"
        assert resolver.resolve("dataclass") == "attrs.define"
        assert resolver.resolve("pd.DataFrame") == "pandas.DataFrame"
        assert resolver.resolve("numpy.array") == "numpy.array"

    def test_unresolved_name_str_representation(self):
        """Test UnresolvedName string representation."""
        unresolved = name_resolver.UnresolvedName(
            original_name="unknown", context="test.func", reason="not imported"
        )
        result_str = str(unresolved)
        assert "'unknown'" in result_str
        assert "test.func" in result_str
        assert "not imported" in result_str


class TestNameResolverWithExtractionResult:
    """Tests for resolving names in extraction results."""

    def test_resolve_decorator_names(self):
        """Test resolving decorator names on functions."""
        imports = [models.ImportInfo(module="attrs", names=["define"], aliases={"define": "dataclass"})]

        func = models.FunctionInfo(
            name="MyClass",
            is_public=True,
            decorators=[{"name": "dataclass", "args": []}],
        )

        result = models.ExtractionResult(
            module=models.ModuleInfo(path="test.py", name="test"),
            imports=imports,
            functions=[func],
        )

        resolver = name_resolver.NameResolver(imports, "test")
        resolved_result, unresolved = resolver.resolve_extraction_result(result)

        # Decorator name should be resolved
        assert resolved_result.functions[0].decorators[0]["name"] == "attrs.define"
        assert len(unresolved) == 0

    def test_resolve_base_class_names(self):
        """Test resolving base class names in inheritance."""
        imports = [models.ImportInfo(module="models", names=["BaseModel"])]

        cls = models.ClassInfo(
            name="User",
            is_public=True,
            bases=["BaseModel"],
        )

        result = models.ExtractionResult(
            module=models.ModuleInfo(path="test.py", name="test"),
            imports=imports,
            classes=[cls],
        )

        resolver = name_resolver.NameResolver(imports, "test")
        resolved_result, unresolved = resolver.resolve_extraction_result(result)

        # Base class name should be resolved
        assert resolved_result.classes[0].bases[0] == "models.BaseModel"
        assert len(unresolved) == 0

    def test_resolve_method_decorators(self):
        """Test resolving decorator names on methods."""
        imports = [models.ImportInfo(module="builtins", names=["property"])]

        method = models.FunctionInfo(
            name="name",
            is_public=True,
            decorators=[{"name": "property", "args": []}],
        )

        cls = models.ClassInfo(
            name="User",
            is_public=True,
            methods=[method],
        )

        result = models.ExtractionResult(
            module=models.ModuleInfo(path="test.py", name="test"),
            imports=imports,
            classes=[cls],
        )

        resolver = name_resolver.NameResolver(imports, "test")
        resolved_result, unresolved = resolver.resolve_extraction_result(result)

        # Method decorator should be resolved
        assert resolved_result.classes[0].methods[0].decorators[0]["name"] == "builtins.property"
        assert len(unresolved) == 0

    def test_collect_unresolved_names(self):
        """Test that unresolved names are collected."""
        imports = []  # No imports

        func = models.FunctionInfo(
            name="process",
            is_public=True,
            decorators=[{"name": "unknown_decorator", "args": []}],
        )

        cls = models.ClassInfo(
            name="User",
            is_public=True,
            bases=["UnknownBase"],
        )

        result = models.ExtractionResult(
            module=models.ModuleInfo(path="test.py", name="test"),
            imports=imports,
            functions=[func],
            classes=[cls],
        )

        resolver = name_resolver.NameResolver(imports, "test")
        resolved_result, unresolved = resolver.resolve_extraction_result(result)

        # Should have 2 unresolved names
        assert len(unresolved) == 2
        unresolved_names = [u.original_name for u in unresolved]
        assert "unknown_decorator" in unresolved_names
        assert "UnknownBase" in unresolved_names
