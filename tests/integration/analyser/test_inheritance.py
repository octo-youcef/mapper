"""Integration tests for class inheritance across modules in Neo4j."""

from pathlib import Path

import pytest

from mapper import analyser, graph_loader


class TestInheritance:
    """Tests for class inheritance tracking.

    All tests use the inheritance fixture analyzed once in setup_class.
    """

    PACKAGE_NAME = "inheritance"

    @pytest.fixture(scope="class", autouse=True)
    def analyzed_inheritance_fixture(self, neo4j_connection):
        """Analyze inheritance fixture once for all tests in this class."""
        fixture_path = Path(__file__).parent.parent.parent / "fixtures/sample_projects/inheritance"

        loader = graph_loader.GraphLoader(neo4j_connection, self.PACKAGE_NAME)
        loader.clear_package()

        code_analyser = analyser.Analyser(fixture_path, loader=loader)
        result = code_analyser.analyse()

        if not result.success:
            pytest.fail(f"Failed to analyze inheritance fixture: {result.errors}")

        yield neo4j_connection

        # Cleanup after all tests
        loader.clear_package()

    def test_single_inheritance(self, analyzed_inheritance_fixture):
        """Test simple single inheritance relationship (Animal -> Dog/Cat)."""
        connection = analyzed_inheritance_fixture

        with connection.driver.session(database=connection.database) as session:
            # Verify Dog inherits from Animal
            dog_inherits = session.run(
                """
                MATCH (dog:Class {package: $pkg, name: 'Dog'})-[:INHERITS]->(animal:Class {name: 'Animal'})
                RETURN dog.fqn as dog, animal.fqn as animal
                """,
                pkg=self.PACKAGE_NAME,
            ).data()

            assert len(dog_inherits) == 1
            assert dog_inherits[0]["dog"] == "derived.Dog"
            assert dog_inherits[0]["animal"] == "base.Animal"

            # Verify Cat also inherits from Animal
            cat_inherits = session.run(
                """
                MATCH (cat:Class {package: $pkg, name: 'Cat'})-[:INHERITS]->(animal:Class {name: 'Animal'})
                RETURN cat.fqn as cat
                """,
                pkg=self.PACKAGE_NAME,
            ).data()

            assert len(cat_inherits) == 1
            assert cat_inherits[0]["cat"] == "derived.Cat"

    def test_inheritance_chain(self, analyzed_inheritance_fixture):
        """Test inheritance chain GrandParent -> Parent -> Child."""
        connection = analyzed_inheritance_fixture

        with connection.driver.session(database=connection.database) as session:
            # Verify chain relationships exist
            inherits = session.run(
                """
                MATCH (child:Class {package: $pkg})-[:INHERITS]->(parent:Class)
                WHERE child.name IN ['Child', 'Parent'] AND parent.name IN ['Parent', 'GrandParent']
                RETURN child.name as child, parent.name as parent
                ORDER BY child
                """,
                pkg=self.PACKAGE_NAME,
            ).data()

            assert len(inherits) == 2
            # Child -> Parent
            assert inherits[0]["child"] == "Child"
            assert inherits[0]["parent"] == "Parent"
            # Parent -> GrandParent
            assert inherits[1]["child"] == "Parent"
            assert inherits[1]["parent"] == "GrandParent"

    def test_cross_module_inheritance(self, analyzed_inheritance_fixture):
        """Test inheritance where base and derived are in different modules."""
        connection = analyzed_inheritance_fixture

        with connection.driver.session(database=connection.database) as session:
            # Verify cross-module inheritance (derived.Dog -> base.Animal)
            inherits = session.run(
                """
                MATCH (m1:Module)-[:DEFINES]->(dog:Class {name: 'Dog'})-[:INHERITS]->(animal:Class {name: 'Animal'})<-[:DEFINES]-(m2:Module)
                WHERE m1.name <> m2.name
                RETURN dog.fqn as dog_fqn, animal.fqn as animal_fqn, m1.name as dog_module, m2.name as animal_module
                """,
            ).data()

            assert len(inherits) == 1
            assert inherits[0]["dog_fqn"] == "derived.Dog"
            assert inherits[0]["animal_fqn"] == "base.Animal"
            assert inherits[0]["dog_module"] == "derived"
            assert inherits[0]["animal_module"] == "base"

    def test_multiple_inheritance(self, analyzed_inheritance_fixture):
        """Test class inheriting from multiple base classes."""
        connection = analyzed_inheritance_fixture

        with connection.driver.session(database=connection.database) as session:
            # Verify Combined inherits from both Mixin1 and Mixin2
            inherits = session.run(
                """
                MATCH (combined:Class {package: $pkg, name: 'Combined'})-[:INHERITS]->(base:Class)
                RETURN base.name as base_name
                ORDER BY base_name
                """,
                pkg=self.PACKAGE_NAME,
            ).data()

            assert len(inherits) == 2
            assert inherits[0]["base_name"] == "Mixin1"
            assert inherits[1]["base_name"] == "Mixin2"

    def test_inheritance_with_methods(self, analyzed_inheritance_fixture):
        """Test that inherited methods are tracked correctly."""
        connection = analyzed_inheritance_fixture

        with connection.driver.session(database=connection.database) as session:
            # Verify Dog class has methods
            dog_methods = session.run(
                """
                MATCH (dog:Class {package: $pkg, name: 'Dog'})-[:CONTAINS]->(m:Method)
                RETURN m.name as method_name
                ORDER BY method_name
                """,
                pkg=self.PACKAGE_NAME,
            ).data()

            # Dog has speak() and fetch()
            assert len(dog_methods) == 2
            method_names = [m["method_name"] for m in dog_methods]
            assert "speak" in method_names
            assert "fetch" in method_names

            # Verify Animal class has methods
            animal_methods = session.run(
                """
                MATCH (animal:Class {package: $pkg, name: 'Animal'})-[:CONTAINS]->(m:Method)
                RETURN m.name as method_name
                """,
                pkg=self.PACKAGE_NAME,
            ).data()

            # Animal has __init__ and speak()
            assert len(animal_methods) >= 1
            method_names = [m["method_name"] for m in animal_methods]
            assert "speak" in method_names

    def test_inheritance_diamond_pattern(self, analyzed_inheritance_fixture):
        """Test diamond inheritance pattern (A <- B, A <- C, B <- D, C <- D)."""
        connection = analyzed_inheritance_fixture

        with connection.driver.session(database=connection.database) as session:
            # Verify all diamond relationships
            inherits = session.run(
                """
                MATCH (child:Class {package: $pkg})-[:INHERITS]->(parent:Class)
                WHERE child.name IN ['B', 'C', 'D'] AND parent.name IN ['A', 'B', 'C']
                RETURN child.name as child, parent.name as parent
                ORDER BY child, parent
                """,
                pkg=self.PACKAGE_NAME,
            ).data()

            # B->A, C->A, D->B, D->C
            assert len(inherits) == 4

            # Check specific relationships
            b_to_a = any(i["child"] == "B" and i["parent"] == "A" for i in inherits)
            c_to_a = any(i["child"] == "C" and i["parent"] == "A" for i in inherits)
            d_to_b = any(i["child"] == "D" and i["parent"] == "B" for i in inherits)
            d_to_c = any(i["child"] == "D" and i["parent"] == "C" for i in inherits)

            assert b_to_a
            assert c_to_a
            assert d_to_b
            assert d_to_c
