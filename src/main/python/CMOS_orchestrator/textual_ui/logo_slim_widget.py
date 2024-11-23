from rich.style import Style
from rich.text import Text
from textual.widget import Widget


class BootLogoSlim(Widget):
    """A widget to display bootlogo."""

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)

    def render(self):
        grid = """          Creation Media Operating System          """
        style = Style.parse("black on #f4ed11")
        styled_text = Text(grid, style=style)
        return styled_text
