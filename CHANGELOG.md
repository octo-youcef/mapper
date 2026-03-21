# Changelog

All notable changes to this project will be documented in this file.

The format is based on [Keep a Changelog](https://keepachangelog.com/en/1.0.0/),
and this project adheres to [Semantic Versioning](https://semver.org/spec/v2.0.0.html).

## [Unreleased]

## [0.2.0] - 2026-03-21

### Added
- **Configuration system** with TOML-based global and local configs
  - Global config: `~/.config/mapper/config.toml`
  - Local config: `.mapper.toml` (overrides global)
  - Configuration sections: `[neo4j]`, `[analysis]`, `[output]`
  - Reads Neo4j credentials from `NEO4J_USER` and `NEO4J_PASSWORD` environment variables
- **Interactive `mapper init` command** for guided setup
  - Validates required environment variables (fails fast if missing)
  - Prompts for Neo4j connection details with sensible defaults
  - Tests Neo4j connectivity before proceeding
  - Initializes database schema with constraints and indexes
  - Creates config file with all options documented
  - Supports `--global` flag for global configuration
- **Config management commands**
  - `mapper config get` - View effective configuration with source indicators
  - `mapper config get --global/--local` - View specific config
  - `mapper config set` - Set configuration values
  - `mapper config edit` - Edit config in $EDITOR
- **Neo4j database initialization**
  - Idempotent constraints: unique `Module.path`, `Class.fqn`, `Function.fqn`
  - Performance indexes on name and type fields
  - Automatic schema setup via `mapper init`
- **Integration test suite** (7 tests)
  - Full init workflow testing
  - Environment variable validation
  - Connection testing and error handling
  - Config file creation and merging
- **User journey documentation**
  - Initial Setup guide with step-by-step Neo4j setup and configuration
  - Configuration Management guide for global/local settings
  - Updated user journey index
- **Technical documentation**
  - Configuration System architecture and implementation details
  - Neo4j Schema with constraints, indexes, and best practices
  - Updated technical documentation index
- Dependencies: `tomli` (Python 3.10), `tomli-w` for TOML support

### Changed
- Neo4j default password changed from `neo4j` to `devpassword` (Neo4j 5+ requirement)
- Updated documentation to reflect new credentials and setup process

## [0.1.2] - 2026-03-21

### Changed
- Replaced GitHub releases badge with static version badge (auto-updated by bump-my-version)
- Replaced Codecov with gist-based dynamic coverage badge
- Updated badge system to follow chew-site pattern (version, tests, coverage, python)
- Made test badge dynamic (auto-updated by CI via GitHub Gist)

### Removed
- Codecov integration

### Added
- CI workflow to auto-update coverage and test badges via GitHub Gist
- Coverage badge color-coding based on percentage
- Comprehensive badge system documentation in docs/technical/badges.md
- CODEOWNERS file for main branch protection

## [0.1.1] - 2026-03-21

### Changed
- Expanded Python support to 3.10+ (previously 3.12+)
- Added CI matrix testing for Python 3.10, 3.11, and 3.12
- Fixed coverage path in CI workflow

## [0.1.0] - 2026-03-21

### Added
- Initial project setup with CLI structure
- Typer-based CLI with placeholder commands
- Modular CLI organization (analyse, config, queries groups)
- Comprehensive test suite (45 tests)
- Technical documentation for CLI commands
- Neo4j Docker setup for development
- GitHub Actions CI/CD pipeline

[unreleased]: https://github.com/octo-youcef/mapper/compare/v0.2.0...HEAD
[0.2.0]: https://github.com/octo-youcef/mapper/compare/v0.1.2...v0.2.0
[0.1.2]: https://github.com/octo-youcef/mapper/compare/v0.1.1...v0.1.2
[0.1.1]: https://github.com/octo-youcef/mapper/compare/v0.1.0...v0.1.1
[0.1.0]: https://github.com/octo-youcef/mapper/releases/tag/v0.1.0
