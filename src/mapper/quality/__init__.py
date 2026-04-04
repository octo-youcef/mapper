"""Quality rule system for code quality enforcement.

This module provides built-in quality rules that can be run via CLI commands
to enforce code quality standards without writing Cypher queries.

Quality rules are pass/fail checks with configurable thresholds, designed for
CI/CD integration with exit codes (0 = pass, 1 = fail).
"""

__all__: list[str] = []
