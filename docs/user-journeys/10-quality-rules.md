# User Journey: Running Quality Rules

**Version**: 0.8.1  
**Audience**: Tier 1 users (don't want to write Cypher)  
**Goal**: Enforce code quality standards with built-in pass/fail checks

---

## Overview

Quality rules provide built-in pass/fail checks for code quality standards. Unlike exploratory queries that return ranked results, quality rules enforce thresholds and provide clear pass/fail status suitable for CI/CD pipelines.

**Key Differences from Queries:**
- **Queries** (`mapper query`): Exploratory, ranked results, severity levels (critical → ok)
- **Quality** (`mapper quality`): Enforcement, pass/fail, exit codes for CI/CD

---

## User Story

**As a** Python developer maintaining code quality standards,  
**I want** to enforce type coverage and docstring requirements without writing Cypher,  
**So that** I can gate pull requests and maintain consistent code quality across my team.

---

## Prerequisites

1. Project analyzed with `mapper analyse`
2. Neo4j running and accessible
3. `mapper.toml` configuration file (optional, for custom thresholds)

---

## Workflow

### Step 1: Configure Quality Rules

Create or update `mapper.toml` with quality rule thresholds:

```toml
[quality.type_coverage]
enabled = true
min_coverage = 80           # percentage
require_return_types = true
exclude_patterns = ["test_*", "__init__"]

[quality.docstring_coverage]
enabled = true
min_coverage = 90
exclude_patterns = ["__str__", "__repr__"]

[quality.param_complexity]
enabled = true
max_parameters = 5
exclude_patterns = ["__init__"]
```

**Default behavior (if no config):**
- Type coverage: 80% threshold, return types optional
- Docstring coverage: 90% threshold
- Parameter complexity: 5 parameters maximum

---

### Step 2: Run Individual Quality Checks

Check type hint coverage:

```bash
$ mapper quality type-coverage

✓ Type Coverage: 85% (threshold: 80%)
  
  By File:
  src/mapper/analyser/main.py        12/15  (80%)
  src/mapper/graph_loader/loader.py   8/10  (80%)
  src/mapper/query_system/queries.py  7/8   (87%)
  
  Overall: 27/33 public functions have type hints

Exit code: 0
```

Check docstring coverage:

```bash
$ mapper quality docstring-coverage

✗ Docstring Coverage: 75% (threshold: 90%)
  
  By File:
  src/mapper/analyser/main.py         10/15  (66%) ← below threshold
  src/mapper/graph_loader/loader.py    8/10  (80%) ← below threshold
  src/mapper/query_system/queries.py   7/8   (87%)
  
  Overall: 25/33 public functions have docstrings
  
  Missing docstrings:
  - src/mapper/analyser/main.py:42 (process_file)
  - src/mapper/analyser/main.py:58 (validate_path)
  - src/mapper/analyser/main.py:73 (extract_metadata)
  - src/mapper/graph_loader/loader.py:105 (create_edge)
  - src/mapper/graph_loader/loader.py:120 (find_node)

Exit code: 1
```

Check parameter complexity:

```bash
$ mapper quality param-complexity

✗ Parameter Complexity: 3 violations (threshold: 5 max)
  
  By File:
  src/mapper/analyser/main.py         2 violations
  src/mapper/graph_loader/loader.py   1 violation
  
  Functions exceeding threshold:
  - src/mapper/analyser/main.py:42 (process_extraction) - 7 parameters
  - src/mapper/analyser/main.py:95 (validate_and_load) - 6 parameters
  - src/mapper/graph_loader/loader.py:156 (_create_single_import_node) - 6 parameters

Exit code: 1
```

---

### Step 3: Run All Enabled Checks

Use `mapper quality check` to run all enabled rules:

```bash
$ mapper quality check

Running quality checks...

✓ Type Coverage: 85% (threshold: 80%)
✗ Docstring Coverage: 75% (threshold: 90%)
✗ Parameter Complexity: 3 violations (max: 5 parameters)

2 of 3 checks failed

Exit code: 1
```

---

### Step 4: Export Results for CI/CD

**JSON output (for tooling):**

```bash
$ mapper quality check --json
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
        "violations": ["process_file", "validate_path", "extract_metadata"]
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
        "violations": ["process_file", "validate_path", "extract_metadata", "helper_fn", "setup"]
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
          {"function": "process_extraction", "line": 42, "param_count": 7},
          {"function": "validate_and_load", "line": 95, "param_count": 6}
        ]
      },
      {
        "path": "src/mapper/graph_loader/loader.py",
        "violations": [
          {"function": "_create_single_import_node", "line": 156, "param_count": 6}
        ]
      }
    ]
  }
]
```

**CSV output (for tracking over time):**

```bash
$ mapper quality check --csv
rule,file_path,total_functions,compliant_functions,compliance_percentage,status
type_coverage,src/mapper/analyser/main.py,15,12,80.0,pass
type_coverage,src/mapper/graph_loader/loader.py,10,8,80.0,pass
type_coverage,src/mapper/query_system/queries.py,8,7,87.5,pass
docstring_coverage,src/mapper/analyser/main.py,15,10,66.7,fail
docstring_coverage,src/mapper/graph_loader/loader.py,10,8,80.0,fail
docstring_coverage,src/mapper/query_system/queries.py,8,7,87.5,pass
param_complexity,src/mapper/analyser/main.py,15,13,86.7,fail
param_complexity,src/mapper/graph_loader/loader.py,10,9,90.0,fail
param_complexity,src/mapper/query_system/queries.py,8,8,100.0,pass
```

---

## CI/CD Integration

### GitHub Actions Example

```yaml
name: Code Quality

on: [pull_request]

jobs:
  quality:
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v4
      
      - name: Setup Python
        uses: actions/setup-python@v5
        with:
          python-version: '3.12'
      
      - name: Start Neo4j
        run: |
          docker run -d --name neo4j \
            -p 7687:7687 \
            -e NEO4J_AUTH=neo4j/password \
            neo4j:5
      
      - name: Install mapper
        run: pip install mapper-tool
      
      - name: Analyze code
        run: mapper analyse .
        env:
          NEO4J_USER: neo4j
          NEO4J_PASSWORD: password
      
      - name: Run quality checks
        run: mapper quality check --json > quality-report.json
        env:
          NEO4J_USER: neo4j
          NEO4J_PASSWORD: password
      
      - name: Parse results
        if: failure()
        run: |
          echo "Failed rules:"
          jq -r '.[] | select(.status == "fail") | .rule' quality-report.json
      
      - name: Upload report
        uses: actions/upload-artifact@v4
        with:
          name: quality-report
          path: quality-report.json
```

### Parsing JSON with jq

**Check overall status:**
```bash
mapper quality check --json | jq 'any(.[]; .status == "fail")'
# Output: true (if any failed), false (if all passed)
```

**Get all failed rules:**
```bash
mapper quality check --json | jq -r '.[] | select(.status == "fail") | .rule'
# Output: docstring_coverage
```

**Count violations per file:**
```bash
mapper quality type-coverage --json | jq '.by_file[] | {path, violations: (.total - .compliant)}'
# Output: {"path": "src/mapper/analyser/main.py", "violations": 3}
```

**Get worst-performing files:**
```bash
mapper quality type-coverage --json | jq '.by_file | sort_by(.percentage) | .[0:3]'
# Output: Top 3 files with lowest coverage
```

**Extract specific file results:**
```bash
mapper quality check --json | jq '.[] | .by_file[] | select(.path | contains("analyser"))'
# Output: All analyser file results
```

---

## Verification

After running quality checks:

1. **Exit code indicates pass/fail:**
   - Exit code 0: All enabled checks passed
   - Exit code 1: One or more checks failed

2. **Console output shows summary:**
   - Check mark (✓) for passed rules
   - X mark (✗) for failed rules
   - File-level breakdown with percentages

3. **JSON output is parsable:**
   - Array of rule results
   - Each result has status, threshold, actual, by_file details
   - Can be parsed with jq or other JSON tools

4. **CSV output is importable:**
   - Standard CSV format with headers
   - One row per file per rule
   - Can be imported to spreadsheets or databases

---

## Troubleshooting

### "No configuration found"

If no `mapper.toml` exists, default thresholds are used:
- Type coverage: 80%
- Docstring coverage: 90%
- Parameter complexity: 5 parameters maximum

Create `mapper.toml` in project root to customize.

### "Quality check failed but I see 100% coverage"

Check exclude patterns - some functions may be excluded:
- Test files (`test_*.py`)
- Private functions (starting with `_`)
- Special methods (`__init__`, `__str__`, `__repr__`)

### "Exit code 0 but some files are below threshold"

Quality checks are package-level, not file-level. A file can be below threshold as long as the overall package meets the threshold.

To enforce file-level thresholds, use individual file checks:
```bash
mapper quality type-coverage --json | jq '.by_file[] | select(.percentage < 80)'
```

---

## Related Documentation

- [Interface Design: Quality Rules](../interface/quality-rules.md)
- [User Journey: Querying Structured Metadata](./09-querying-structured-metadata.md)
- [Technical: Neo4j Schema](../technical/neo4j-schema.md)
