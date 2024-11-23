import time

from rich.text import Text
from textual.containers import Container
from textual.reactive import Reactive
from textual.widget import Widget

from CMOS_orchestrator.textual_ui.logo_slim_widget import BootLogoSlim
from CMOS_orchestrator.textual_ui.system_stats_widget import SystemStatsWidget


class CmosObserverWidget(Widget):
    status = Reactive("No status yet")
    description = Reactive("")
    last_status = Reactive("No status yet")
    has_already_created_widget = False

    def update(self, message):
        self.last_status = self.status
        self.status = message.status
        self.description = message.description

    def render(self):
        # has_failed = True
        has_failed = "CMOS experienced a failure!" in self.status
        if has_failed:
            if not self.has_already_created_widget:
                self.has_already_created_widget = True
                system_stats_widget2 = SystemStatsWidget(id="system-stats2")
                self.app.mount(
                    Container(
                        BootLogoSlim(id='logo-slim'),
                        system_stats_widget2,
                        id="top-container-slim",
                        classes="hidden",
                    ),
                    before=0
                )
            self.styles.background = "red"
            self.app.query_one("#top-container").add_class("hidden")
            self.app.query_one("#top-container-slim").remove_class("hidden")
            return Text(
                f"Status: {self.status}\nDescription: {self.description}\nStatus That Failed: {self.last_status}",
                style="bold")
        else:
            return Text(f"Status: {self.status}\nDescription: {self.description}", style="bold")