from pathlib import Path

from pkg_resources import resource_filename
from textual.app import App, ComposeResult
from textual.containers import Container
from textual.lazy import Lazy, Reveal

from CMOS_orchestrator.core import main
from CMOS_orchestrator.textual_ui.cmos_observer_widget import CmosObserverWidget
from CMOS_orchestrator.textual_ui.gather_iso_observer_widget import GatherIsoObserverWidget
from CMOS_orchestrator.textual_ui.log_widget import SystemSynchronizedLogWidget
from CMOS_orchestrator.textual_ui.logo_slim_widget import BootLogoSlim
from CMOS_orchestrator.textual_ui.logo_widget import BootLogo
from CMOS_orchestrator.textual_ui.system_stats_widget import SystemStatsWidget


class TextualApp(App):
    """A Textual app to help visualize the CMOS orchestration process."""
    TITLE = "CMOS"
    css_path = resource_filename(__name__, '../resources/grid_layout1.tcss')
    CSS_PATH = css_path
    BINDINGS = [("d", "toggle_dark", "Toggle dark mode")]
    cmos_observer_widget = CmosObserverWidget(id="cmos-observer")
    gather_iso_observer_widget = GatherIsoObserverWidget(id="gather-iso-observer", total=100)
    system_stats_widget = SystemStatsWidget(id="system-stats")

    def compose(self) -> ComposeResult:
        """Create child widgets for the app."""
        yield Container(
            BootLogo(id='logo'),
            self.system_stats_widget,
            id="top-container",
        )
        yield self.cmos_observer_widget
        yield Container(
            self.gather_iso_observer_widget,
            id="progress-bars",
        )
        yield SystemSynchronizedLogWidget(id="log")

    def action_toggle_dark(self) -> None:
        """An action to toggle dark mode."""
        self.dark = not self.dark

    async def on_ready(self) -> None:
        self.run_worker(self.run_cmos, thread=True)

    def run_cmos(self) -> None:
        main([self.cmos_observer_widget], [self.gather_iso_observer_widget])


def run():
    app = TextualApp()
    app.run()