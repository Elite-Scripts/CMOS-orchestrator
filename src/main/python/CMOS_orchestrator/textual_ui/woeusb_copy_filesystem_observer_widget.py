import asyncio
from asyncio import create_task

from WoeUSB import core
from textual.reactive import Reactive
from textual.widgets import ProgressBar


class WoeUsbCopyFilesystemObserverWidget(ProgressBar):
    file_path = Reactive("No path yet")
    progress_percent = Reactive("0")

    def process_completed(self):
        self.remove()

    async def auto_refresh(self):
        while True:
            if core.get_current_state() == 'copying-filesystem':
                copyfiles_handle = core.get_copyfiles_handle()
                if hasattr(copyfiles_handle, 'percentage'):
                    if 'hidden' in self.classes:
                        self.remove_class("hidden")
                    self.file_path = copyfiles_handle.file
                    self.progress_percent = copyfiles_handle.percentage
                    self.update(progress=self.progress_percent)
                    self.refresh()
            else:
                if 'hidden' not in self.classes:
                    await self.remove()
                    break
            await asyncio.sleep(1)

    def on_mount(self) -> None:
        """Lifecycle method called when the widget is added to the app."""
        create_task(self.auto_refresh())
