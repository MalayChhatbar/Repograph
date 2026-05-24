# RepoGraph Architecture

## Product intent

RepoGraph helps developers answer:

- What is this repository?
- What should I read first?
- What depends on this file?
- Which tests should I run?
- Where are the risky areas?

## Backend

- `repograph.cli`: user-facing commands
- `repograph.api`: HTTP surface for the React app
- `repograph.core`: indexing and analysis
- `repograph.storage`: SQLite schema and queries
- `repograph.parsers`: language-specific extraction

## Frontend

The frontend is a React app that behaves like a repository workbench with:

- overview
- search
- graph neighborhood
- impact details
- cycle viewer
- explain panel

## Schema outline

- `files`: indexed source files
- `symbols`: extracted classes/functions
- `imports`: file dependencies
- `calls`: symbol edges
- `routes`: framework routes
- `test_links`: related tests with confidence

