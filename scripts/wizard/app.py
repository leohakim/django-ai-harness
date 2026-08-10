"""django-ai-harness guided project wizard (Textual TUI)."""

from __future__ import annotations

import sys
from pathlib import Path

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

# Allow `uv run scripts/wizard/app.py` and package imports
SCRIPTS_DIR = Path(__file__).resolve().parents[1]
if str(SCRIPTS_DIR) not in sys.path:
    sys.path.insert(0, str(SCRIPTS_DIR))

from lib.scaffold import ProjectConfig  # noqa: E402
from lib.scaffold import next_steps  # noqa: E402
from lib.scaffold import sanitize_slug  # noqa: E402
from lib.scaffold import scaffold  # noqa: E402
from wizard.steps import DECISIONS  # noqa: E402
from wizard.steps import IDENTITY_HELP  # noqa: E402
from wizard.steps import Choice  # noqa: E402
from wizard.steps import Decision  # noqa: E402

HARNESS_ROOT = Path(__file__).resolve().parents[2]


def visible_decisions(answers: dict[str, str]) -> list[Decision]:
    out: list[Decision] = []
    for decision in DECISIONS:
        ok = True
        for key, expected in decision.requires:
            if answers.get(key) != expected:
                ok = False
                break
        if ok:
            out.append(decision)
    return out


class WelcomeScreen(Screen[None]):
    BINDINGS = [
        Binding("enter", "continue", "Continuar", show=True, priority=True),
    ]

    def compose(self) -> ComposeResult:
        yield Header(show_clock=False)
        with Vertical(id="panel"):
            yield Label("django-ai-harness", id="brand")
            yield Label("Asistente guiado para un proyecto Django nuevo", id="tagline")
            yield Markdown(
                """
Este asistente te acompaña **paso a paso**.

En cada decisión verás:
- **Qué añade** si lo activas
- **Qué quitas / dejas fuera** si no
- **Implicancias** prácticas para el día a día

Al final generaremos **cookiecutter-django** (plantilla upstream) + el **overlay**
del harness (DX moderno + arquitectura HackSoft).

Controles: `Enter` continuar · `q` salir · flechas para opciones.
"""
            )
            yield Button("Empezar", variant="primary", id="start")
        yield Footer()

    def on_mount(self) -> None:
        self.set_focus(self.query_one("#start", Button))

    def on_button_pressed(self, event: Button.Pressed) -> None:
        if event.button.id == "start":
            self.action_continue()

    def action_continue(self) -> None:
        self.app.push_screen(IdentityScreen())


class IdentityScreen(Screen[None]):
    def compose(self) -> ComposeResult:
        yield Header()
        with VerticalScroll(id="panel"):
            yield Label("1 · Identidad del proyecto", classes="step-title")
            yield Markdown(IDENTITY_HELP)
            yield Label("Nombre visible del proyecto")
            yield Input(placeholder="My Shop", id="project_name")
            yield Label("Ruta de destino (carpeta nueva)")
            yield Input(placeholder=str(Path.home() / "Projects" / "my_shop"), id="target")
            yield Label("Descripción corta")
            yield Input(value="Project managed with django-ai-harness", id="description")
            yield Label("Autor")
            yield Input(value="django-ai-harness", id="author_name")
            yield Label("Dominio (para emails de ejemplo)")
            yield Input(value="example.com", id="domain_name")
            yield Static("", id="identity_error", classes="error")
            with Horizontal(classes="actions"):
                yield Button("Atrás", id="back")
                yield Button("Continuar", variant="primary", id="next")
        yield Footer()

    def on_button_pressed(self, event: Button.Pressed) -> None:
        if event.button.id == "back":
            self.app.pop_screen()
            return
        if event.button.id == "next":
            self._submit()

    def _submit(self) -> None:
        err = self.query_one("#identity_error", Static)
        name = self.query_one("#project_name", Input).value.strip()
        target_raw = self.query_one("#target", Input).value.strip()
        description = self.query_one("#description", Input).value.strip()
        author = self.query_one("#author_name", Input).value.strip() or "django-ai-harness"
        domain = self.query_one("#domain_name", Input).value.strip() or "example.com"
        if not name:
            err.update("Escribe un nombre de proyecto.")
            return
        if not target_raw:
            err.update("Indica la ruta de destino.")
            return
        target = Path(target_raw).expanduser()
        try:
            slug = sanitize_slug(target.name)
        except ValueError as exc:
            err.update(str(exc))
            return
        if target.exists():
            err.update(f"La ruta ya existe: {target}")
            return
        app = self.app
        assert isinstance(app, WizardApp)
        app.identity = {
            "project_name": name,
            "target": str(target),
            "description": description or "Project managed with django-ai-harness",
            "author_name": author,
            "domain_name": domain,
            "email": f"maintainers@{domain}",
            "project_slug": slug,
        }
        app.answers = {}
        app.decision_index = 0
        app.push_screen(DecisionScreen())


class DecisionScreen(Screen[None]):
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
                yield Button("Atrás", id="back")
                yield Button("Continuar", variant="primary", id="next")
        yield Footer()

    def on_mount(self) -> None:
        self._load_decision()

    def _current(self) -> Decision:
        app = self.app
        assert isinstance(app, WizardApp)
        decisions = visible_decisions(app.answers)
        return decisions[app.decision_index]

    def _load_decision(self) -> None:
        app = self.app
        assert isinstance(app, WizardApp)
        decisions = visible_decisions(app.answers)
        if app.decision_index >= len(decisions):
            return
        decision = decisions[app.decision_index]
        total = len(decisions)
        self.query_one("#step_title", Label).update(
            f"{app.decision_index + 2} · {decision.title}  ({app.decision_index + 1}/{total})"
        )
        self.query_one("#step_subtitle", Label).update(decision.subtitle)
        self.query_one("#why", Markdown).update(decision.why)
        options = self.query_one("#choices", OptionList)
        options.clear_options()
        default_idx = 0
        prior = app.answers.get(decision.key, decision.default)
        for i, choice in enumerate(decision.choices):
            options.add_option(Option(choice.label, id=choice.value))
            if choice.value == prior:
                default_idx = i
        options.highlighted = default_idx
        self.selected_value = decision.choices[default_idx].value
        self._render_explain(decision.choices[default_idx])

    def _choice_by_value(self, value: str) -> Choice:
        for choice in self._current().choices:
            if choice.value == value:
                return choice
        return self._current().choices[0]

    def _render_explain(self, choice: Choice) -> None:
        text = (
            f"[b]Selección:[/b] {choice.label}\n\n"
            f"[green]+ Añade[/green]\n{choice.adds}\n\n"
            f"[red]− Quita / deja fuera[/red]\n{choice.removes}\n\n"
            f"[cyan]Implicancia[/cyan]\n{choice.implication}"
        )
        self.query_one("#explain", Static).update(text)

    def on_option_list_option_highlighted(self, event: OptionList.OptionHighlighted) -> None:
        if event.option_id is None:
            return
        value = str(event.option_id)
        self.selected_value = value
        self._render_explain(self._choice_by_value(value))

    def on_option_list_option_selected(self, event: OptionList.OptionSelected) -> None:
        if event.option_id is None:
            return
        value = str(event.option_id)
        self.selected_value = value
        self._render_explain(self._choice_by_value(value))

    def on_button_pressed(self, event: Button.Pressed) -> None:
        app = self.app
        assert isinstance(app, WizardApp)
        if event.button.id == "back":
            if app.decision_index == 0:
                self.app.pop_screen()
                return
            prev = dict(app.answers)
            app.decision_index -= 1
            rebuilt: dict[str, str] = {}
            i = 0
            # Keep answers through the step we return to so prior selection is restored
            while i <= app.decision_index:
                vis = visible_decisions(rebuilt)
                if i >= len(vis):
                    break
                key = vis[i].key
                if key not in prev:
                    break
                rebuilt[key] = prev[key]
                i += 1
            app.answers = rebuilt
            self._load_decision()
            return
        if event.button.id == "next":
            value = self.selected_value or self._current().default
            app.answers[self._current().key] = value
            app.decision_index += 1
            decisions = visible_decisions(app.answers)
            if app.decision_index >= len(decisions):
                self.app.push_screen(SummaryScreen())
            else:
                self._load_decision()


class SummaryScreen(Screen[None]):
    def compose(self) -> ComposeResult:
        yield Header()
        with VerticalScroll(id="panel"):
            yield Label("Resumen · confirma antes de generar", classes="step-title")
            yield Markdown("", id="summary_md")
            with Horizontal(classes="actions"):
                yield Button("Atrás", id="back")
                yield Button("Generar proyecto", variant="success", id="generate")
        yield Footer()

    def on_mount(self) -> None:
        app = self.app
        assert isinstance(app, WizardApp)
        lines = [
            f"**Proyecto:** {app.identity['project_name']}",
            f"**Ruta:** `{app.identity['target']}`",
            f"**Slug:** `{app.identity['project_slug']}`",
            "",
            "| Decisión | Valor |",
            "|---|---|",
        ]
        for decision in visible_decisions(app.answers):
            value = app.answers.get(decision.key, decision.default)
            choice = next(c for c in decision.choices if c.value == value)
            lines.append(f"| {decision.title} | {choice.label} |")
        lines.append("")
        lines.append(
            "Al confirmar se ejecutará **cookiecutter-django** (commit pin) "
            "+ **overlay** django-ai-harness. Puede tardar unos minutos la primera vez."
        )
        self.query_one("#summary_md", Markdown).update("\n".join(lines))

    def on_button_pressed(self, event: Button.Pressed) -> None:
        app = self.app
        assert isinstance(app, WizardApp)
        if event.button.id == "back":
            app.decision_index = max(0, len(visible_decisions(app.answers)) - 1)
            self.app.pop_screen()
            # Reload previous decision screen if present
            if isinstance(self.app.screen, DecisionScreen):
                self.app.screen._load_decision()
            return
        if event.button.id == "generate":
            self.app.push_screen(GenerateScreen())


class GenerateScreen(ModalScreen[None]):
    def compose(self) -> ComposeResult:
        with Vertical(id="generate_panel"):
            yield Label("Generando proyecto…", id="gen_title")
            yield ProgressBar(total=100, show_eta=False, id="progress")
            yield RichLog(id="gen_log", highlight=True, markup=True)
            yield Button("Cerrar", id="close", disabled=True)

    def on_mount(self) -> None:
        self.set_interval(0.05, self._tick_progress)
        self.run_worker(self._run, exclusive=True, thread=True)

    def _tick_progress(self) -> None:
        bar = self.query_one("#progress", ProgressBar)
        if bar.progress < 90:
            bar.advance(1)

    def _write_log(self, message: str) -> None:
        self.query_one("#gen_log", RichLog).write(message)

    def _run(self) -> None:
        app = self.app
        assert isinstance(app, WizardApp)
        identity = dict(app.identity)
        # Only persist answers for currently visible decisions
        visible_answers: dict[str, str] = {}
        while True:
            vis = visible_decisions(visible_answers)
            progressed = False
            for decision in vis:
                if decision.key not in visible_answers:
                    visible_answers[decision.key] = app.answers.get(
                        decision.key,
                        decision.default,
                    )
                    progressed = True
                    break
            if not progressed:
                break
        try:
            self.app.call_from_thread(self._write_log, "[cyan]Preparando configuración…[/cyan]")
            cfg = ProjectConfig(
                target=Path(identity["target"]),
                project_name=identity["project_name"],
                description=identity["description"],
                author_name=identity["author_name"],
                domain_name=identity["domain_name"],
                email=identity["email"],
                project_slug=identity["project_slug"],
                use_docker=visible_answers.get("use_docker", "y"),
                rest_api=visible_answers.get("rest_api", "DRF"),
                use_celery=visible_answers.get("use_celery", "n"),
                frontend_pipeline=visible_answers.get("frontend_pipeline", "None"),
                ci_tool=visible_answers.get("ci_tool", "Github"),
                use_whitenoise=visible_answers.get("use_whitenoise", "y"),
                use_sentry=visible_answers.get("use_sentry", "n"),
                cloud_provider=visible_answers.get("cloud_provider", "None"),
                with_pgbouncer=visible_answers.get("with_pgbouncer", "n") == "y",
            )
            self.app.call_from_thread(
                self._write_log,
                f"[cyan]cookiecutter-django @ {cfg.cookiecutter_ref[:12]}…[/cyan]",
            )
            scaffold(cfg, HARNESS_ROOT)
            self.app.call_from_thread(self._write_log, "[green]Overlay aplicado.[/green]")
            self.app.call_from_thread(self._write_log, next_steps(cfg))
            self.app.call_from_thread(self._done_ok)
        except Exception as exc:  # noqa: BLE001 — show in UI
            self.app.call_from_thread(self._write_log, f"[red]Error:[/red] {exc}")
            self.app.call_from_thread(self._done_err)

    def _done_ok(self) -> None:
        bar = self.query_one("#progress", ProgressBar)
        bar.progress = 100
        self.query_one("#gen_title", Label).update("Listo")
        self.query_one("#close", Button).disabled = False

    def _done_err(self) -> None:
        self.query_one("#gen_title", Label).update("Falló la generación")
        self.query_one("#close", Button).disabled = False

    def on_button_pressed(self, event: Button.Pressed) -> None:
        if event.button.id == "close":
            self.app.exit()


class WizardApp(App[None]):
    TITLE = "django-ai-harness"
    SUB_TITLE = "Asistente de nuevo proyecto"
    CSS_PATH = str(Path(__file__).with_name("wizard.tcss"))
    BINDINGS = [Binding("q", "quit", "Salir")]

    identity: dict[str, str] = {}
    answers: dict[str, str] = {}
    decision_index: int = 0

    def on_mount(self) -> None:
        self.push_screen(WelcomeScreen())


def main() -> None:
    WizardApp().run()


if __name__ == "__main__":
    main()
