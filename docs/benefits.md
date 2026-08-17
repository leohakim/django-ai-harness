# Benefits

## For solo developers

- Stop re-deciding tooling on every new repository.
- Inherit cookiecutter-django's production patterns, then layer the harness's DX on top.
- Catch environment and migration drift early, through system checks that actually run in
  CI rather than only in a local shell.
- Upgrade an old project with one command instead of manually diffing it against a newer
  template.

## For teams

- A shared architecture vocabulary: services, selectors, thin interfaces.
- Agents and humans follow the same `AGENTS.md` contract, so review comments stop
  repeating the same three points.
- Practices evolve in one open-source repository instead of drifting across private
  applications.
- `apply --check` in CI turns "we should update our boilerplate someday" into a build
  signal.

## For AI agents

- Scaffolding is a command, not an improvisation.
- The architecture skill removes the most common regression: business logic sliding into
  views and serializers.
- The review skill gives a repeatable audit instead of a vague "looks good".

## Compared to using cookiecutter-django alone

cookiecutter-django is excellent, and the harness does not replace it. It adds:

- An agent contract and portable Agent Skills
- DX packages and patterns from the *Boost Your Django DX* tradition, modernised
- HackSoft architecture as a first-class, enforced contract
- An upgrade path: `apply` propagates improvements into projects generated months ago
- A golden example regenerated in CI, so upstream drift is a failing build rather than a
  discovery

## Compared to a personal notes repository

Notes do not apply themselves. The overlay mutates a real project tree, idempotently, so
knowledge becomes runnable configuration — and stays reviewable, because every change it
makes is either a marker block or a tracked file.

## What it costs

Worth stating plainly:

- One more dependency in your bootstrap path.
- The pinned cookiecutter-django commit lags upstream by design; you adopt upstream
  changes when the harness has validated them.
- The opinions are opinions. If your team disagrees with services and selectors, the
  architecture half of this is friction rather than help — though the DX half still
  stands on its own.
