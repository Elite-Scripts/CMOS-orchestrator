from rich.text import Text
from textual.reactive import Reactive
from textual.widget import Widget


class CmosObserverWidget(Widget):
    status = Reactive("No status yet")
    description = Reactive("")
    last_status = Reactive("No status yet")

    def update(self, message):
        self.last_status = self.status
        self.status = message.status
        self.description = message.description

    def render(self):
        if "CMOS experienced a failure!" in self.status:
            return Text(
                f"Status: {self.status}\nDescription: {self.description}\nStatus That Failed: {self.last_status}",
                style="bold")
        else:
            return Text(f"Status: {self.status}\nDescription: {self.description}", style="bold")