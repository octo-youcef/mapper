# Documentation Standards

This guide covers documentation requirements and structure for the Mapper project.

## Documentation Structure

```
docs/
├── user-journeys/      # User journey documentation (CRITICAL)
│   ├── NN-feature-name.md
│   └── README.md
├── interface/          # Interface documentation (CRITICAL)
│   ├── cli.md
│   ├── api.md
│   └── README.md
├── technical/          # Technical architecture
│   ├── module-name.md
│   └── README.md
└── architecture/       # System design
    └── overview.md
```

User-journey and interface documentation are the most important - always start here before implementing.

---

## When to Document

### New User Journeys

Document in `docs/user-journeys/`:
- Format: Prerequisites → Steps → Outcomes → Troubleshooting
- Update index: `docs/user-journeys/README.md`
- Cross-reference related journeys
- Create **draft PR** for review before implementation

### New/Modified Interfaces

Document in `docs/interface/`:
- **All public APIs and interfaces** must be documented
- CLI commands, API endpoints, function signatures
- Include usage examples
- Create **draft PR** for review before implementation
- **Must be kept up to date** with code changes

### New/Modified Modules

Document in `docs/technical/`:
- Purpose, key classes/functions, usage examples
- Integration points with other modules
- Update index: `docs/technical/README.md`

### New Project Rules

Update `CLAUDE.md` immediately:
- Keep rules clear, actionable, specific
- Update "Last Updated" date

### All Changes

Update `CHANGELOG.md` with user-facing changes

---

## Documentation Validity

All documentation must be checked for validity before commit:
- Links work
- Code examples run
- Instructions are accurate
- Version numbers are current
- Interface documentation matches actual code (CLI commands, API signatures, function interfaces)

---

## User Journey Format

```markdown
# NN: Feature Name

**Goal**: [What the user wants to accomplish]

**Prerequisites**:
- [What must be set up first]

**Steps**:
1. [First step]
2. [Second step]
   ```bash
   # Example command
   ```
3. [Third step]

**Verification**:
- [How to confirm success]

**Troubleshooting**:
- **Issue**: [Common problem]
  - **Solution**: [How to fix]
```

---

## Interface Documentation Format

```markdown
# Module Name

## Overview
[Brief description of what this module provides]

## Classes

### ClassName
[Description]

**Methods**:
- `method_name(param: Type) -> ReturnType`: [Description]

**Example**:
```python
from mapper import module

instance = module.ClassName(param)
result = instance.method_name(value)
```

## Functions

### function_name
```python
def function_name(param: Type) -> ReturnType:
    """Docstring."""
```

[Description and usage examples]
```

---

## Technical Documentation Format

```markdown
# Module Name

## Purpose
[Why this module exists, what problem it solves]

## Key Components

### ClassName
[Description, responsibilities, key methods]

### AnotherClass
[Description, responsibilities, key methods]

## Integration Points
[How this module interacts with others]

## Usage Examples
[Real-world examples of using this module]

## Design Decisions
[Rationale for key architectural choices]
```
