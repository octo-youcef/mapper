# User Journey Documentation

This directory contains user-focused workflow documentation for Mapper.

## Contents

1. **[Initial Setup](01-initial-setup.md)**: First-time setup with Neo4j and configuration
2. **[Configuration Management](02-configuration-management.md)**: Managing global and local settings
3. **[Analyzing a Codebase](03-analyzing-codebase.md)**: Analyze Python projects and store code graph in Neo4j
4. **[Storing Code in Graph Database](04-storing-code-graph.md)**: Store analyzed code in Neo4j and navigate to the graph
5. **[Analyzing and Querying Code](05-analyzing-querying-code.md)**: Query stored code to understand architecture, dependencies, and find issues (advanced)
6. **[Enforcing Code Quality Rules](06-enforcing-code-quality.md)**: Define and enforce code quality rules using graph queries
7. **[Checking System Status](07-checking-status.md)**: Verify Mapper configuration and Neo4j connectivity
8. **[Detecting Code Risks](08-detecting-code-risks.md)**: Run CLI queries to identify risks without Neo4j knowledge (recommended starting point)
9. **[Querying Structured Metadata](09-querying-structured-metadata.md)**: Write precise queries using structured parameter and decorator data (v0.8.0+)
10. **[Running Quality Rules](10-quality-rules.md)**: Enforce code quality standards with built-in pass/fail checks (v0.8.1+)
11. **Exporting Data**: Exporting analysis results _(coming soon)_

## Documentation Format

Each user journey follows this structure:

1. **Prerequisites**: What you need before starting
2. **Steps**: Step-by-step instructions with examples
3. **Outcomes**: What to expect at the end
4. **Troubleshooting**: Common issues and solutions

## Documentation Standards

- Use clear, non-technical language where possible
- Include screenshots or terminal output examples
- Cross-reference related journeys
- Update this index when adding new documents
