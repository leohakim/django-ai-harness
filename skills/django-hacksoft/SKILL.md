---
name: django-hacksoft
description: Use when working on Django projects or reviewing Django code where HackSoft Django Styleguide architecture must be enforced, especially services, selectors, DRF APIs, serializers, models, settings, errors, tests, Celery tasks, URLs, or moving business logic out of views, serializers, forms, signals, managers, querysets, and model save methods.
---

# Django Styleguide

## Core Contract

Apply the HackSoft Django Styleguide in strict mode for django-ai-harness projects (and user Django apps using this harness).

Before implementing or reviewing Django code, read `references/hacksoft-django-styleguide.md`.

The upstream source is [HackSoftware/Django-Styleguide](https://github.com/HackSoftware/Django-Styleguide). The local reference is an operative summary checked on 2026-07-07. If the user asks for the latest upstream version, verify the repository first.

## Strict Mode

The upstream guide says teams may cherry-pick. This user's instruction overrides that: enforce the guide by default and do not silently introduce code that violates it.

If an existing project already diverges from the styleguide:
- Follow established compatibility only where needed to avoid breaking current behavior.
- Put new or changed business logic in the styleguide layer.
- Surface the divergence in the final answer or review finding.
- Ask only when a required exception would materially affect the architecture.

## Workflow

1. Inspect the app structure and identify the layer being changed: model, service, selector, API/view, serializer/form, URL, task, settings, or test.
2. Classify the behavior:
   - Writes, workflows, side effects, cross-model rules: service.
   - Reads, filtering, visibility, query optimization: selector.
   - Simple non-relational invariants: model `clean` or database constraints.
   - Simple non-relational derived values: model property or method.
   - HTTP input/output: API with nested serializers.
   - Async interface: Celery task that fetches data and calls a service.
3. Move misplaced behavior to the correct layer before adding more logic.
4. Keep interfaces thin: APIs, serializers, forms, tasks, admin hooks, and management commands call services/selectors instead of owning business rules.
5. Add or update tests at the layer where the behavior lives.

## Non-Negotiables

- Business logic belongs in services, selectors, simple model validation, or simple model properties/methods.
- Business logic does not belong in APIs/views, serializers/forms, template tags, model `save`, signals, or custom managers/querysets.
- Services write or orchestrate behavior. Use keyword-only arguments for multiple inputs, type annotations, `full_clean()` before saving model instances, and `transaction.atomic` around multi-step writes.
- Selectors read data. They can return querysets, iterables, objects, IDs, or shaped data, but they must not mutate state.
- APIs expose one operation per class/function. Prefer `APIView` or `GenericAPIView` over DRF's high-level generic views when those abstractions would hide business flow.
- DRF serializers are interface-level validation and representation tools. Prefer nested `InputSerializer`, `OutputSerializer`, and `FilterSerializer`; avoid broad shared serializers unless the project has a strong reason.
- Celery tasks are interfaces to core logic. They fetch the minimal data, import and call the service inside the task body, and put task retry/failure handling in the task.
- Side effects that depend on committed database rows run with `transaction.on_commit`.

## Review Checklist

Use this checklist for every Django implementation or review:

- Is each business rule in a service, selector, or simple model method/validation rather than an interface layer?
- Are writes and side effects covered by service tests?
- Are query and visibility rules in selectors and covered by selector tests?
- Do APIs only validate request data, fetch objects consistently, call services/selectors, and serialize responses?
- Are model `clean`, properties, and methods limited to simple non-relational logic?
- Are database constraints used where the database can enforce the invariant?
- Are Celery tasks thin and named/imported to avoid circular imports?
- Are errors shaped consistently through a project-level exception strategy?
- Do tests mirror the module structure and name the thing under test?
- Did you preserve existing compatibility without expanding non-styleguide patterns?
