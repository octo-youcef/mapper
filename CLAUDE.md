# Claude Code Instructions for Mapper

This file contains project-specific instructions for Claude Code when working with this repository. General workflow preferences are in Claude's MEMORY.md and apply unless overridden here.

## Table of Contents
- [Philosophy](#philosophy) ⭐
- [Project Context](#project-context)
- [CRITICAL Rules](#critical-rules) 🚨
- [Development Workflow](#development-workflow)
- [Git Workflow](#git-workflow)
- [Versioning](#versioning)
- [Quick Reference](#quick-reference)
- [Code Standards Reference](#code-standards-reference) 📚

---

## Philosophy

These principles guide how we work together:

**Experiment and iterate**: Try things, see what works, throw away what doesn't quickly. "If it doesn't agree with experiment, it's wrong." - Feynman

**Question everything**: Always question me. Push back if something seems wrong. A few more questions leading to a better solution is preferred over rushing to the wrong implementation.

**Context is king**: Provide enough context to understand and debug. Error messages, logs, documentation - always include relevant context.

**Simple is better than complex**: Choose simple solutions over complex ones. Don't over-engineer.

**User interface and user outcomes are paramount**: Everything else can be changed later, but getting the user experience right is critical.

---

## Project Context

- **Type**: CLI Tool
- **Purpose**: AST-based Python code analyzer with Neo4j graph storage
- **Package Manager**: uv
- **Task Runner**: just
- **Testing**: pytest, pytest-mock
- **Code Quality**: ruff, mypy, isort
- **CLI Framework**: Typer
- **Database**: Neo4j

---

## CRITICAL Rules 🚨

**These rules override any defaults and must be followed exactly:**

### Question-Asking Protocol (MOST IMPORTANT)

Before implementing features, ask questions **one at a time**:

- **Ask ONE question** - Allow user to focus and give detailed answers
- **Provide context** - Explain why the question matters
- **Offer suggestions** - Include your recommendation
- **Number questions** - Track progress through decision-making

Examples of what to ask about:
- User journey: What is the user trying to accomplish?
- User experience: How should the interface look/feel?
- Design decisions: Data structures, APIs, algorithms
- Error handling strategies
- Testing approach

**Why this is critical**: Asking good questions one at a time leads to better design decisions and saves significant rework time.

### Validate Changes Against Style Guides (BLOCKING)

**All code changes must comply with the contributing style guides:**

- [Python Style Guide](docs/contributing/python-style.md) - Import style, protocols, naming, types, docstrings, error handling
- [Code Architecture](docs/contributing/code-architecture.md) - Public vs private, module organization, function ordering
- [Testing Standards](docs/contributing/testing.md) - Coverage, organization, parametrization
- [Documentation Standards](docs/contributing/documentation.md) - Structure, formats, validity

**Before push:** Run `just lint` to catch style violations automatically.

---

## Development Workflow

### Feature Implementation Workflow (CRITICAL)

**Goal: Small increments, fast feedback, fewer review rounds.**

Work happens in phases with explicit checkpoints for early alignment.

---

#### Phase 1: Align on Approach

1. Discuss user journey with questions (one at a time)
2. Write user journey document (`docs/user-journeys/NN-feature-name.md`)
   - Define user goals, workflow, and outcomes
   - Include prerequisites, steps, verification, troubleshooting
   - Update `docs/user-journeys/README.md` index

**CHECKPOINT 1**: Push draft PR with user journey doc
- **Request review**: "User journey complete - validating we're solving the right problem"
- User validates: Is this the right problem to solve?

---

#### Phase 2: Design Interface

3. Write interface documentation (`docs/interface/feature-name.md`) if adding public APIs
   - Document public interface (CLI commands, API endpoints, function signatures)
   - Include usage examples showing how it will be used

**CHECKPOINT 2**: Push interface docs to same PR
- **Request review**: "Interface design complete - validating API ergonomics before implementation"
- User validates: Is the interface clear and well-designed?

---

#### Phase 3: Plan Implementation

4. Create implementation plan in ROADMAP.md:
   ```markdown
   ## [Feature Name] - Implementation Plan
   
   **PR Strategy**: Single PR | Multiple smaller PRs
   
   **GitHub Issues**: #XX, #YY (list all issues this work will resolve)
   
   **Commit Structure**:
   1. [Self-contained unit 1] - what and why
   2. [Self-contained unit 2] - what and why
   ...
   
   **Review Milestones**:
   - After Commit X: Why review here? (e.g., "Validate foundation")
   - After Commit Y: Why review here? (e.g., "Before building on this")
   - Final: Ready for merge after version bump
   
   **Technical Approach**:
   - Key architectural decisions
   - Design patterns used
   - Integration points
   ```
   
   **IMPORTANT**: Check ROADMAP.md for any existing GitHub issues related to this feature. List them in the plan so they can be referenced in the PR and closed on merge.

**CHECKPOINT 3**: Push plan to ROADMAP.md
- **Request review**: "Implementation plan complete - agreeing on commit structure and milestones"
- User validates: Agree on granularity, PR strategy, and review points?

---

#### Phase 4: Implement Incrementally

5. Implement according to plan:
   - Write tests first for each unit
   - Implement the functionality
   - Keep commits matching the plan structure
   - **Keep fixup commits during draft phase** - makes incremental review easier

**Push at planned milestones**:
- After completing each milestone from plan
- **Always include context**: "Milestone X complete: [what] - ready for review to [why]"
- Example: "Foundation complete: base classes and registry - ready for review to validate before building queries on top"

**When to push for milestone review:**

✅ Completed a planned commit/unit
✅ Foundation work that later work builds on
✅ Complete feature slice working end-to-end
✅ Before a major direction change needs validation
✅ After significant refactor affecting many files

❌ Not after every single commit (too granular)
❌ Not when stuck on implementation detail (try to solve first)

**PR stays in DRAFT** - Allows fixup commits without breaking review flow

---

#### Phase 5: Finalize

6. Self-validate before asking for final review:
   - Run `just lint` and fix all issues
   - Run `just test-coverage` and verify coverage passes
   - Check all changes against [contributing style guides](#code-standards-reference-)
   
7. Update documentation:
   - CHANGELOG.md with user-facing changes
   - README.md if features or commands changed
   - Technical docs in `docs/technical/` if architecture changed
   - Review existing docs for accuracy

8. Version bump:
   - Propose version type (patch/minor/major) and get confirmation
   - Run `just version <type>` to bump version
   - Update "Current Version" in this file

9. **Rebase to clean commit history**:
   - Squash fixup commits into their parent commits
   - Ensure each commit is self-contained and logical
   - Verify all tests pass after rebase

10. **Verify GitHub issue references**:
    - Check ROADMAP.md implementation plan for listed GitHub issues
    - Add issue references to PR description (e.g., "Closes #33, Resolves #42")
    - Verify issue numbers are correct and still open

11. **Mark PR ready for final review**
    - **Request review**: "Ready for final review - all feedback addressed, tests passing, docs updated"
    - Wait for CI to pass (use `gh pr view <number> --json statusCheckRollup`)

---

**Key Principles:**

- **3 upfront checkpoints** catch issues when they're cheap to fix
- **Milestone reviews during implementation** prevent building on wrong foundation  
- **Draft PR + fixup commits** make incremental review easier
- **Clean history at the end** via rebase before marking ready
- **Explicit review requests** with context help reviewer understand what and why

---

## Git Workflow

**This section guides how we work together on commits and PRs.**

### Branch Strategy

Branches should be descriptive and categorical:

- **`feature/description`** - New features or enhancements
- **`fix/description`** - Bug fixes
- **`patch/description`** - Small patches, typos, minor corrections
- **`docs/description`** - Documentation-only changes

Use descriptive names that explain what the branch does, not just ticket numbers.

**NEVER push directly to main** - ALL changes go through PRs. Main branch is protected - direct pushes rejected.

### Commit History

**Goal: Clean, logical commits that tell a story.**

**During draft PR phase:**
- Fixup commits are ENCOURAGED - makes incremental review easier
- "Fix linting", "Address feedback", "Fix typo" commits are fine
- Reviewer can see what changed since last review without re-reading everything

**Before marking PR ready (Phase 5):**
- Rebase to squash fixups into logical feature units
- Each commit = complete, cohesive piece of functionality
- Related changes grouped together (feature + tests + docs)
- Commits tell a clear story
- Reviewers can understand each commit in isolation

**Final commit structure example:**
```
✅ GOOD - After rebase, logical units:
1. Add query infrastructure (registry, executor, formatters)
2. Add find-dead-code query with tests
3. Add remaining queries with tests
4. Add CLI integration
5. Update documentation
6. Bump version: 0.7.0 → 0.7.1

✅ ALSO GOOD - During draft, incremental changes visible:
1. Add query infrastructure
2. Fix linting in registry
3. Address feedback: simplify executor
4. Add find-dead-code query
5. Fix typo in query
...
[Then rebase before marking ready]
```

### Handling Review Feedback

**At milestones during draft PR:**
- Add fixup commits addressing feedback
- Push with context: "Addressed feedback on milestone X: [what changed]"
- Keeps incremental changes visible for next review

**Before marking ready (Phase 5):**
- Rebase to incorporate all feedback into logical commits
- Use `git rebase -i` to squash fixups
- Verify tests pass after rebase
- Push cleaned history

### Commit Messages

Keep commit messages clear and informative:

- First line: Brief summary (under 70 characters)
- Blank line
- Detailed explanation if needed (why this change, not what changed)
- Reference issues/PRs if relevant

```
Add JWT authentication for API endpoints

Implement token-based authentication to secure API access.
Users can obtain tokens via /auth/login and include them
in Authorization headers for subsequent requests.

Fixes #123
```

### Git Safety Protocol

- NEVER update the git config
- NEVER run destructive git commands (push --force, reset --hard, checkout ., restore ., clean -f, branch -D) unless the user explicitly requests these actions
  - `git push --force-with-lease` is acceptable and preferred over `--force`
- NEVER skip hooks (--no-verify, --no-gpg-sign, etc) unless the user explicitly requests it
- NEVER run force push to main/master, warn the user if they request it
- CRITICAL: Always create NEW commits rather than amending, unless the user explicitly requests a git amend
- When staging files, prefer adding specific files by name rather than using "git add -A" or "git add ."

---

## Versioning

### Version Bumps

- **Patch** (0.2.0 → 0.2.1): Bug fixes, documentation, minor improvements
- **Minor** (0.2.0 → 0.3.0): New features, enhancements, new capabilities
- **Major** (0.2.0 → 1.0.0): Breaking changes, incompatible API changes

### Version Management

- Use `just version patch|minor|major` to bump version
- Automatic updates:
  - `pyproject.toml` (version field)
  - `src/mapper/__init__.py` (__version__ variable)
  - `README.md` (version badge)
  - `CHANGELOG.md` ([Unreleased] → versioned section)
  - Creates git commit (no tag)
- **Manual update**: "Current Version" field at bottom of this file

**Note:** Tags are created by GitHub Actions on merge to main, not locally. This prevents tag conflicts during PR rebases.

### README Badges

- **Version badge**: Auto-updated by `just version`
- **Tests badge**: Manually update test count after `just test-coverage`
- **Coverage badge**: Auto-updated by CI after merge (via GitHub Gist)
- **Python badge**: Manually updated for supported versions

---

## Quick Reference

### Common Commands

```bash
# Development
just install          # Install dependencies
just build/up/down    # Docker container management
just reset            # Full reset (stops, removes volumes, rebuilds)

# Testing & Quality
just test             # Run all tests
just test-coverage    # With coverage report
just format           # Format code (ruff + isort)
just lint             # Run all quality checks

# Versioning
just version-show     # Show current version
just version patch    # Bump patch version
just version minor    # Bump minor version

# CLI
just mapper [args]    # Run CLI tool
```

### Feature Implementation Quick Reference

**Phases with checkpoints:**
1. **Align** → User journey doc → Request review
2. **Design** → Interface docs → Request review  
3. **Plan** → Implementation plan in ROADMAP.md (list GitHub issues) → Request review
4. **Implement** → Code according to plan → Request review at milestones
5. **Finalize** → Self-validate, update docs, bump version, rebase, verify issue refs → Mark ready

**Before each push:**
- Run `just lint` to catch style issues
- Self-validate against [contributing guides](#code-standards-reference-)
- Include context: what milestone and why reviewing

**Before marking ready:**
- All tests passing (`just test-coverage`)
- All docs updated (CHANGELOG, README, technical docs)
- Clean commit history (rebase/squash fixups)
- Version bumped
- GitHub issues verified and referenced in PR (check ROADMAP.md plan)

---

## Code Standards Reference 📚

**For detailed standards, refer to these guides:**

### Before Writing Code

Review these documents to understand patterns and best practices:

- **[Python Style Guide](docs/contributing/python-style.md)** - Import style, protocol naming, type hints, docstrings, error handling, data structures, string formatting, data classes, context managers
- **[Code Architecture](docs/contributing/code-architecture.md)** - Public vs private naming, application vs CLI separation, module organization, function ordering, enums, AST analysis scope, Neo4j schema
- **[Testing Standards](docs/contributing/testing.md)** - Coverage requirements, test organization, parametrization, code quality checks

### Before Documenting

- **[Documentation Standards](docs/contributing/documentation.md)** - Structure, formats, validity requirements, when to document

### Important Notes

- The guides above provide detailed explanations and examples
- This CLAUDE.md file contains project-specific overrides and workflow instructions
- **When uncertain**: Check the relevant guide first, then ask user for validation if still ambiguous
  - Previous wording "check the guide first" was unclear about next steps after checking
  - Always prefer asking for clarification over making assumptions
- CRITICAL rules in this file (Question-Asking Protocol, Style Guide validation) always take precedence

---

**Last Updated**: 2026-04-04  
**Current Version**: 0.7.9
