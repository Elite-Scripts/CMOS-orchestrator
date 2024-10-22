import logging
from logging import Handler

from textual.widgets import Log


class WidgetHandler(Handler):
    """Custom logging handler sending logs to textual widget."""

    def __init__(self, widget: Log):
        super().__init__()
        self.widget = widget

    def emit(self, record):
        log_entry = self.format(record)
        self.widget.app.call_from_thread(self.widget.write_line, log_entry)


class SystemSynchronizedLogWidget(Log):
    def on_mount(self) -> None:
        logger = logging.getLogger("cmos")
        logger.setLevel(logging.INFO)
        handler = WidgetHandler(self)
        handler.setFormatter(logging.Formatter('%(levelname)s: %(message)s'))
        logger.addHandler(handler)
