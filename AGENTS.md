
# CatatCuan AI — Development Rules

## Project Principle

CatatCuan AI is an existing working application.

Preserve working functionality and improve the application incrementally.

Do NOT rewrite or rebuild the entire application unless explicitly instructed.

---

## Core Development Rules

1. Work on ONE issue or task at a time.
2. Inspect the relevant existing code before making changes.
3. Prefer the smallest possible change that solves the requested task.
4. Do not modify unrelated files.
5. Do not perform opportunistic refactoring.
6. Preserve existing working behavior unless the task explicitly requires changing it.
7. Never replace working functionality merely because another implementation looks cleaner.
8. Do not introduce new features unless explicitly requested.
9. Do not change dependencies unless necessary for the requested task.
10. Never expose API keys, secrets, credentials, or environment values.

---

## Architecture Boundaries

Maintain the existing project structure whenever possible:

- `app.py` — application orchestration
- `components/` — UI components
- `services/` — external services and AI integrations
- `styles/` — application styling
- `utils/` — shared utilities
- `config.py` — application configuration

Do not reorganize this architecture unless explicitly requested.

---

## UI / UX Tasks

When the task concerns UI or UX:

- Focus only on presentation, layout, responsiveness, accessibility, and interaction required by the task.
- Preserve application logic.
- Preserve financial calculations.
- Preserve transaction processing.
- Preserve authentication behavior.
- Preserve AI behavior.
- Prefer editing `components/` and `styles/` rather than business logic.

UI redesign must NOT automatically trigger backend refactoring.

---

## Protected Areas

Unless the task explicitly requires it, DO NOT modify:

- `services/ai_service.py`
- `services/supabase_service.py`
- authentication logic
- AI prompts or AI model configuration
- transaction schema
- transaction validation rules
- financial calculation logic
- API configuration
- environment/secrets handling

If a requested task appears to require modifying one of these areas, explain why before changing it.

---

## Transaction Safety

The existing transaction data structure is a compatibility boundary.

Do not rename, remove, or reinterpret transaction fields without explicit approval.

Changes to transaction parsing, validation, storage, or calculations must be treated as separate tasks from UI work.

---

## AI Safety

Do not modify AI prompts, providers, models, parsing behavior, or API handling during unrelated tasks.

AI-related changes must be isolated and reviewed separately.

---

## Authentication & Database Safety

Do not modify Supabase configuration, authentication flows, database behavior, or user handling during unrelated tasks.

Never hardcode credentials.

---

## Change Discipline

Before editing:

1. Understand the requested task.
2. Inspect the relevant files.
3. Identify the minimum files that need modification.
4. Avoid touching unrelated code.

During editing:

1. Keep the diff small.
2. Preserve naming conventions where reasonable.
3. Avoid combining refactoring with feature work.
4. Avoid changing multiple architectural layers unless necessary.

After editing:

1. Review the diff.
2. Run available tests or checks relevant to the change.
3. Check for syntax/import errors.
4. Report which files were changed.
5. Explain what changed.
6. Report tests/checks performed.
7. Mention any remaining risks or assumptions.

---

## Stop Conditions

Stop and explain before proceeding if:

- the task requires a major architecture rewrite;
- the task would change the transaction schema;
- the task would modify both UI and core financial logic;
- the task requires replacing the AI provider;
- the task requires destructive database changes;
- required behavior is ambiguous and different interpretations could materially affect the application.

---

## Definition of Done

A task is complete only when:

- the requested scope is implemented;
- unrelated functionality has not intentionally changed;
- relevant checks have been performed;
- the resulting diff remains focused;
- changed files and test results are reported.

One successful small change is preferred over one large risky rewrite.
