import asyncio
from asyncio import create_task

import psutil
from textual.reactive import Reactive
from textual.widget import Widget


class SystemStatsWidget(Widget):
    total_memory = Reactive(0)
    available_memory = Reactive(0)
    used_memory = Reactive(0)
    memory_percent = Reactive(0)
    cpu_percent = Reactive(0)
    disk_usage = Reactive("")

    async def update_system_stats(self):
        while True:
            memory_info = psutil.virtual_memory()
            cpu_info = psutil.cpu_percent(interval=1)
            disk_info = psutil.disk_usage('/')
            self.total_memory = memory_info.total // 1024 ** 2
            self.available_memory = memory_info.available // 1024 ** 2
            self.used_memory = (memory_info.total - memory_info.available) // 1024 ** 2
            self.memory_percent = memory_info.percent
            self.cpu_percent = cpu_info
            self.disk_usage = f"{disk_info.used // (1024 ** 3)}GB used out of {disk_info.total // (1024 ** 3)}GB"
            await asyncio.sleep(0.25)

    def on_mount(self) -> None:
        """Lifecycle method called when the widget is added to the app."""
        create_task(self.update_system_stats())

    def render(self) -> "RenderableType":
        return self.get_content()

    def get_title(self) -> str:
        """Title for widget"""
        return "SYSTEM STATS"

    def get_content(self) -> str:
        """Content of widget"""
        return f"""
        MEMORY INFO
        Total memory: {self.total_memory} MB
        Available memory: {self.available_memory} MB
        Used memory: {self.used_memory} MB
        Memory percent used: {self.memory_percent} %

        CPU UTILIZATION
        CPU usage: {self.cpu_percent} %

        DISK USAGE
        Disk usage: {self.disk_usage}
        """