# For humans

## Day to day

Treat django-ai-harness as a standard library of process rather than a template you fork.

```bash
uvx django-ai-harness new ~/Projects/thing "Thing"   # start something
uvx django-ai-harness apply .                        # pull in harness improvements
uvx django-ai-harness info                           # see what you would get
```

Read `knowledge/` when you want to know *why* a tool is there rather than how to use it;
the package's own documentation is always the better how-to.

## Inside a generated project

It is an ordinary cookiecutter-django project plus a handful of harness files:

- Follow the project's own README for Docker and deployment.
- Follow `AGENTS.md` for architecture — it applies to you as much as to an agent.
- Copy `harness_templates/app_skeleton/` when starting a new app.
- Seed local data with `python manage.py seed_database` instead of hand-crafted fixtures.

Re-apply the overlay after a harness release:

```bash
uvx django-ai-harness apply .
uv sync
```

Files you edited are reported, never overwritten. See [updating.md](updating.md).

## With coding agents

Generated projects carry an `AGENTS.md` that Claude Code, Cursor, Codex and Copilot read
by convention, so your architecture rules stop being something you re-type into every
prompt.

For deeper enforcement, install the Agent Skills from [`skills/`](../skills) into your
agent's skills directory, or point the agent at this repository:

| Skill | When |
|---|---|
| `django-dx-scaffold` | Starting a project |
| `django-hacksoft` | Writing or reviewing feature code |
| `django-dx-review` | Before opening a pull request |

## Language

The wizard and CLI output are available in English and Spanish:

```bash
uvx django-ai-harness --lang es wizard
export DJANGO_AI_HARNESS_LANG=es
```

Error messages from the library stay in English so that tracebacks and bug reports are
readable by every contributor.

## Contributing back

The best contributions are practices you already validated on a real project. See
[CONTRIBUTING.md](../CONTRIBUTING.md); prefer small pull requests that update
`knowledge/`, the overlay and the docs together.
