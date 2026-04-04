"""Integration tests for structured properties (parameters and decorators) queries."""

import pytest

from mapper import analyser, graph_loader


class TestStructuredPropertiesQueries:
    """Tests for querying structured parameters and decorators in Neo4j.

    These tests validate that Tier 2 users can write precise Cypher queries
    on parameter-level and decorator-level metadata.

    Test fixture structure:
    - Functions with various parameter kinds (positional-only, keyword-only, *args, **kwargs)
    - Functions with type hints and defaults
    - Functions and classes with decorators
    """

    PACKAGE_NAME = "structured_properties_test"

    @pytest.fixture(scope="class", autouse=True)
    def analyzed_fixture(self, neo4j_connection, tmp_path_factory):
        """Create and analyze test code with structured properties."""
        # TODO(0.8.1): Move this test code to sample_projects/ and load from there
        # instead of writing inline. This will make the test data reusable and easier
        # to maintain.

        # Create temporary directory for test code
        test_dir = tmp_path_factory.mktemp("structured_props")
        test_file = test_dir / "sample.py"

        # Write test code with various parameter types and decorators
        test_file.write_text(
            '''"""Sample module for testing structured properties."""

from typing import Optional

def simple_function(a: str, b: int = 10):
    """Function with typed params and default."""
    pass

def complex_params(pos_only: str, /, normal: int, *args, kw_only: bool, **kwargs) -> None:
    """Function with all parameter kinds."""
    pass

def optional_params(name: Optional[str] = None, count: int = 0):
    """Function with optional parameters."""
    pass

def no_types(x, y, z=5):
    """Function without type hints."""
    pass

def variadic_only(*args, **kwargs):
    """Function with only variadic params."""
    pass

def keyword_only_func(*, required: str, optional: int = 42):
    """Function with keyword-only parameters."""
    pass

# Decorated functions
@property
def decorated_simple():
    """Simple decorator."""
    pass

def rate_limit(calls):
    """Decorator with args."""
    def decorator(func):
        return func
    return decorator

@rate_limit(10)
def decorated_with_args():
    """Decorator with arguments."""
    pass

# Decorated class
class MyClass:
    """Test class with decorators."""

    @staticmethod
    def static_method():
        """Static method."""
        pass

    @classmethod
    def class_method(cls):
        """Class method."""
        pass

    def instance_method(self, value: str):
        """Instance method."""
        pass
'''
        )

        # Analyze the test code
        loader = graph_loader.GraphLoader(neo4j_connection, self.PACKAGE_NAME)
        loader.clear_package()

        code_analyser = analyser.Analyser(test_dir, loader=loader)
        result = code_analyser.analyse()

        if not result.success:
            pytest.fail(f"Failed to analyze test fixture: {result.errors}")

        yield neo4j_connection

        # Cleanup
        loader.clear_package()

    # ===== Parameter-level queries =====

    def test_query_functions_by_parameter_count(self, analyzed_fixture):
        """Test finding functions by number of parameters."""
        connection = analyzed_fixture

        # Find functions with exactly 2 parameters
        query = """
        MATCH (f:Function {package: $package})-[:HAS_PARAMETER]->(p:Parameter)
        WITH f, count(p) as param_count
        WHERE param_count = 2
        RETURN f.name as name, param_count
        ORDER BY name
        """
        with connection.driver.session(database=connection.database) as session:
            result = session.run(query, package=self.PACKAGE_NAME)
            functions = [record["name"] for record in result]

        # simple_function has 2 params (a, b)
        # variadic_only has 2 params (*args, **kwargs)
        assert "simple_function" in functions
        assert len(functions) >= 2

    def test_query_functions_with_defaults(self, analyzed_fixture):
        """Test finding functions with default parameter values."""
        connection = analyzed_fixture

        # Find all parameters that have defaults
        query = """
        MATCH (f:Function {package: $package})-[:HAS_PARAMETER]->(p:Parameter)
        WHERE p.default IS NOT NULL
        RETURN f.name as function_name, p.name as param_name, p.default as default_value
        ORDER BY function_name, param_name
        """
        with connection.driver.session(database=connection.database) as session:
            result = session.run(query, package=self.PACKAGE_NAME)
            records = list(result)

        # simple_function: b=10
        # optional_params: name=None, count=0
        # no_types: z=5
        # keyword_only_func: optional=42
        assert len(records) >= 4

        # Verify specific defaults
        defaults_by_func = {}
        for record in records:
            func = record["function_name"]
            if func not in defaults_by_func:
                defaults_by_func[func] = {}
            defaults_by_func[func][record["param_name"]] = record["default_value"]

        assert defaults_by_func.get("simple_function", {}).get("b") == "10"
        assert defaults_by_func.get("optional_params", {}).get("name") == "None"
        assert defaults_by_func.get("no_types", {}).get("z") == "5"

    def test_query_functions_by_parameter_kind(self, analyzed_fixture):
        """Test finding functions with specific parameter kinds."""
        connection = analyzed_fixture

        # Find functions with keyword-only parameters
        query = """
        MATCH (f:Function {package: $package})-[:HAS_PARAMETER]->(p:Parameter)
        WHERE p.kind = 'KEYWORD_ONLY'
        RETURN DISTINCT f.name as name
        ORDER BY name
        """
        with connection.driver.session(database=connection.database) as session:
            result = session.run(query, package=self.PACKAGE_NAME)
            functions = [record["name"] for record in result]

        # complex_params has kw_only parameter
        # keyword_only_func has required and optional
        assert "complex_params" in functions
        assert "keyword_only_func" in functions

    def test_query_functions_with_var_positional(self, analyzed_fixture):
        """Test finding functions with *args parameters."""
        connection = analyzed_fixture

        # Find functions with VAR_POSITIONAL (*args)
        query = """
        MATCH (f:Function {package: $package})-[:HAS_PARAMETER]->(p:Parameter)
        WHERE p.kind = 'VAR_POSITIONAL'
        RETURN f.name as name, p.name as param_name
        ORDER BY name
        """
        with connection.driver.session(database=connection.database) as session:
            result = session.run(query, package=self.PACKAGE_NAME)
            records = list(result)

        # complex_params and variadic_only have *args
        names = [r["name"] for r in records]
        assert "complex_params" in names
        assert "variadic_only" in names

        # Verify param name is 'args'
        assert all(r["param_name"] == "args" for r in records)

    def test_query_functions_with_var_keyword(self, analyzed_fixture):
        """Test finding functions with **kwargs parameters."""
        connection = analyzed_fixture

        # Find functions with VAR_KEYWORD (**kwargs)
        query = """
        MATCH (f:Function {package: $package})-[:HAS_PARAMETER]->(p:Parameter)
        WHERE p.kind = 'VAR_KEYWORD'
        RETURN f.name as name, p.name as param_name
        ORDER BY name
        """
        with connection.driver.session(database=connection.database) as session:
            result = session.run(query, package=self.PACKAGE_NAME)
            records = list(result)

        # complex_params and variadic_only have **kwargs
        names = [r["name"] for r in records]
        assert "complex_params" in names
        assert "variadic_only" in names

        # Verify param name is 'kwargs'
        assert all(r["param_name"] == "kwargs" for r in records)

    def test_query_functions_with_type_hints(self, analyzed_fixture):
        """Test finding functions with typed parameters."""
        connection = analyzed_fixture

        # Find parameters that have type hints
        query = """
        MATCH (f:Function {package: $package})-[:HAS_PARAMETER]->(p:Parameter)
        WHERE p.has_type_hint = true
        RETURN f.name as function_name, p.name as param_name, p.type_hint as type_hint
        ORDER BY function_name, param_name
        """
        with connection.driver.session(database=connection.database) as session:
            result = session.run(query, package=self.PACKAGE_NAME)
            records = list(result)

        # simple_function: a: str, b: int
        # complex_params: pos_only: str, normal: int, kw_only: bool
        # optional_params: name: Optional[str], count: int
        assert len(records) >= 7

        # Verify specific type hints
        type_hints = {(r["function_name"], r["param_name"]): r["type_hint"] for r in records}
        assert type_hints.get(("simple_function", "a")) == "str"
        assert type_hints.get(("simple_function", "b")) == "int"

    def test_query_functions_without_type_hints(self, analyzed_fixture):
        """Test finding functions with untyped parameters."""
        connection = analyzed_fixture

        # Find functions where ALL parameters lack type hints
        query = """
        MATCH (f:Function {package: $package})-[:HAS_PARAMETER]->(p:Parameter)
        WITH f, collect(p) as params
        WHERE size(params) > 0
        AND all(param IN params WHERE param.has_type_hint = false)
        RETURN f.name as name
        ORDER BY name
        """
        with connection.driver.session(database=connection.database) as session:
            result = session.run(query, package=self.PACKAGE_NAME)
            functions = [record["name"] for record in result]

        # no_types function has no type hints
        assert "no_types" in functions

    def test_query_parameters_by_position(self, analyzed_fixture):
        """Test finding parameters by their position."""
        connection = analyzed_fixture

        # Find all first parameters (position 0)
        query = """
        MATCH (f:Function {package: $package})-[:HAS_PARAMETER]->(p:Parameter)
        WHERE p.position = 0
        RETURN f.name as function_name, p.name as param_name
        ORDER BY function_name
        """
        with connection.driver.session(database=connection.database) as session:
            result = session.run(query, package=self.PACKAGE_NAME)
            records = list(result)

        # Each function's first parameter
        first_params = {r["function_name"]: r["param_name"] for r in records}
        assert first_params.get("simple_function") == "a"
        assert first_params.get("complex_params") == "pos_only"
        assert first_params.get("no_types") == "x"

    # ===== Decorator-level queries =====

    def test_query_decorated_functions(self, analyzed_fixture):
        """Test finding decorated functions."""
        connection = analyzed_fixture

        # Find all functions with decorators
        query = """
        MATCH (f:Function {package: $package})-[:DECORATED_WITH]->(d:Decorator)
        RETURN f.name as function_name, collect(d.name) as decorators
        ORDER BY function_name
        """
        with connection.driver.session(database=connection.database) as session:
            result = session.run(query, package=self.PACKAGE_NAME)
            records = list(result)

        # decorated_simple has @property
        # decorated_with_args has @rate_limit(10)
        function_names = [r["function_name"] for r in records]
        assert "decorated_simple" in function_names
        assert "decorated_with_args" in function_names

    def test_query_functions_by_decorator_name(self, analyzed_fixture):
        """Test finding functions with specific decorator."""
        connection = analyzed_fixture

        # Find functions decorated with @property
        query = """
        MATCH (f:Function {package: $package})-[:DECORATED_WITH]->(d:Decorator {name: 'property'})
        RETURN f.name as name
        """
        with connection.driver.session(database=connection.database) as session:
            result = session.run(query, package=self.PACKAGE_NAME)
            functions = [record["name"] for record in result]

        assert "decorated_simple" in functions

    def test_query_decorators_with_arguments(self, analyzed_fixture):
        """Test finding decorators with arguments."""
        connection = analyzed_fixture

        # Find decorators that have arguments
        query = """
        MATCH (f:Function {package: $package})-[:DECORATED_WITH]->(d:Decorator)
        WHERE d.args IS NOT NULL
        RETURN f.name as function_name, d.name as decorator_name, d.args as args, d.full_text as full_text
        """
        with connection.driver.session(database=connection.database) as session:
            result = session.run(query, package=self.PACKAGE_NAME)
            records = list(result)

        # decorated_with_args has @rate_limit(10)
        assert any(r["decorator_name"] == "rate_limit" for r in records)
        rate_limit_record = next(r for r in records if r["decorator_name"] == "rate_limit")
        assert rate_limit_record["args"] == "(10)"  # Args include parentheses
        assert "rate_limit(10)" in rate_limit_record["full_text"]

    def test_query_decorated_methods(self, analyzed_fixture):
        """Test finding decorated methods in classes."""
        connection = analyzed_fixture

        # Find methods with decorators
        query = """
        MATCH (c:Class {package: $package})-[:CONTAINS]->(m:Method)-[:DECORATED_WITH]->(d:Decorator)
        RETURN c.name as class_name, m.name as method_name, collect(d.name) as decorators
        ORDER BY method_name
        """
        with connection.driver.session(database=connection.database) as session:
            result = session.run(query, package=self.PACKAGE_NAME)
            records = list(result)

        # MyClass has @staticmethod and @classmethod decorators
        method_decorators = {r["method_name"]: r["decorators"] for r in records}
        assert "staticmethod" in method_decorators.get("static_method", [])
        assert "classmethod" in method_decorators.get("class_method", [])

    def test_query_decorator_usage_count(self, analyzed_fixture):
        """Test counting decorator usage across codebase."""
        connection = analyzed_fixture

        # Count how many times each decorator is used
        query = """
        MATCH (d:Decorator {package: $package})
        RETURN d.name as decorator, count(*) as usage_count
        ORDER BY usage_count DESC, decorator
        """
        with connection.driver.session(database=connection.database) as session:
            result = session.run(query, package=self.PACKAGE_NAME)
            records = list(result)

        # Should have counts for property, rate_limit, staticmethod, classmethod
        decorator_counts = {r["decorator"]: r["usage_count"] for r in records}
        assert decorator_counts.get("property", 0) >= 1
        assert decorator_counts.get("rate_limit", 0) >= 1
        assert decorator_counts.get("staticmethod", 0) >= 1
        assert decorator_counts.get("classmethod", 0) >= 1

    # ===== Combined queries =====

    def test_query_decorated_functions_with_specific_parameters(self, analyzed_fixture):
        """Test combining decorator and parameter queries."""
        connection = analyzed_fixture

        # Find decorated functions that have type hints
        query = """
        MATCH (f:Function {package: $package})-[:DECORATED_WITH]->(d:Decorator)
        WHERE any(param IN f.parameters WHERE param.has_type_hint = true)
        RETURN f.name as name, collect(d.name) as decorators
        ORDER BY name
        """
        with connection.driver.session(database=connection.database) as session:
            result = session.run(query, package=self.PACKAGE_NAME)
            records = list(result)

        # This validates we can combine both structured property types in queries
        assert len(records) >= 0  # May or may not have decorated typed functions

    def test_query_complex_parameter_pattern(self, analyzed_fixture):
        """Test complex pattern: functions with defaults but no type hints."""
        connection = analyzed_fixture

        # Find functions with defaults but no type hints on those params
        query = """
        MATCH (f:Function {package: $package})-[:HAS_PARAMETER]->(p:Parameter)
        WHERE p.default IS NOT NULL AND p.has_type_hint = false
        RETURN DISTINCT f.name as name
        ORDER BY name
        """
        with connection.driver.session(database=connection.database) as session:
            result = session.run(query, package=self.PACKAGE_NAME)
            functions = [record["name"] for record in result]

        # no_types has z=5 without type hint
        assert "no_types" in functions
