# Skill: update-llm-txt

> Update the `llm.txt` project context file after implementing changes to the codebase.

## When to Use

Run this skill **after completing any implementation task** that changes the project's structure, APIs, models, dependencies, configuration, or architecture. This keeps `llm.txt` accurate for future agentic coding sessions.

**Trigger examples:**
- Added a new domain model, use case, repository, or adapter
- Added/removed dependencies in `pyproject.toml`
- Added/changed API endpoints or schemas
- Added/changed chatbot tools
- Modified the DI wiring in `dependencies.py`
- Added new configuration settings
- Changed database schema or seed data
- Added/changed tests
- Modified Docker services
- Changed architecture patterns or conventions
- Deleted or deprecated files/code

## Steps

### 1. Identify What Changed

Determine which sections of `llm.txt` are affected. The file has these sections:

| Section | Update When... |
|---------|----------------|
| **Tech Stack** | Python version, libraries, or version constraints change |
| **Quick Commands** | New commands added, existing ones change |
| **The Rules (ALWAYS/NEVER)** | Conventions, patterns, or anti-patterns change |
| **Architecture (tree)** | Files/directories added, moved, or removed |
| **Critical Paths** | Key files or logic locations change |
| **Domain Models** | Dataclasses, enums, value objects added/changed in `src/core/domain/models.py` |
| **Domain Exceptions** | Exceptions added/changed in `src/core/domain/exceptions.py` — also update HTTP status mapping |
| **Ports** | Use case or repository Protocols added/changed |
| **REST API** | Routes added/changed in `routes.py` |
| **LLM Chatbot** | Tools, ChatDeps, system prompt changed in `chatbot.py` |
| **Persistence** | DB models, repos, database.py changed |
| **DI** | Factory functions added/changed in `dependencies.py` |
| **Configuration** | Settings changed in `settings.py` |
| **Docker Services** | `docker-compose.yml`, Dockerfiles changed |
| **Tests** | Test files added/changed, counts updated |
| **Gotchas & Known Limitations** | New caveats, workarounds, or tech debt discovered |
| **Do Not Touch** | Files deleted, code removed, or stale references found |

### 2. Read the Current llm.txt

```
Read llm.txt from the project root to understand its current state.
```

### 3. Read the Changed Source Files

Read the actual source files that were modified to get accurate:
- Class/function signatures and method names
- Import paths
- Configuration values and defaults
- Table structures
- Test counts

**Do NOT guess or rely on memory.** Always read the files to get exact details.

### 4. Update the Affected Sections

Edit `llm.txt` to reflect the changes. Follow these formatting rules:

- **High density, markdown-lite** — tables > paragraphs, code blocks for signatures
- **Architecture tree**: ASCII tree of `src/` with inline comments
- **Domain Models**: Class name + key fields in Python pseudocode
- **Ports tables**: Protocol name → method signatures
- **API table**: Method | Path | Status | Description
- **DI listing**: function name → return type (one per line)
- **Test table**: File | Count
- **Do Not Touch table**: Item | Status | Notes

### 5. Manage the "Do Not Touch" Section

This is critical for preventing hallucinated imports:

- **When deleting a file**: Add it to "Do Not Touch" with status "Deleted" and reason
- **When removing a class/function**: Add it with status "Removed" and what replaced it (if anything)
- **When a reference exists but code doesn't**: Add with status "Never existed" or "Not yet created"
- **Periodically prune**: Remove entries that are very old and unlikely to be hallucinated

### 6. Update "Gotchas & Known Limitations"

- **When you discover a workaround**: Document it (e.g., "OLLAMA_BASE_URL must end with /v1")
- **When you fix a limitation**: Remove it from the list
- **When you add tech debt**: Document what's missing or unfinished

### 7. Verify Accuracy

After editing, scan the updated `llm.txt` to ensure:
- No stale references to removed code
- New additions are documented
- File paths are correct
- Method signatures match actual code
- Test counts are updated (run `uv run pytest tests/unit --collect-only -q` if unsure)
- Architecture tree reflects current file structure
- "Do Not Touch" doesn't list things that were re-added

## Important Rules

- **Be precise**: `llm.txt` is consumed by LLMs for context. Wrong information is worse than no information.
- **Be concise**: Tables and code blocks over prose. Every line should earn its token cost.
- **Read before writing**: Always read the actual source files. Don't rely on what you think is there.
- **Preserve section ordering**: Add new sections at logical positions, don't shuffle.
- **Update test counts accurately**: Read test files or run `--collect-only` to get real numbers.
- **"Do Not Touch" is safety-critical**: It prevents agents from importing deleted code or recreating removed files.
