# App skeleton (HackSoft Django Styleguide)

Copy this layout into every new app. It is a reference, not an installed package.

```text
<app>/
├── models.py       # data + simple non-relational invariants
├── services.py     # writes, workflows, side effects
├── selectors.py    # reads, filtering, visibility
├── apis/           # one operation per class, thin
└── tests/
    ├── services/
    ├── selectors/
    └── apis/
```

Rules of thumb:

- If it writes or orchestrates, it is a service.
- If it reads or filters, it is a selector.
- If a rule can be expressed as a database constraint, prefer the constraint.
- Interfaces (APIs, forms, admin, tasks, management commands) call services and
  selectors; they never own business rules.
