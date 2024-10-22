import os
from pathlib import Path

from textual.app import App, ComposeResult
from textual.containers import Container

import core
from textual_ui.log_widget import SystemSynchronizedLogWidget
from textual_ui.logo_widget import BootLogo
from textual_ui.system_stats_widget import SystemStatsWidget


class TextualApp(App):
    """A Textual app to help visualize the CMOS orchestration process."""
    TITLE = "CMOS"
    script_dir = Path(__file__).parent
    css_path = script_dir / '..' / '..' / 'resources' / 'grid_layout1.tcss'
    CSS_PATH = css_path.resolve()
    BINDINGS = [("d", "toggle_dark", "Toggle dark mode")]

    def compose(self) -> ComposeResult:
        """Create child widgets for the app."""
        yield Container(
            BootLogo(id='logo'),
            SystemStatsWidget(id="system-stats"),
            id="top-container",
        )
        yield SystemSynchronizedLogWidget(id="log")

    def action_toggle_dark(self) -> None:
        """An action to toggle dark mode."""
        self.dark = not self.dark

    async def on_ready(self) -> None:
        self.run_worker(self.run_cmos, thread=True)

    def run_cmos(self) -> None:
        core.main()


def run():
    app = TextualApp()
    app.run()
