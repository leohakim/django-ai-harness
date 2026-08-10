# HackSoft Django Styleguide Reference

Source: [HackSoftware/Django-Styleguide](https://github.com/HackSoftware/Django-Styleguide). Checked 2026-07-07.

Use this reference as the local operating contract for strict HackSoft-style Django architecture. It paraphrases the upstream repository and adapts it to the user's requirement: follow the styleguide by default.

## Architectural Baseline

Separate application core from interfaces.

The application core contains domain behavior:
- Services for writes, workflows, state changes, side effects, and orchestration.
- Selectors for reads, filtering, visibility, and query construction.
- Model `clean` for simple validation over the model's own non-relational fields.
- Model properties/methods for simple derived values based on the model's own non-relational fields.

Interfaces translate external input/output into calls to the core:
- APIs and views.
- Serializers and forms.
- Admin hooks.
- Management commands.
- Celery tasks.
- URL routing.

Do not use APIs, views, serializers, forms, template tags, signals, custom managers/querysets, or model `save` as the primary home for business logic.

## Decision Table

| Behavior | Put It In |
|---|---|
| Create/update/delete model data | Service |
| Multi-step workflow | Service, often class-based if the flow has named steps |
| Cross-model validation | Service |
| External call, email, notification, task scheduling | Service, with async trigger via task if needed |
| Query construction, visibility, filtering | Selector |
| Read-only aggregate or listing | Selector |
| Simple invariant over the same model fields | Model `clean` or database constraint |
| Invariant the database can enforce | Database constraint |
| Simple derived value from same model fields | Model property |
| Derived value requiring arguments | Model method |
| Derived value spanning relations or likely causing N+1 queries | Selector or serializer function |
| HTTP request validation | API nested `InputSerializer` or `FilterSerializer` |
| HTTP response shape | API nested `OutputSerializer` or serializer function |
| Celery retry/failure behavior | Task |
| Actual business action triggered by Celery | Service |

## Cookie Cutter

Prefer starting new projects from a Django cookiecutter or project template that already encodes the architecture: split settings, clear app layout, test setup, formatting, linting, and environment handling.

Do not treat the template as the architecture. The architecture is still enforced by the core/interface split, service/selector placement, and thin APIs.

When working in an existing project, adapt the file placement to the project layout while preserving the styleguide responsibilities.

## Models

Use models primarily for data structure and simple local behavior.

### BaseModel

Prefer a shared abstract base model when the project needs fields like `created_at` and `updated_at`. Keep it simple and reusable.

### Validation

Use model `clean` when:
- The rule depends only on the model's own non-relational fields.
- The rule is simple and easy to understand locally.

Move validation to services when:
- It spans relations.
- It needs additional queries.
- It coordinates multiple objects.
- It is complex enough to obscure the model.

Call `full_clean()` in services before `save()` when creating or updating model instances directly.

Use database constraints when the database can enforce the invariant. Prefer constraints for integrity that must hold regardless of insertion path.

### Properties And Methods

Use `@property` for simple derived values from non-relational fields.

Use model methods when the derived value needs arguments or when setting one field must consistently set another derived field.

Move the logic out of the model when it spans relationships, performs queries, risks N+1 behavior when serialized, or grows beyond simple local calculation.

### Model Tests

Test models only when they contain additional behavior: validation, properties, or methods. For pure local validation, avoid unnecessary database writes and call `full_clean()` directly.

## Services

Services are the default home for business logic. They can access the database, call selectors, call other services, integrate with external systems, and schedule side effects.

Default service shape:
- Live in `services.py` for small apps.
- Split into `services/` submodules when the app grows by domain.
- Use function services for simple operations.
- Use class services for namespacing, shared private helpers, or flows with multiple named actions.
- Use keyword-only arguments when there are multiple inputs.
- Add type annotations for arguments and return values.
- Use `transaction.atomic` around multi-step writes.
- Call `full_clean()` before saving model instances.
- Return the domain object or meaningful result.

Preferred naming is action-oriented and greppable, commonly `<entity>_<action>`, such as `user_create`, `user_update`, `course_publish`, or `payment_refund`.

Services may call other services. This is expected when a workflow needs to keep the business flow traceable in one place.

Use `transaction.on_commit` for async tasks or other side effects that depend on committed database state.

### Updating Models

For repetitive updates, use a generic update helper only for direct field assignment. Keep side-effect fields and domain-specific consequences in the concrete service.

When updating, prefer passing only changed fields to `save(update_fields=...)` when the project pattern supports it.

## Selectors

Selectors are the read side of the application core.

Use selectors for:
- Lists and detail fetches.
- Visibility rules.
- Permission-aware data access.
- Filtering.
- Query optimization.
- Data needed by APIs, services, tasks, and admin screens.

Selectors can return querysets, model instances, lists, IDs, dictionaries, or typed results. Pick the return shape that best serves the caller and keep it consistent within the app.

Selectors should not mutate state or trigger side effects.

Filtering belongs in selectors. APIs may validate and normalize filter parameters, but selectors build the actual query. `django-filter` is a good fit when the project uses it.

## APIs And Serializers

APIs are interface code. They validate input, call the application core, and serialize output.

Rules:
- One API per operation. CRUD usually becomes separate list, detail, create, and update APIs.
- Prefer class-based APIs by default.
- Prefer `APIView` or `GenericAPIView` over high-level generic DRF views when generic classes would hide business flow in serializers.
- Do not put business logic in APIs.
- Keep object fetching consistent across the project.
- Use services for writes and selectors for reads.

Naming convention: `<Thing><Action>Api`, such as `UserCreateApi`, `CourseListApi`, or `FileUploadStartApi`.

### Serializers

Use serializers as API-local interface tools:
- `InputSerializer` for request body data.
- `FilterSerializer` for query parameters.
- `OutputSerializer` for response data.

Prefer nesting these serializers inside the API class. This keeps the API contract local and reduces accidental reuse.

Prefer `serializers.Serializer` over `ModelSerializer` by default. Use `ModelSerializer` only when the project has a clear reason and the behavior remains explicit.

Reuse serializers sparingly. Shared serializers can create accidental coupling when one API's contract changes.

For nested serializer fields, use an `inline_serializer` style utility if the project has one.

### List APIs

For list APIs:
- Validate filters in the API.
- Pass validated filters to a selector.
- Let the selector construct/filter the queryset.
- Use a pagination helper when using DRF pagination with simple `APIView`.

### Detail, Create, Update

Detail APIs call selectors and return `OutputSerializer` data.

Create APIs validate with `InputSerializer`, call a create service, and return a response suitable for the operation.

Update APIs validate partial inputs, call an update service, and avoid embedding update rules in the serializer.

### Advanced Serialization

When output is complex or needs query optimization, use serializer functions in `serializers.py`. A serializer function may refetch data with `select_related`/`prefetch_related`, build in-memory caches, set temporary computed attributes, and return response-ready data.

Do not force all serialization optimizations into selectors when they only exist to shape an API response.

## URLs

Organize URLs the way APIs are organized: one URL per operation.

For larger domains, split related routes into domain pattern lists or nested route modules. Choose a structure that keeps the URL tree clear and reduces conflicts in large `urls.py` files.

## Settings

Prefer a split settings structure:
- `config/django/base.py`, `local.py`, `production.py`, `test.py` for Django settings modules.
- `config/settings/` for integrations and non-core settings such as Celery, CORS, Sentry, sessions, etc.
- `config/env.py` as the shared environment reader, commonly with `django-environ`.

Everything should be importable from `base.py`. Avoid settings that only exist in production modules; use environment toggles for production-only behavior.

For integrations:
- Put integration settings in their own module.
- Gate optional integrations with an explicit boolean or empty setting.
- Fail on missing required environment values only when the integration is enabled.

Use `.env` for local development if desired. Do not commit secrets. Provide `.env.example` with empty values so developers know which variables exist.

Prefix environment variables consistently. Prefix Django-specific variables with `DJANGO_` when that convention is used; do not mix conventions casually.

## Errors And Exceptions

Define the API error shape early.

DRF's default exception output can vary across validation errors, not-found errors, and permission errors. Django's `ValidationError` is not handled by DRF by default unless the project maps it.

Use a project-level exception handler when building APIs. At minimum, decide how to handle:
- Django `ValidationError`.
- DRF `ValidationError`.
- `Http404`.
- `PermissionDenied`.
- Project/domain exceptions such as `ApplicationError`.

HackSoft's proposed direction is:
- Business logic may raise project-specific application exceptions.
- Serializer and model validation errors remain validation errors.
- The API layer exposes a consistent shape such as `{"message": "...", "extra": {...}}`.
- Unexpected server errors must not be silenced; let them surface and be reported.

## Tests

Split tests by the code layer they verify:
- `tests/models/test_<model_or_behavior>.py`
- `tests/selectors/test_<selector>.py`
- `tests/services/test_<service>.py`
- `tests/apis/test_<api_or_operation>.py`

Name test classes after the thing under test, for example `UserCreateTests` or `AVeryNeatServiceTests`.

Service tests should cover business logic exhaustively and usually hit the database. Mock async task calls and calls outside the project boundary.

Selector tests should cover query, filtering, visibility, and permission rules.

API tests should verify interface behavior: request validation, status codes, response shape, auth/permission integration, and that the API calls the correct core behavior through real code where practical.

Use factories, fakes, service setup helpers, or direct model creation based on what keeps the test readable and maintainable. Match the project's existing test style when adding tests.

## Celery

Treat Celery as another interface to the application core.

Task rules:
- Tasks fetch the required data.
- Tasks import and call services inside the task body to avoid circular imports.
- Tasks do not own business logic.
- Retry and failure handling belong in the task.
- Failure callbacks can call services to record failed state.

When triggering tasks from services:
- Import the task at module level with a `_task` suffix if it shares a name with the service.
- Trigger task dispatch in `transaction.on_commit` when the task depends on committed database state.

Keep tasks in `tasks.py` for small apps. Split into `tasks/` submodules when an app grows, and re-export/import in `tasks/__init__.py` so Celery autodiscovery still works.

For periodic tasks, keep definitions centralized in a management command such as `setup_periodic_tasks` when the project uses `django-celery-beat`. Prefer readable cron documentation, including a `crontab.guru` link for non-trivial schedules.

## Common Violations To Fix

- Serializer `.create()` or `.update()` owns business rules: move to service.
- Viewset action performs a workflow: replace with a thin API that calls a service.
- Model `save()` mutates unrelated fields or calls external systems: move to service/model method as appropriate.
- Signal implements domain flow: replace with explicit service orchestration unless it is true decoupled glue like cache invalidation.
- Custom manager/queryset hides domain behavior: keep query convenience there only if it remains a model-query interface; move domain workflows to services/selectors.
- Celery task contains the real business operation: move operation to service and call it from the task.
- API duplicates filtering logic: move query construction to selector and keep API filter validation only.

## Developer Experience

Use type annotations for service inputs and outputs, selector inputs and outputs, serializer helper functions, and utilities where they clarify contracts. Do not force typing into places where the framework makes it noisy without improving correctness.

Keep Django code easy to inspect:
- Names should reveal the operation and layer.
- Files should be small enough to scan.
- Module boundaries should match domain behavior.
- Tests should show how the layer is meant to be used.

When a project uses `mypy`, align service and selector signatures with the configured Django typing setup. Do not introduce typing patterns that fight the local configuration.
