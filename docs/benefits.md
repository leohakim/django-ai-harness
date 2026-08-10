# Benefits

## For solo developers

- Stop re-deciding tooling on every new repo.
- Inherit battle-tested cookiecutter-django production patterns, then layer DX extras from the harness.
- Catch migration and environment drift early (`django-linear-migrations`, `django-version-checks`, pending-migration tests).

## For teams

- Shared architecture vocabulary (services / selectors / thin APIs).
- Agents and humans follow the same `AGENTS.md` contract.
- Practices evolve in **one** open-source repo instead of drifting across private apps.

## For AI agents

- Scaffolding is scripted (`django-dx-scaffold`), not improvised.
- Architecture skill (`django-hacksoft`) reduces logic-in-views regressions.
- Review skill (`django-dx-review`) gives a repeatable audit checklist.

## Compared to “only cookiecutter-django”

cookiecutter-django is excellent. The harness adds:

- Explicit agent instructions and Cursor skills
- Extra DX packages and patterns from the *Boost Your Django DX* tradition (modernized)
- HackSoft enforcement as a first-class contract
- A maintained mapping of practices → files (`knowledge/book-map.md`)
- CI that regenerates/validates a golden example against upstream

## Compared to “only a personal notes repo”

Notes do not apply themselves. The **overlay** mutates a real project tree idempotently, so knowledge becomes runnable configuration.
