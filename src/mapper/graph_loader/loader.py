"""Graph loader implementation."""

from mapper import ast_parser, graph


class GraphLoader:
    """Loads analysis results into Neo4j graph database."""

    def __init__(self, connection: graph.Neo4jConnection, package_name: str):
        """Initialize graph loader.

        Args:
            connection: Neo4j connection
            package_name: Name of the package being analyzed
        """
        self.connection = connection
        self.package_name = package_name
        self._node_ids: dict[str, str] = {}  # Track created nodes for relationships
        self._deferred_relationships: list[tuple] = []  # Relationships to create later

    def clear_package(self) -> int:
        """Clear all nodes for this package from the graph.

        Returns:
            Number of nodes deleted
        """
        with self.connection.driver.session(database=self.connection.database) as session:
            result = session.run(
                """
                MATCH (n {package: $package})
                DETACH DELETE n
                RETURN count(n) as deleted
                """,
                package=self.package_name,
            )
            record = result.single()
            return record["deleted"] if record else 0

    def load_extraction(self, extraction: ast_parser.models.ExtractionResult) -> None:
        """Load extraction result into graph.

        Args:
            extraction: AST extraction result to load
        """
        module_name = extraction.module.name

        # Create module node
        module_node_id = self._create_module_node(extraction.module)

        # Create class nodes and methods
        for class_info in extraction.classes:
            class_fqn = f"{module_name}.{class_info.name}"
            class_node_id = self._create_class_node(class_info, class_fqn)
            # DEFINES relationship: Module defines Class
            self.connection.create_relationship(module_node_id, class_node_id, "DEFINES")

            # Create methods within class
            for method in class_info.methods:
                method_fqn = f"{class_fqn}.{method.name}"
                method_node_id = self._create_function_node(method, method_fqn, is_method=True)
                # CONTAINS relationship: Class contains Method
                self.connection.create_relationship(class_node_id, method_node_id, "CONTAINS")

                # Track method calls for later
                for call in method.calls:
                    call_name = call.name if hasattr(call, "name") else call
                    self._deferred_relationships.append(("calls", method_fqn, call_name))

            # Track inheritance for later
            for base in class_info.bases:
                self._deferred_relationships.append(("inherits", class_fqn, base))

        # Create function nodes
        for func_info in extraction.functions:
            func_fqn = f"{module_name}.{func_info.name}"
            func_node_id = self._create_function_node(func_info, func_fqn)
            # DEFINES relationship: Module defines Function
            self.connection.create_relationship(module_node_id, func_node_id, "DEFINES")

            # Track function calls for later
            for call in func_info.calls:
                # Extract call name from CallInfo object (temporary - will be enhanced in Patch 2)
                call_name = call.name if hasattr(call, "name") else call
                self._deferred_relationships.append(("calls", func_fqn, call_name))

        # Handle imports
        for import_info in extraction.imports:
            # Track imports for later relationship creation
            self._deferred_relationships.append(("imports", module_name, import_info.module))

    def finalize(self) -> None:
        """Finalize loading by creating deferred relationships.

        Call this after all extractions have been loaded to create
        relationships between nodes that may have been created in different files.
        """
        for rel_type, from_fqn, to_name in self._deferred_relationships:
            from_id = self._node_ids.get(from_fqn)
            if not from_id:
                continue  # Source node not found

            # Try to resolve target by FQN first, then by simple name
            to_id = self._node_ids.get(to_name)
            if not to_id:
                # Try finding by simple name (last component of FQN)
                to_id = self._find_node_by_simple_name(to_name)

            if to_id:
                if rel_type == "inherits":
                    self.connection.create_relationship(from_id, to_id, "INHERITS")
                elif rel_type == "calls":
                    self.connection.create_relationship(from_id, to_id, "CALLS")
                elif rel_type == "imports":
                    self.connection.create_relationship(from_id, to_id, "IMPORTS")

    def _find_node_by_simple_name(self, simple_name: str) -> str | None:
        """Find a node by its simple name (last component of FQN).

        Args:
            simple_name: Simple name to search for

        Returns:
            Node ID if found, None otherwise
        """
        for fqn, node_id in self._node_ids.items():
            # Check if this FQN ends with the simple name
            if fqn.endswith(f".{simple_name}") or fqn == simple_name:
                return node_id
        return None

    def _create_module_node(self, module: ast_parser.models.ModuleInfo) -> str:
        """Create a Module node.

        Args:
            module: Module information

        Returns:
            Node ID for created module
        """
        fqn = module.name
        properties = {
            "name": module.name,
            "fqn": fqn,
            "path": module.path,
            "package": self.package_name,
        }
        if module.docstring:
            properties["docstring"] = module.docstring

        node_id = self.connection.create_node("Module", properties)
        self._node_ids[fqn] = node_id
        return node_id

    def _create_class_node(self, class_info: ast_parser.models.ClassInfo, fqn: str) -> str:
        """Create a Class node.

        Args:
            class_info: Class information
            fqn: Fully qualified name (module.ClassName)

        Returns:
            Node ID for created class
        """
        properties = {
            "name": class_info.name,
            "fqn": fqn,
            "package": self.package_name,
            "is_public": class_info.is_public,
        }
        if class_info.docstring:
            properties["docstring"] = class_info.docstring
        if class_info.bases:
            properties["bases"] = str(class_info.bases)  # Serialize for now

        node_id = self.connection.create_node("Class", properties)
        self._node_ids[fqn] = node_id
        return node_id

    def _create_function_node(
        self, func_info: ast_parser.models.FunctionInfo, fqn: str, is_method: bool = False
    ) -> str:
        """Create a Function or Method node.

        Args:
            func_info: Function information
            fqn: Fully qualified name (module.function_name or module.Class.method_name)
            is_method: Whether this is a method (vs standalone function)

        Returns:
            Node ID for created function
        """
        label = "Method" if is_method else "Function"
        properties = {
            "name": func_info.name,
            "fqn": fqn,
            "package": self.package_name,
            "is_public": func_info.is_public,
        }
        if func_info.docstring:
            properties["docstring"] = func_info.docstring
        if func_info.return_type:
            properties["return_type"] = func_info.return_type
        if func_info.parameters:
            properties["parameters"] = str(func_info.parameters)  # Serialize for now
        if func_info.decorators:
            properties["decorators"] = str(func_info.decorators)  # Serialize for now

        node_id = self.connection.create_node(label, properties)
        self._node_ids[fqn] = node_id
        return node_id
