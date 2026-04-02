# Testing Standards

This guide covers testing requirements and patterns for the Mapper project.

## Coverage Requirements

- **Minimum 80% coverage** - CI will fail below this threshold
- Run `just test-coverage` to verify
- Add tests for new code to maintain coverage

---

## Test Organization

**Mirror source structure** and separate by type:

```
tests/
├── conftest.py                      # Shared fixtures
├── unit/
│   ├── cli/
│   │   ├── test_setup.py
│   │   └── test_analyse.py
│   ├── ast_parser/
│   │   └── test_extractor.py
│   └── status_checker/
│       └── test_checker.py
└── integration/
    ├── cli/
    │   └── test_workflows.py
    └── analyser/
        └── test_end_to_end.py
```

**Benefits:**
- Groups tests by type (unit vs integration)
- Then groups by module being tested
- Makes it easy to find all tests for a specific module
- Scales well as project grows

---

## Testing Style

**Prefer test classes over flat functions:**

```python
# ✅ CORRECT - Test classes group related tests
class TestAnalyzeCommand:
    """Tests for analyze command."""

    def test_basic_analysis(self):
        """Test basic analysis with required path."""
        ...

    def test_with_options(self):
        """Test with command options."""
        ...

# ❌ INCORRECT - Flat test functions
def test_analyze_basic():
    ...

def test_analyze_options():
    ...
```

**Benefits:** Better organization, easier setup/teardown, clearer test hierarchy

---

## Parametrized Tests

**Use parametrized tests for repetitive patterns:**

```python
# ✅ CORRECT - Parametrize similar test cases
@pytest.mark.parametrize(
    "flag,should_suppress_output",
    [
        ("--quiet", True),
        ("-q", True),
        ("--verbose", False),
        ("-v", False),
    ],
    ids=["quiet", "quiet-short", "verbose", "verbose-short"],
)
def test_output_flags(self, flag, should_suppress_output):
    """Test command with output control flags."""
    result = runner.invoke(app, ["analyse", "start", str(tmp_path), flag])
    assert result.exit_code == 0
    if should_suppress_output:
        assert "Analyzing:" not in result.stdout

# ❌ INCORRECT - Duplicate test logic
def test_quiet_flag(self):
    """Test command with --quiet flag."""
    result = runner.invoke(app, ["analyse", "start", str(tmp_path), "--quiet"])
    assert result.exit_code == 0
    assert "Analyzing:" not in result.stdout

def test_quiet_short_flag(self):
    """Test command with -q flag."""
    result = runner.invoke(app, ["analyse", "start", str(tmp_path), "-q"])
    assert result.exit_code == 0
    assert "Analyzing:" not in result.stdout
```

**When to parametrize:**
- Testing same logic with different inputs/outputs
- Flag variations (`--verbose`/`-v`, `--quiet`/`-q`)
- Multiple valid data patterns (import styles, name resolution patterns)
- Edge cases with different values

**When NOT to parametrize:**
- Tests with different mock configurations or complex unique setups
- Tests that verify fundamentally different behavior
- Tests where shared setup would obscure intent

**Test IDs:**
- Always provide `ids` parameter for readable test output
- Use descriptive names: `"simple-import"`, `"import-with-alias"`
- Use lambda for complex parameter sets: `ids=lambda x: x if isinstance(x, str) and "-" in x else ""`

**Benefits:** Reduces code duplication, makes test patterns explicit, easier to add new test cases

---

## Code Quality Checks

### Before Every Commit

- **MUST validate linting**: `just lint` - Fix all issues
- **MUST pass type checking**: `uv run mypy .` - No errors
- **MUST format code**: `just format` - Consistent style
- Never commit code that fails linting

### Before Every PR

- **MUST pass all tests**: `just test` - All tests green
- **MUST maintain 80% coverage**: `just test-coverage` - Coverage must be ≥ 80%
- **MUST pass CI checks**: All GitHub Actions workflows pass
- Update test count in README.md (e.g., "58 passing")

---

## Pre-Commit Hooks

Required checks before local commit:

1. **Format code** - Auto-format to correct style (`just format`)
2. **Linting** - All linting checks pass (`just lint`)
3. **Type checking** - mypy must pass (`uv run mypy .`)
4. **Unit tests** - All unit tests pass
5. **CHANGELOG** - CHANGELOG.md must be updated
6. **Documentation validity** - All docs checked (links work, examples run, instructions accurate)
7. **Secrets scanning** - No API keys, tokens, passwords, or credentials

**Never Commit:**
- `.env` files
- Credential files
- API keys or tokens
- Sensitive configuration
- Data files
- Personal information

---

## Pre-Push Hooks

Required checks before pushing to remote:

1. **All pre-commit checks** - Everything from pre-commit must pass (implied)
2. **Build verification** - Project builds successfully
3. **Unit tests + coverage** - 80% coverage required
4. **Integration tests** - All integration tests pass
5. **Version bump** - Version must be incremented appropriately
