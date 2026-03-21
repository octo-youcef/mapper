# Changelog

All notable changes to this project will be documented in this file.

The format is based on [Keep a Changelog](https://keepachangelog.com/en/1.0.0/),
and this project adheres to [Semantic Versioning](https://semver.org/spec/v2.0.0.html).

## [Unreleased]

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

[unreleased]: https://github.com/octo-youcef/mapper/compare/v0.1.2...HEAD
[0.1.2]: https://github.com/octo-youcef/mapper/compare/v0.1.1...v0.1.2
[0.1.1]: https://github.com/octo-youcef/mapper/compare/v0.1.0...v0.1.1
[0.1.0]: https://github.com/octo-youcef/mapper/releases/tag/v0.1.0
