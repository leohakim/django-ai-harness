"""Guided project wizard (Textual TUI).

The wizard is a thin front-end over :mod:`django_ai_harness.scaffold`: it collects the
same answers the ``new`` subcommand takes as flags, explaining each trade-off, then calls
the exact same code path. Anything the wizard can do is scriptable.
"""

from __future__ import annotations

from pathlib import Path
from typing import ClassVar

from textual.app import App
from textual.app import ComposeResult
from textual.binding import Binding
from textual.containers import Horizontal
from textual.containers import Vertical
from textual.containers import VerticalScroll
from textual.reactive import reactive
from textual.screen import ModalScreen
from textual.screen import Screen
from textual.widgets import Button
from textual.widgets import Footer
from textual.widgets import Header
from textual.widgets import Input
from textual.widgets import Label
from textual.widgets import Markdown
from textual.widgets import OptionList
from textual.widgets import ProgressBar
from textual.widgets import RichLog
from textual.widgets import Static
from textual.widgets.option_list import Option

from django_ai_harness.i18n import Translator
from django_ai_harness.scaffold import ProjectConfig
from django_ai_harness.scaffold import next_steps
from django_ai_harness.scaffold import sanitize_slug
from django_ai_harness.scaffold import scaffold
from django_ai_harness.wizard.steps import Choice
from django_ai_harness.wizard.steps import Decision
from django_ai_harness.wizard.steps import visible_decisions

__all__ = ["WizardApp", "run"]


class WizardApp(App[None]):
    """Collects project identity and one decision per screen, then generates."""

    TITLE = "django-ai-harness"
    CSS_PATH = str(Path(__file__).with_name("wizard.tcss"))
    BINDINGS: ClassVar[list[Binding]] = [Binding("q", "quit", "Quit")]

    def __init__(self, *, language: str = "en", target: Path | None = None) -> None:
        super().__init__()
        self.translate = Translator(language)
        self.language = self.translate.language
        self.initial_target = target
        self.identity: dict[str, str] = {}
        self.answers: dict[str, str] = {}
        self.decision_index = 0
        self.SUB_TITLE = self.translate("wizard.subtitle")

    def on_mount(self) -> None:
        self.push_screen(WelcomeScreen())

    # Convenience so screens can write `self.wizard.translate(...)`.
    @property
    def wizard(self) -> WizardApp:  # pragma: no cover - trivial
        return self


class _WizardScreen(Screen[None]):
    """Base screen with typed access to the app and its translator."""

    @property
    def wizard(self) -> WizardApp:
        app = self.app
        if not isinstance(app, WizardApp):  # pragma: no cover - defensive
            msg = "screen mounted outside WizardApp"
            raise TypeError(msg)
        return app

    @property
    def t(self) -> Translator:
        return self.wizard.translate


class WelcomeScreen(_WizardScreen):
    BINDINGS: ClassVar[list[Binding]] = [
        Binding("enter", "start", "Start", show=True, priority=True),
    ]

    _INTRO: ClassVar[dict[str, str]] = {
        "en": """This wizard walks you through a new Django project **one decision at a time**.

For every choice you will see:

- **Adds** — what you gain by enabling it
- **Leaves out** — what you give up
- **Implication** — what it means day to day

At the end it runs **cookiecutter-django** at a pinned commit and applies the
**django-ai-harness overlay**: DX defaults, HackSoft architecture, and an agent contract.

`Enter` continue · `q` quit · arrow keys to move between options.
""",
        "es": """Este asistente te guía por un proyecto Django nuevo **una decisión a la vez**.

Para cada elección vas a ver:

- **Agrega** — qué ganás al activarlo
- **Deja fuera** — a qué renunciás
- **Implicancia** — qué significa en el día a día

Al final ejecuta **cookiecutter-django** en un commit pineado y aplica el
**overlay de django-ai-harness**: defaults de DX, arquitectura HackSoft y un contrato
para agentes.

`Enter` continuar · `q` salir · flechas para moverte entre opciones.
""",
    }

    def compose(self) -> ComposeResult:
        yield Header(show_clock=False)
        with Vertical(id="panel"):
            yield Label("django-ai-harness", id="brand")
            yield Label(self.t("wizard.title"), id="tagline")
            yield Markdown(self.t.pick(self._INTRO))
            yield Button(self.t("wizard.button.next"), variant="primary", id="start")
        yield Footer()

    def on_mount(self) -> None:
        self.set_focus(self.query_one("#start", Button))

    def on_button_pressed(self, event: Button.Pressed) -> None:
        if event.button.id == "start":
            self.action_start()

    def action_start(self) -> None:
        self.app.push_screen(IdentityScreen())


class IdentityScreen(_WizardScreen):
    def compose(self) -> ComposeResult:
        yield Header()
        with VerticalScroll(id="panel"):
            yield Label(f"1 · {self.t('wizard.identity.title')}", classes="step-title")
            yield Markdown(self.t("wizard.identity.help"))
            yield Label(self.t("wizard.field.project_name"))
            yield Input(placeholder="My Shop", id="project_name")
            yield Label(self.t("wizard.field.target"))
            yield Input(
                value=str(self.wizard.initial_target or ""),
                placeholder=str(Path.home() / "Projects" / "my_shop"),
                id="target",
            )
            yield Label(self.t("wizard.field.author"))
            yield Input(value="django-ai-harness", id="author_name")
            yield Label(self.t("wizard.field.domain"))
            yield Input(value="example.com", id="domain_name")
            yield Static("", id="identity_error", classes="error")
            with Horizontal(classes="actions"):
                yield Button(self.t("wizard.button.back"), id="back")
                yield Button(self.t("wizard.button.next"), variant="primary", id="next")
        yield Footer()

    def on_mount(self) -> None:
        self.set_focus(self.query_one("#project_name", Input))

    def on_button_pressed(self, event: Button.Pressed) -> None:
        if event.button.id == "back":
            self.app.pop_screen()
        elif event.button.id == "next":
            self._submit()

    def _value(self, widget_id: str, fallback: str = "") -> str:
        return self.query_one(f"#{widget_id}", Input).value.strip() or fallback

    def _submit(self) -> None:
        error = self.query_one("#identity_error", Static)
        name = self._value("project_name")
        target_raw = self._value("target")
        domain = self._value("domain_name", "example.com")

        missing = {
            "en": "Project name and target directory are both required.",
            "es": "El nombre del proyecto y la carpeta destino son obligatorios.",
        }
        exists = {
            "en": "That path already exists: {path}",
            "es": "Esa ruta ya existe: {path}",
        }
        if not name or not target_raw:
            error.update(self.t.pick(missing))
            return

        target = Path(target_raw).expanduser()
        try:
            slug = sanitize_slug(target.name)
        except ValueError as exc:
            error.update(str(exc))
            return
        if target.exists():
            error.update(self.t.pick(exists).format(path=target))
            return

        self.wizard.identity = {
            "project_name": name,
            "target": str(target),
            "author_name": self._value("author_name", "django-ai-harness"),
            "domain_name": domain,
            "email": f"hello@{domain}",
            "project_slug": slug,
        }
        self.wizard.answers = {}
        self.wizard.decision_index = 0
        self.app.push_screen(DecisionScreen())


class DecisionScreen(_WizardScreen):
    selected_value: reactive[str | None] = reactive(None)

    def compose(self) -> ComposeResult:
        yield Header()
        with Vertical(id="panel"):
            yield Label("", id="step_title", classes="step-title")
            yield Label("", id="step_subtitle")
            yield Markdown("", id="why")
            yield OptionList(id="choices")
            yield Static("", id="explain", classes="explain")
            with Horizontal(classes="actions"):
                yield Button(self.t("wizard.button.back"), id="back")
                yield Button(self.t("wizard.button.next"), variant="primary", id="next")
        yield Footer()

    def on_mount(self) -> None:
        self._load_decision()

    def _current(self) -> Decision:
        decisions = visible_decisions(self.wizard.answers)
        index = min(self.wizard.decision_index, len(decisions) - 1)
        return decisions[index]

    def _load_decision(self) -> None:
        decisions = visible_decisions(self.wizard.answers)
        if self.wizard.decision_index >= len(decisions):
            return
        decision = decisions[self.wizard.decision_index]
        step = self.t(
            "wizard.step",
            current=self.wizard.decision_index + 1,
            total=len(decisions),
        )
        self.query_one("#step_title", Label).update(f"{self.t.pick(decision.title)}  ·  {step}")
        self.query_one("#step_subtitle", Label).update(self.t.pick(decision.subtitle))
        self.query_one("#why", Markdown).update(self.t.pick(decision.why))

        options = self.query_one("#choices", OptionList)
        options.clear_options()
        preselected = self.wizard.answers.get(decision.key, decision.default)
        default_index = 0
        for index, choice in enumerate(decision.choices):
            options.add_option(Option(self.t.pick(choice.label), id=choice.value))
            if choice.value == preselected:
                default_index = index
        options.highlighted = default_index
        self.selected_value = decision.choices[default_index].value
        self._render_explanation(decision.choices[default_index])

    def _choice_by_value(self, value: str) -> Choice:
        for choice in self._current().choices:
            if choice.value == value:
                return choice
        return self._current().choices[0]

    def _render_explanation(self, choice: Choice) -> None:
        text = (
            f"[green]+ {self.t('wizard.section.adds')}[/green]\n"
            f"{self.t.pick(choice.adds)}\n\n"
            f"[red]- {self.t('wizard.section.removes')}[/red]\n"
            f"{self.t.pick(choice.removes)}\n\n"
            f"[cyan]{self.t('wizard.section.implication')}[/cyan]\n"
            f"{self.t.pick(choice.implication)}"
        )
        self.query_one("#explain", Static).update(text)

    def _highlight(self, option_id: str | None) -> None:
        if option_id is None:
            return
        self.selected_value = str(option_id)
        self._render_explanation(self._choice_by_value(str(option_id)))

    def on_option_list_option_highlighted(self, event: OptionList.OptionHighlighted) -> None:
        self._highlight(event.option_id)

    def on_option_list_option_selected(self, event: OptionList.OptionSelected) -> None:
        self._highlight(event.option_id)

    def on_button_pressed(self, event: Button.Pressed) -> None:
        if event.button.id == "back":
            self._go_back()
        elif event.button.id == "next":
            self._go_next()

    def _go_back(self) -> None:
        if self.wizard.decision_index == 0:
            self.app.pop_screen()
            return
        # Answers gate visibility, so replay them up to the step we return to.
        previous = dict(self.wizard.answers)
        self.wizard.decision_index -= 1
        rebuilt: dict[str, str] = {}
        for index in range(self.wizard.decision_index + 1):
            candidates = visible_decisions(rebuilt)
            if index >= len(candidates):
                break
            key = candidates[index].key
            if key not in previous:
                break
            rebuilt[key] = previous[key]
        self.wizard.answers = rebuilt
        self._load_decision()

    def _go_next(self) -> None:
        decision = self._current()
        self.wizard.answers[decision.key] = self.selected_value or decision.default
        self.wizard.decision_index += 1
        if self.wizard.decision_index >= len(visible_decisions(self.wizard.answers)):
            self.app.push_screen(SummaryScreen())
        else:
            self._load_decision()


class SummaryScreen(_WizardScreen):
    def compose(self) -> ComposeResult:
        yield Header()
        with VerticalScroll(id="panel"):
            yield Label(self.t("wizard.summary.title"), classes="step-title")
            yield Markdown("", id="summary_md")
            with Horizontal(classes="actions"):
                yield Button(self.t("wizard.button.back"), id="back")
                yield Button(self.t("wizard.button.create"), variant="success", id="generate")
        yield Footer()

    def on_mount(self) -> None:
        identity = self.wizard.identity
        lines = [
            self.t("wizard.summary.intro"),
            "",
            f"**{self.t('wizard.field.project_name')}:** {identity['project_name']}",
            f"**{self.t('wizard.field.target')}:** `{identity['target']}`",
            f"**Slug:** `{identity['project_slug']}`",
            "",
            "| | |",
            "|---|---|",
        ]
        for decision in visible_decisions(self.wizard.answers):
            value = self.wizard.answers.get(decision.key, decision.default)
            choice = next(item for item in decision.choices if item.value == value)
            lines.append(f"| {self.t.pick(decision.title)} | {self.t.pick(choice.label)} |")
        self.query_one("#summary_md", Markdown).update("\n".join(lines))

    def on_button_pressed(self, event: Button.Pressed) -> None:
        if event.button.id == "back":
            self.wizard.decision_index = max(0, len(visible_decisions(self.wizard.answers)) - 1)
            self.app.pop_screen()
            if isinstance(self.app.screen, DecisionScreen):
                self.app.screen._load_decision()
        elif event.button.id == "generate":
            self.app.push_screen(GenerateScreen())


#: The bar creeps to this percentage while the worker runs, then jumps to 100 on success.
_PROGRESS_CEILING = 90


class GenerateScreen(ModalScreen[None]):
    """Runs the scaffold in a worker thread and streams progress into the UI."""

    def compose(self) -> ComposeResult:
        with Vertical(id="generate_panel"):
            yield Label("", id="gen_title")
            yield ProgressBar(total=100, show_eta=False, id="progress")
            yield RichLog(id="gen_log", highlight=True, markup=True)
            yield Button("Close", id="close", disabled=True)

    @property
    def wizard(self) -> WizardApp:
        app = self.app
        if not isinstance(app, WizardApp):  # pragma: no cover - defensive
            msg = "screen mounted outside WizardApp"
            raise TypeError(msg)
        return app

    def on_mount(self) -> None:
        self.query_one("#gen_title", Label).update(self.wizard.translate("wizard.running"))
        self.query_one("#close", Button).label = self.wizard.translate("wizard.button.quit")
        self.set_interval(0.1, self._tick)
        self.run_worker(self._generate, exclusive=True, thread=True)

    def _tick(self) -> None:
        bar = self.query_one("#progress", ProgressBar)
        if (bar.progress or 0) < _PROGRESS_CEILING:
            bar.advance(1)

    def _log(self, message: str) -> None:
        self.query_one("#gen_log", RichLog).write(message)

    def _resolved_answers(self) -> dict[str, str]:
        """Materialize defaults for every decision that ended up visible."""
        resolved: dict[str, str] = {}
        for decision in visible_decisions(self.wizard.answers):
            resolved[decision.key] = self.wizard.answers.get(decision.key, decision.default)
        return resolved

    def _generate(self) -> None:
        identity = dict(self.wizard.identity)
        answers = self._resolved_answers()
        try:
            config = ProjectConfig(
                target=Path(identity["target"]),
                project_name=identity["project_name"],
                author_name=identity["author_name"],
                domain_name=identity["domain_name"],
                email=identity["email"],
                project_slug=identity["project_slug"],
                use_docker=answers.get("use_docker", "y"),
                rest_api=answers.get("rest_api", "DRF"),
                use_celery=answers.get("use_celery", "n"),
                frontend_pipeline=answers.get("frontend_pipeline", "None"),
                ci_tool=answers.get("ci_tool", "Github"),
                use_whitenoise=answers.get("use_whitenoise", "y"),
                use_sentry=answers.get("use_sentry", "n"),
                cloud_provider=answers.get("cloud_provider", "None"),
                with_pgbouncer=answers.get("with_pgbouncer", "n") == "y",
                language=self.wizard.language,
            )
            ref = config.cookiecutter_ref[:12]
            self.app.call_from_thread(self._log, f"[cyan]cookiecutter-django @ {ref}[/cyan]")
            scaffold(config)
            self.app.call_from_thread(self._log, "[green]Overlay applied.[/green]")
            self.app.call_from_thread(self._log, next_steps(config))
            self.app.call_from_thread(self._finish, ok=True)
        except Exception as exc:
            self.app.call_from_thread(self._log, f"[red]error:[/red] {exc}")
            self.app.call_from_thread(self._finish, ok=False)

    def _finish(self, *, ok: bool) -> None:
        key = "wizard.done" if ok else "wizard.failed"
        if ok:
            self.query_one("#progress", ProgressBar).progress = 100
        self.query_one("#gen_title", Label).update(self.wizard.translate(key))
        self.query_one("#close", Button).disabled = False

    def on_button_pressed(self, event: Button.Pressed) -> None:
        if event.button.id == "close":
            self.app.exit()


def run(*, language: str = "en", target: Path | None = None) -> int:
    """Entry point used by ``django-ai-harness wizard``."""
    WizardApp(language=language, target=target).run()
    return 0


if __name__ == "__main__":  # pragma: no cover
    raise SystemExit(run())
