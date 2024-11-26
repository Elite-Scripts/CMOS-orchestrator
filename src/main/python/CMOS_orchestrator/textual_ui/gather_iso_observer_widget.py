import asyncio
from asyncio import create_task

from textual.reactive import Reactive
from textual.widgets import ProgressBar


class GatherIsoObserverWidget(ProgressBar):
    file_path = Reactive("No path yet")
    progress_percent = Reactive("0")
    has_already_created_widget = False

    def update_progress(self, progress_update):
        self.file_path = progress_update.file_path
        self.progress_percent = progress_update.progress_percent
        self.update(progress=self.progress_percent)

    async def auto_refresh(self):
        while True:
            self.refresh()
            await asyncio.sleep(1)

    def on_mount(self) -> None:
        """Lifecycle method called when the widget is added to the app."""
        create_task(self.auto_refresh())