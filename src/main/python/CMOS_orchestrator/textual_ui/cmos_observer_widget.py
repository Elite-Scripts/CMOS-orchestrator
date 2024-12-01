import asyncio
import time
from asyncio import create_task

from WoeUSB import core
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
    woeusb_state = Reactive("No status yet")

    def update(self, message):
        self.last_status = self.status
        self.status = message.status
        self.description = message.description

    async def auto_refresh(self):
        while True:
            self.woeusb_state = core.get_current_state()
            self.refresh()
            await asyncio.sleep(1)

    def on_mount(self) -> None:
        """Lifecycle method called when the widget is added to the app."""
        create_task(self.auto_refresh())

    def render(self):
        # has_failed = True
        if self.status == 'CMOS has completed successfully!':
            for widget in self.app.query('.background-in-progress'):
                widget.remove_class('background-in-progress')
                widget.add_class('background-complete')
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
            self.app.query_one('#progress-bars').remove_class("background-in-progress")
            self.app.query_one('#progress-bars').add_class("background-failure")
            self.app.query_one('#log').remove_class("hidden")
            return Text(
                f"Status: {self.status}\nDescription: {self.description}\nStatus That Failed: {self.last_status}",
                style="bold")
        else:
            if 'WoeUSB' in self.status:
                return Text(f"{self.status}: {self.woeusb_state}\nDescription: {self.description}", style="bold")
            else:
                return Text(f"{self.status}\nDescription: {self.description}", style="bold")