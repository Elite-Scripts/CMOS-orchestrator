import json
import logging
from logging import Handler

import rich
from textual.widgets import Log


class JsonLogFormatter(logging.Formatter):
    def format(self, record):
        return json.dumps({
            'time': self.formatTime(record),
            'name': record.name,
            'levelname': record.levelname,
            'message': record.msg
        })


def wrap_text(text: str, max_len: int) -> str:
    words = text.split()
    lines, current_line = [], []

    for word in words:
        if len(' '.join(current_line + [word])) <= max_len:
            current_line.append(word)
        else:
            lines.append(' '.join(current_line))
            current_line = [word]

    lines.append(' '.join(current_line))

    return "\n".join(lines)


class WidgetHandler(Handler):
    """Custom logging handler sending logs to textual widget."""

    def __init__(self, widget: Log, max_len: int):
        super().__init__()
        self.widget = widget
        self.max_len = max_len

    def emit(self, record: logging.LogRecord) -> None:
        log_entry = self.format(record)
        log_entry = wrap_text(log_entry, max_len=self.max_len)
        self.widget.app.call_from_thread(self.widget.write_line, log_entry)


class SystemSynchronizedLogWidget(Log):
    def on_mount(self) -> None:
        logger = logging.getLogger("cmos")
        logger.setLevel(logging.INFO)

        file_handler = logging.FileHandler('cmos_logfile.log')
        file_handler.setFormatter(logging.Formatter('%(asctime)s %(levelname)s: %(message)s'))
        logger.addHandler(file_handler)

        json_file_handler = logging.FileHandler('cmos_logfile.json')
        json_file_handler.setFormatter(JsonLogFormatter())
        logger.addHandler(json_file_handler)

        console_width = rich.get_console().width
        handler = WidgetHandler(self, max_len=console_width)  # Use console width as max_len
        handler.setFormatter(logging.Formatter('%(levelname)s: %(message)s'))
        logger.addHandler(handler)