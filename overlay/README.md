# overlay/

The overlay itself lives in [`src/django_ai_harness/overlay.py`](../src/django_ai_harness/overlay.py)
so that it ships in the published wheel. Its module docstring states the design contract.

`apply.py` in this directory is a compatibility shim: it keeps
`python overlay/apply.py /path/to/project` working from a source checkout, which is the
path documented by projects generated with version 1.x. The `--harness-root` option those
projects pass is accepted and ignored — templates now travel inside the package.

Prefer the installed command:

```bash
uvx django-ai-harness apply /path/to/project
uvx django-ai-harness apply /path/to/project --check
```

Documentation: [../docs/overlay.md](../docs/overlay.md).
