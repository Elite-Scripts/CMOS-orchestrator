from pkg_resources import resource_filename
from textual.app import App, ComposeResult
from textual.containers import Container
from textual.widgets import Footer

from CMOS_orchestrator.core import main, PostProcessTask, is_os_running_in_virtualbox
from CMOS_orchestrator.textual_ui.cmos_observer_widget import CmosObserverWidget
from CMOS_orchestrator.textual_ui.gather_iso_observer_widget import GatherIsoObserverWidget
from CMOS_orchestrator.textual_ui.log_widget import SystemSynchronizedLogWidget
from CMOS_orchestrator.textual_ui.logo_widget import BootLogo
from CMOS_orchestrator.textual_ui.system_stats_widget import SystemStatsWidget
from CMOS_orchestrator.textual_ui.woeusb_copy_filesystem_observer_widget import WoeUsbCopyFilesystemObserverWidget


class TextualApp(App):
    """A Textual app to help visualize the CMOS orchestration process."""
    TITLE = "CMOS"
    css_path = resource_filename(__name__, '../resources/grid_layout1.tcss')
    CSS_PATH = css_path
    BINDINGS = [("d", "toggle_log_widget", "View Logs")]
    cmos_observer_widget = CmosObserverWidget(id="cmos-observer", classes='background-in-progress')
    gather_iso_observer_widget = GatherIsoObserverWidget(id="gather-iso-observer", total=100,
                                                         classes="hidden background-in-progress")
    woeusb_copy_filesystem_observer_widget = WoeUsbCopyFilesystemObserverWidget(id="woeusb-copy-filesystem-observer",
                                                                                total=100,
                                                                                classes="hidden background-in-progress")
    system_stats_widget = SystemStatsWidget(id="system-stats")
    system_synchronized_log_widget = SystemSynchronizedLogWidget(id="system-synchronized-log", classes='hidden')

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
            self.woeusb_copy_filesystem_observer_widget,
            classes='background-in-progress',
            id="progress-bars",
        )
        yield self.system_synchronized_log_widget
        yield Footer()

    def action_toggle_log_widget(self) -> None:
        self.query_one('#system-synchronized-log').toggle_class('hidden')
        self.system_synchronized_log_widget.refresh_lines(0, 1000)

    async def on_ready(self) -> None:
        self.run_worker(self.run_cmos, thread=True)

    def run_cmos(self) -> None:
        post_process_task = PostProcessTask.RESTART
        if is_os_running_in_virtualbox():
            # TODO remove this test environment specific code out of the src.
            post_process_task = PostProcessTask.NONE
        main([self.cmos_observer_widget], [self.gather_iso_observer_widget], post_process_task=post_process_task)


def run():
    app = TextualApp()
    app.run()