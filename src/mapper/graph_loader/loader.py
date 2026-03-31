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
        self._module_dependencies: set[tuple[str, str]] = (
            set()
        )  # Track (from_module, to_module) pairs for DEPENDS_ON

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
                    # Use full_name which contains the resolved FQN
                    call_name = call.full_name if hasattr(call, "full_name") else call
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
                # Use full_name which contains the resolved FQN
                call_name = call.full_name if hasattr(call, "full_name") else call
                self._deferred_relationships.append(("calls", func_fqn, call_name))

        # Handle imports - create Import nodes
        for import_info in extraction.imports:
            self._create_import_nodes(import_info, module_node_id, module_name)

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
                match rel_type:
                    case "inherits":
                        self.connection.create_relationship(from_id, to_id, "INHERITS")
                    case "calls":
                        self.connection.create_relationship(from_id, to_id, "CALLS")
                    case "imports":
                        self.connection.create_relationship(from_id, to_id, "IMPORTS")
                    case "from_module":
                        self.connection.create_relationship(from_id, to_id, "FROM_MODULE")
                    case "depends_on":
                        self.connection.create_relationship(from_id, to_id, "DEPENDS_ON")
            elif rel_type in ("from_module", "depends_on"):
                # External module doesn't exist in graph yet - create External Module node
                external_node_id = self.connection.create_node(
                    "Module", {"name": to_name, "package": to_name, "is_external": True}
                )
                self._node_ids[to_name] = external_node_id
                match rel_type:
                    case "from_module":
                        self.connection.create_relationship(
                            from_id, external_node_id, "FROM_MODULE"
                        )
                    case "depends_on":
                        self.connection.create_relationship(from_id, external_node_id, "DEPENDS_ON")

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

    def _create_single_import_node(
        self,
        module_node_id: str,
        from_module: str,
        submodule_path: str | None,
        local_name: str,
        importing_module_name: str,
    ) -> str:
        """Create a single Import node.

        Args:
            module_node_id: ID of the importing module node
            from_module: Base module being imported
            submodule_path: Submodule path if any
            local_name: Local name (with alias if present)
            importing_module_name: FQN of importing module

        Returns:
            Node ID of created Import node
        """
        properties = {
            "from_module": from_module,
            "local_name": local_name,
            "package": self.package_name,
        }
        if submodule_path:
            properties["submodule_path"] = submodule_path

        import_node_id = self.connection.create_node("Import", properties)

        # Create Module -[IMPORTS]-> Import relationship
        self.connection.create_relationship(module_node_id, import_node_id, "IMPORTS")

        # Track deferred FROM_MODULE relationship to external module
        # Build full module path for the external module
        external_module = f"{from_module}.{submodule_path}" if submodule_path else from_module
        self._deferred_relationships.append(("from_module", import_node_id, external_module))

        # Track deferred DEPENDS_ON relationship (Module -> Module shortcut)
        # Use set to deduplicate - only one DEPENDS_ON per module pair
        dependency_pair = (importing_module_name, external_module)
        if dependency_pair not in self._module_dependencies:
            self._module_dependencies.add(dependency_pair)
            self._deferred_relationships.append(
                ("depends_on", importing_module_name, external_module)
            )

        return import_node_id

    def _create_import_nodes(self, import_info, module_node_id: str, module_name: str) -> None:
        """Create Import nodes for an import statement.

        Args:
            import_info: ImportInfo with import details
            module_node_id: ID of the importing module node
            module_name: FQN of the importing module
        """
        # Parse module path into from_module and submodule_path
        module_parts = import_info.module.split(".")
        from_module = module_parts[0]
        submodule_path = ".".join(module_parts[1:]) if len(module_parts) > 1 else None

        # Handle different import patterns
        if import_info.alias:
            # import X as Y or import X.Y as Z
            self._create_single_import_node(
                module_node_id, from_module, submodule_path, import_info.alias, module_name
            )
        elif import_info.module in import_info.names:
            # import X (where X is in names list)
            # Use the top-level module name as local_name
            self._create_single_import_node(
                module_node_id, from_module, submodule_path, from_module, module_name
            )
        else:
            # from X import Y, Z (possibly with aliases)
            for name in import_info.names:
                local_name = import_info.aliases.get(name, name)
                self._create_single_import_node(
                    module_node_id, from_module, submodule_path, local_name, module_name
                )
