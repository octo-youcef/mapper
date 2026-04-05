# Interface Design: Quality Rules

**Version**: 0.8.1  
**Status**: Design  
**Related**: [User Journey: Running Quality Rules](../user-journeys/10-quality-rules.md)

---

## Overview

Quality rules provide built-in pass/fail checks for code quality standards. This interface defines the CLI commands, configuration schema, output formats, and quality rule specifications.

**Key Design Principles**:
- **Separate entrypoint**: `mapper quality` is distinct from `mapper query` due to different semantics
- **Pass/fail semantics**: Rules return pass/fail status, not severity rankings
- **Exit codes**: Exit 1 if any rule fails, 0 if all pass (for CI/CD)
- **Package-level enforcement**: Thresholds apply to overall package, not individual files
- **Configurable thresholds**: User-defined thresholds in `mapper.toml`
- **Multiple output formats**: Console (human-readable), JSON (CI/CD), CSV (tracking)

---

## CLI Commands

### `mapper quality check`

Run all enabled quality checks.

**Signature**:
```bash
mapper quality check [OPTIONS]
```

**Options**:
- `--format FORMAT`: Output format (console, json, csv). Default: console
- `--json`: Shortcut for `--format json`
- `--csv`: Shortcut for `--format csv`

**Exit Codes**:
- `0`: All enabled checks passed
- `1`: One or more checks failed

**Behavior**:
- Reads configuration from `mapper.toml`
- Runs all quality rules where `enabled = true`
- Returns per-rule results (not aggregated)
- If no configuration exists, uses default thresholds with all rules enabled

---

### `mapper quality type-coverage`

Check type hint coverage on public functions and methods.

**Signature**:
```bash
mapper quality type-coverage [OPTIONS]
```

**Options**:
- `--format FORMAT`: Output format (console, json, csv). Default: console
- `--json`: Shortcut for `--format json`
- `--csv`: Shortcut for `--format csv`

**Exit Codes**:
- `0`: Type coverage meets or exceeds threshold
- `1`: Type coverage below threshold

---

### `mapper quality docstring-coverage`

Check docstring coverage on public functions and methods.

**Signature**:
```bash
mapper quality docstring-coverage [OPTIONS]
```

**Options**:
- `--format FORMAT`: Output format (console, json, csv). Default: console
- `--json`: Shortcut for `--format json`
- `--csv`: Shortcut for `--format csv`

**Exit Codes**:
- `0`: Docstring coverage meets or exceeds threshold
- `1`: Docstring coverage below threshold

---

### `mapper quality param-complexity`

Check function parameter complexity.

**Signature**:
```bash
mapper quality param-complexity [OPTIONS]
```

**Options**:
- `--format FORMAT`: Output format (console, json, csv). Default: console
- `--json`: Shortcut for `--format json`
- `--csv`: Shortcut for `--format csv`

**Exit Codes**:
- `0`: No functions exceed parameter threshold
- `1`: One or more functions exceed parameter threshold

---

## Configuration Schema

Quality rules are configured in `mapper.toml` under `[quality.*]` sections.

### Type Coverage Configuration

```toml
[quality.type_coverage]
enabled = true                    # Enable/disable rule
min_coverage = 80                 # Minimum percentage (0-100)
require_return_types = true       # Require return type hints
exclude_patterns = ["test_*", "__init__"]  # Exclude functions matching patterns
```

**Defaults** (if section not present):
- `enabled = true`
- `min_coverage = 80`
- `require_return_types = false`
- `exclude_patterns = []`

---

### Docstring Coverage Configuration

```toml
[quality.docstring_coverage]
enabled = true                    # Enable/disable rule
min_coverage = 90                 # Minimum percentage (0-100)
exclude_patterns = ["__str__", "__repr__", "__init__"]  # Exclude functions
```

**Defaults** (if section not present):
- `enabled = true`
- `min_coverage = 90`
- `exclude_patterns = []`

---

### Parameter Complexity Configuration

```toml
[quality.param_complexity]
enabled = true                    # Enable/disable rule
max_parameters = 5                # Maximum parameter count
exclude_patterns = ["__init__"]   # Exclude functions matching patterns
```

**Defaults** (if section not present):
- `enabled = true`
- `max_parameters = 5`
- `exclude_patterns = []`

---

## Output Formats

### Console Format (Default)

**For `mapper quality check`**:
```
Running quality checks...

✓ Type Coverage: 85% (threshold: 80%)
✗ Docstring Coverage: 75% (threshold: 90%)
✗ Parameter Complexity: 3 violations (max: 5 parameters)

2 of 3 checks failed

Exit code: 1
```

**For individual rules** (e.g., `mapper quality type-coverage`):
```
✓ Type Coverage: 85% (threshold: 80%)
  
  By File:
  src/mapper/analyser/main.py        12/15  (80%)
  src/mapper/graph_loader/loader.py   8/10  (80%)
  src/mapper/query_system/queries.py  7/8   (87%)
  
  Overall: 27/33 public functions have type hints

Exit code: 0
```

---

### JSON Format

**Schema for `mapper quality check`**:

Returns array of quality rule results. Each rule has a different structure based on its type.

**Type Coverage / Docstring Coverage** (percentage-based rules):
```json
{
  "rule": "type_coverage",
  "status": "pass" | "fail",
  "threshold": 80,
  "actual": 85.0,
  "overall": {
    "total": 33,
    "compliant": 28,
    "percentage": 84.8
  },
  "by_file": [
    {
      "path": "src/mapper/analyser/main.py",
      "total": 15,
      "compliant": 12,
      "percentage": 80.0,
      "violations": ["process_file", "validate_path", "extract_metadata"]
    }
  ]
}
```

**Parameter Complexity** (count-based rule):
```json
{
  "rule": "param_complexity",
  "status": "pass" | "fail",
  "threshold": 5,
  "total_violations": 3,
  "by_file": [
    {
      "path": "src/mapper/analyser/main.py",
      "violations": [
        {"function": "process_extraction", "line": 42, "param_count": 7},
        {"function": "validate_and_load", "line": 95, "param_count": 6}
      ]
    }
  ]
}
```

**Full example for `mapper quality check --json`**:
```json
[
  {
    "rule": "type_coverage",
    "status": "pass",
    "threshold": 80,
    "actual": 85.0,
    "overall": {
      "total": 33,
      "compliant": 28,
      "percentage": 84.8
    },
    "by_file": [
      {
        "path": "src/mapper/analyser/main.py",
        "total": 15,
        "compliant": 12,
        "percentage": 80.0,
        "violations": ["process_file", "validate_path"]
      }
    ]
  },
  {
    "rule": "docstring_coverage",
    "status": "fail",
    "threshold": 90,
    "actual": 75.8,
    "overall": {
      "total": 33,
      "compliant": 25,
      "percentage": 75.8
    },
    "by_file": [
      {
        "path": "src/mapper/analyser/main.py",
        "total": 15,
        "compliant": 10,
        "percentage": 66.7,
        "violations": ["process_file", "validate_path", "extract_metadata"]
      }
    ]
  },
  {
    "rule": "param_complexity",
    "status": "fail",
    "threshold": 5,
    "total_violations": 3,
    "by_file": [
      {
        "path": "src/mapper/analyser/main.py",
        "violations": [
          {"function": "process_extraction", "line": 42, "param_count": 7}
        ]
      }
    ]
  }
]
```

---

### CSV Format

**Schema for `mapper quality check --csv`**:

**For percentage-based rules** (type_coverage, docstring_coverage):
```csv
rule,file_path,total_functions,compliant_functions,compliance_percentage,status
type_coverage,src/mapper/analyser/main.py,15,12,80.0,pass
type_coverage,src/mapper/graph_loader/loader.py,10,8,80.0,pass
docstring_coverage,src/mapper/analyser/main.py,15,10,66.7,fail
```

**For count-based rules** (param_complexity):
```csv
rule,file_path,function_name,line_number,parameter_count,status
param_complexity,src/mapper/analyser/main.py,process_extraction,42,7,fail
param_complexity,src/mapper/analyser/main.py,validate_and_load,95,6,fail
```

**Note**: CSV format for `mapper quality check` concatenates different CSV schemas. Percentage-based rules first, then count-based rules.

---

## Quality Rule Interface

Each quality rule implements the following interface:

### QualityRule Protocol

```python
from typing import Protocol

class QualityRule(Protocol):
    """Protocol for quality rules."""
    
    @property
    def name(self) -> str:
        """Machine-readable rule name (e.g., 'type_coverage')."""
        ...
    
    @property
    def display_name(self) -> str:
        """Human-readable rule name (e.g., 'Type Coverage')."""
        ...
    
    def is_enabled(self, config: QualityConfig) -> bool:
        """Check if rule is enabled in configuration."""
        ...
    
    def run(self, connection: Neo4jConnection, package: str) -> QualityResult:
        """Execute quality rule and return result.
        
        Args:
            connection: Neo4j connection
            package: Package name to check
            
        Returns:
            Quality result with pass/fail status
        """
        ...
```

---

### QualityConfig Model

```python
@dataclass
class TypeCoverageConfig:
    """Configuration for type coverage rule."""
    enabled: bool = True
    min_coverage: int = 80
    require_return_types: bool = False
    exclude_patterns: list[str] = field(default_factory=list)


@dataclass
class DocstringCoverageConfig:
    """Configuration for docstring coverage rule."""
    enabled: bool = True
    min_coverage: int = 90
    exclude_patterns: list[str] = field(default_factory=list)


@dataclass
class ParamComplexityConfig:
    """Configuration for parameter complexity rule."""
    enabled: bool = True
    max_parameters: int = 5
    exclude_patterns: list[str] = field(default_factory=list)


@dataclass
class QualityConfig:
    """Quality rules configuration from mapper.toml."""
    type_coverage: TypeCoverageConfig = field(default_factory=TypeCoverageConfig)
    docstring_coverage: DocstringCoverageConfig = field(default_factory=DocstringCoverageConfig)
    param_complexity: ParamComplexityConfig = field(default_factory=ParamComplexityConfig)
```

---

### QualityResult Models

**Base result** (for percentage-based rules):
```python
@dataclass
class FileResult:
    """Results for a single file."""
    path: str
    total: int
    compliant: int
    percentage: float
    violations: list[str]  # Function names


@dataclass
class OverallResult:
    """Overall results across all files."""
    total: int
    compliant: int
    percentage: float


@dataclass
class CoverageQualityResult:
    """Result for coverage-based quality rules."""
    rule: str
    status: str  # "pass" or "fail"
    threshold: int
    actual: float
    overall: OverallResult
    by_file: list[FileResult]
```

**Complexity result** (for count-based rules):
```python
@dataclass
class ViolationDetail:
    """Details of a single violation."""
    function: str
    line: int
    param_count: int


@dataclass
class FileViolations:
    """Violations for a single file."""
    path: str
    violations: list[ViolationDetail]


@dataclass
class ComplexityQualityResult:
    """Result for complexity-based quality rules."""
    rule: str
    status: str  # "pass" or "fail"
    threshold: int
    total_violations: int
    by_file: list[FileViolations]
```

---

## Neo4j Queries

Quality rules query Neo4j for package metadata using structured properties.

### Type Coverage Query

```cypher
// Find all public functions/methods with parameter metadata
MATCH (f:Function {package: $package})
WHERE f.is_public = true
  AND NOT any(pattern IN $exclude_patterns WHERE f.name =~ pattern)

// Count functions with type hints on parameters
WITH f, 
     size([p IN f.parameters WHERE p.has_type_hint = true]) as typed_params,
     size(f.parameters) as total_params

// Function has type coverage if all params have type hints
WITH f,
     CASE WHEN total_params = 0 THEN true
          WHEN typed_params = total_params THEN true
          ELSE false
     END as has_type_coverage

// Aggregate by file
RETURN f.file_path as file_path,
       count(*) as total,
       sum(CASE WHEN has_type_coverage THEN 1 ELSE 0 END) as compliant,
       collect(CASE WHEN NOT has_type_coverage THEN f.name ELSE null END) as violations
```

---

### Docstring Coverage Query

```cypher
// Find all public functions/methods
MATCH (f:Function {package: $package})
WHERE f.is_public = true
  AND NOT any(pattern IN $exclude_patterns WHERE f.name =~ pattern)

// Check if function has docstring
WITH f,
     CASE WHEN f.docstring IS NOT NULL AND f.docstring <> "" THEN true
          ELSE false
     END as has_docstring

// Aggregate by file
RETURN f.file_path as file_path,
       count(*) as total,
       sum(CASE WHEN has_docstring THEN 1 ELSE 0 END) as compliant,
       collect(CASE WHEN NOT has_docstring THEN f.name ELSE null END) as violations
```

---

### Parameter Complexity Query

```cypher
// Find all public functions/methods with parameter count exceeding threshold
MATCH (f:Function {package: $package})
WHERE f.is_public = true
  AND NOT any(pattern IN $exclude_patterns WHERE f.name =~ pattern)
  AND size(f.parameters) > $max_parameters

// Return violations grouped by file
RETURN f.file_path as file_path,
       collect({
         function: f.name,
         line: f.start_line,
         param_count: size(f.parameters)
       }) as violations
ORDER BY file_path
```

---

## Output Formatting

### Console Formatter

**Responsibilities**:
- Format quality results for human-readable console output
- Use check marks (✓) for pass, X marks (✗) for fail
- Show file-level breakdown with percentages
- List violations for failed rules

**Interface**:
```python
class ConsoleFormatter:
    """Format quality results for console output."""
    
    def format_check_results(self, results: list[QualityResult]) -> str:
        """Format results from `mapper quality check`.
        
        Args:
            results: List of quality rule results
            
        Returns:
            Formatted console output
        """
        ...
    
    def format_single_result(self, result: QualityResult) -> str:
        """Format result from individual quality rule command.
        
        Args:
            result: Single quality rule result
            
        Returns:
            Formatted console output with file breakdown
        """
        ...
```

---

### JSON Formatter

**Responsibilities**:
- Serialize quality results to JSON
- Maintain schema for each result type
- Support jq parsing for CI/CD

**Interface**:
```python
class JSONFormatter:
    """Format quality results as JSON."""
    
    def format(self, results: list[QualityResult]) -> str:
        """Format quality results as JSON array.
        
        Args:
            results: List of quality rule results
            
        Returns:
            JSON string
        """
        ...
```

---

### CSV Formatter

**Responsibilities**:
- Serialize quality results to CSV
- Handle different schemas for percentage vs count rules
- Support spreadsheet import

**Interface**:
```python
class CSVFormatter:
    """Format quality results as CSV."""
    
    def format(self, results: list[QualityResult]) -> str:
        """Format quality results as CSV.
        
        Args:
            results: List of quality rule results
            
        Returns:
            CSV string with headers
        """
        ...
```

---

## Implementation Notes

### Configuration Loading

Configuration is loaded from `mapper.toml`:
1. Check for `[quality.type_coverage]`, `[quality.docstring_coverage]`, `[quality.param_complexity]` sections
2. If section missing, use default configuration
3. Validate configuration values (e.g., percentages 0-100, max_parameters > 0)

### Exclude Patterns

Exclude patterns use glob-style matching:
- `test_*`: Match functions starting with "test_"
- `__init__`: Match exact function name
- `*_internal`: Match functions ending with "_internal"

Patterns are applied to function names, not file paths.

### Exit Code Logic

For `mapper quality check`:
```python
def determine_exit_code(results: list[QualityResult]) -> int:
    """Determine exit code from quality results."""
    if any(result.status == "fail" for result in results):
        return 1
    return 0
```

### Error Handling

**Neo4j connection errors**:
- Display clear error message
- Exit with code 1

**Invalid configuration**:
- Display validation error
- Show expected format
- Exit with code 1

**No package analyzed**:
- Display "No analysis found for package" message
- Suggest running `mapper analyse`
- Exit with code 1

---

## Related Documentation

- [User Journey: Running Quality Rules](../user-journeys/10-quality-rules.md)
- [User Journey: Querying Structured Metadata](../user-journeys/09-querying-structured-metadata.md)
- [Technical: Neo4j Schema](../technical/neo4j-schema.md)
