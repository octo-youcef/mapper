# Python API Reference

Public Python API for using Mapper programmatically.

## Status

**This API is under development and subject to change.**

Current focus is on the CLI interface. Programmatic Python API will be documented here as it stabilizes.

## Planned Public API

### Core Modules

```python
import mapper

# Version
print(mapper.__version__)

# Parser
parser = mapper.ASTParser()
ast_tree = parser.parse_file(Path("example.py"))

# Graph connection
connection = mapper.Neo4jConnection(
    uri="bolt://localhost:7687",
    user="neo4j",
    password="password"
)
connection.test_connection()
connection.close()
```

### Submodules

```python
# AST Parser
from mapper import ast_parser
extractor = ast_parser.ASTExtractor()
info = extractor.extract(ast_tree)

# Configuration Manager
from mapper import config_manager
config = config_manager.load_config()
credentials = config_manager.get_neo4j_credentials()

# Status Checker
from mapper import status_checker
checker = status_checker.StatusChecker()
status = checker.check_status(detailed=True)

# Type Inference
from mapper import type_inference
inferrer = type_inference.TypeInferrer()
inferred_type = inferrer.infer_type(node)
```

## Notes

- Import modules rather than individual classes: `from mapper import parser` not `from mapper.parser import ASTParser`
- This ensures clear namespace and consistent usage patterns
- Full API documentation will be added as the API stabilizes

---

**Last Updated**: 2026-03-24
