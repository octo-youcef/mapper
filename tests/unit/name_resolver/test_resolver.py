"""Tests for name resolver."""

import pytest

from mapper import name_resolver
from mapper.ast_parser import models


class TestNameResolver:
    """Tests for NameResolver class."""

    @pytest.mark.parametrize(
        "imports,name_to_resolve,expected_result,test_id",
        [
            # import X pattern
            (
                [models.ImportInfo(module="pandas", names=["pandas"])],
                "pandas",
                "pandas",
                "simple-import",
            ),
            # import X as Y pattern
            (
                [models.ImportInfo(module="pandas", names=["pandas"], alias="pd")],
                "pd",
                "pandas",
                "import-with-alias",
            ),
            # from X import Y pattern
            (
                [models.ImportInfo(module="typing", names=["Optional"])],
                "Optional",
                "typing.Optional",
                "from-import",
            ),
            # from X import Y as Z pattern
            (
                [
                    models.ImportInfo(
                        module="typing", names=["Optional"], aliases={"Optional": "Opt"}
                    )
                ],
                "Opt",
                "typing.Optional",
                "from-import-with-alias",
            ),
            # Attribute access (pd.DataFrame)
            (
                [models.ImportInfo(module="pandas", names=["pandas"], alias="pd")],
                "pd.DataFrame",
                "pandas.DataFrame",
                "attribute-access",
            ),
            # Nested attribute access (attrs.define)
            (
                [models.ImportInfo(module="attrs", names=["attrs"])],
                "attrs.define",
                "attrs.define",
                "nested-attribute",
            ),
            # Multi-part module (os.path) - resolve os
            (
                [models.ImportInfo(module="os.path", names=["os.path"])],
                "os",
                "os",
                "multi-part-module-base",
            ),
            # Multi-part module (os.path) - resolve os.path
            (
                [models.ImportInfo(module="os.path", names=["os.path"])],
                "os.path",
                "os.path",
                "multi-part-module-full",
            ),
        ],
        ids=lambda x: x if isinstance(x, str) and "-" in x else "",
    )
    def test_basic_resolution_patterns(self, imports, name_to_resolve, expected_result, test_id):
        """Test resolving names from different import patterns."""
        resolver = name_resolver.NameResolver(imports, "test_module")
        resolved = resolver.resolve(name_to_resolve)
        assert resolved == expected_result

    @pytest.mark.parametrize(
        "imports,name_to_resolve,test_id",
        [
            # Imported as alias, original name should not resolve
            (
                [models.ImportInfo(module="pandas", names=["pandas"], alias="pd")],
                "pandas",
                "aliased-original-name",
            ),
            # From import with alias, original should not resolve
            (
                [
                    models.ImportInfo(
                        module="typing", names=["Optional"], aliases={"Optional": "Opt"}
                    )
                ],
                "Optional",
                "from-aliased-original",
            ),
        ],
        ids=lambda x: x if isinstance(x, str) and "-" in x else "",
    )
    def test_aliased_imports_original_name_unresolved(self, imports, name_to_resolve, test_id):
        """Test that original names don't resolve when imported with aliases."""
        resolver = name_resolver.NameResolver(imports, "test_module")
        resolved = resolver.resolve(name_to_resolve)
        assert isinstance(resolved, name_resolver.UnresolvedName)

    def test_resolve_from_import_multiple(self):
        """Test resolving multiple names from same module."""
        imports = [models.ImportInfo(module="typing", names=["Optional", "Any", "List"])]
        resolver = name_resolver.NameResolver(imports, "test_module")

        assert resolver.resolve("Optional") == "typing.Optional"
        assert resolver.resolve("Any") == "typing.Any"
        assert resolver.resolve("List") == "typing.List"

    @pytest.mark.parametrize(
        "imports,name_to_resolve,context,expected_original,expected_reason,test_id",
        [
            # Name not in imports
            (
                [models.ImportInfo(module="pandas", names=["pandas"])],
                "numpy",
                "test_func",
                "numpy",
                name_resolver.models.ResolutionFailureReason.NOT_IN_IMPORTS,
                "not-imported",
            ),
            # Attribute with unknown prefix
            (
                [models.ImportInfo(module="pandas", names=["pandas"], alias="pd")],
                "np.array",
                None,
                "np.array",
                name_resolver.models.ResolutionFailureReason.NOT_IN_IMPORTS,
                "unknown-prefix",
            ),
        ],
        ids=lambda x: x if isinstance(x, str) and "-" in x else "",
    )
    def test_unresolved_names(
        self,
        imports,
        name_to_resolve,
        context,
        expected_original,
        expected_reason,
        test_id,
    ):
        """Test that unresolved names return UnresolvedName with correct metadata."""
        resolver = name_resolver.NameResolver(imports, "test_module")
        resolved = resolver.resolve(name_to_resolve, context=context)

        assert isinstance(resolved, name_resolver.UnresolvedName)
        assert resolved.original_name == expected_original
        if context:
            assert resolved.context == context
        assert resolved.reason == expected_reason

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
        """Test decorator names (currently not resolved due to frozen DecoratorInfo)."""
        imports = [
            models.ImportInfo(module="attrs", names=["define"], aliases={"define": "dataclass"})
        ]

        func = models.FunctionInfo(
            name="MyClass",
            is_public=True,
            decorators=[
                models.DecoratorInfo(name="dataclass", args=None, full_text="@dataclass")
            ],
        )

        result = models.ExtractionResult(
            module=models.ModuleInfo(path="test.py", name="test"),
            imports=imports,
            functions=[func],
        )

        resolver = name_resolver.NameResolver(imports, "test")
        resolved_result, unresolved = resolver.resolve_extraction_result(result)

        # Decorator name resolution is currently disabled (DecoratorInfo is frozen)
        # TODO: Enable decorator name resolution if needed
        assert resolved_result.functions[0].decorators[0].name == "dataclass"
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
        """Test decorator names on methods (currently not resolved due to frozen DecoratorInfo)."""
        imports = [models.ImportInfo(module="builtins", names=["property"])]

        method = models.FunctionInfo(
            name="name",
            is_public=True,
            decorators=[models.DecoratorInfo(name="property", args=None, full_text="@property")],
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

        # Decorator name resolution is currently disabled (DecoratorInfo is frozen)
        # TODO: Enable decorator name resolution if needed
        assert resolved_result.classes[0].methods[0].decorators[0].name == "property"
        assert len(unresolved) == 0

    def test_resolve_function_call_names(self):
        """Test resolving call names in functions."""
        imports = [models.ImportInfo(module="pandas", names=["pandas"], alias="pd")]

        func = models.FunctionInfo(
            name="process",
            is_public=True,
            calls=[
                models.CallInfo(
                    name="DataFrame",
                    call_type=models.CallType.ATTRIBUTE,
                    full_name="pd.DataFrame",
                    qualifier="pd",
                )
            ],
        )

        result = models.ExtractionResult(
            module=models.ModuleInfo(path="test.py", name="test"),
            imports=imports,
            functions=[func],
        )

        resolver = name_resolver.NameResolver(imports, "test")
        resolved_result, unresolved = resolver.resolve_extraction_result(result)

        # Call name should be resolved
        assert resolved_result.functions[0].calls[0].full_name == "pandas.DataFrame"
        assert len(unresolved) == 0

    def test_resolve_method_call_names(self):
        """Test resolving call names in methods."""
        imports = [models.ImportInfo(module="typing", names=["List"])]

        method = models.FunctionInfo(
            name="get_items",
            is_public=True,
            calls=[
                models.CallInfo(
                    name="List",
                    call_type=models.CallType.SIMPLE,
                    full_name="List",
                    qualifier=None,
                )
            ],
        )

        cls = models.ClassInfo(
            name="Container",
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

        # Method call should be resolved
        assert resolved_result.classes[0].methods[0].calls[0].full_name == "typing.List"
        assert len(unresolved) == 0

    def test_collect_unresolved_names(self):
        """Test that unresolved names are collected."""
        imports = []  # No imports

        func = models.FunctionInfo(
            name="process",
            is_public=True,
            decorators=[
                models.DecoratorInfo(
                    name="unknown_decorator", args=None, full_text="@unknown_decorator"
                )
            ],
            calls=[
                models.CallInfo(
                    name="unknown_func",
                    call_type=models.CallType.SIMPLE,
                    full_name="unknown_func",
                    qualifier=None,
                )
            ],
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

        # Should have 2 unresolved names (call, base class)
        # Decorator name resolution is currently disabled, so decorator not tracked as unresolved
        assert len(unresolved) == 2
        unresolved_names = [u.original_name for u in unresolved]
        assert "unknown_func" in unresolved_names
        assert "UnknownBase" in unresolved_names
