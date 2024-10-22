from rich.segment import Segment
from rich.style import Style
from rich_pixels import Pixels
from textual.widget import Widget


class BootLogo(Widget):
    """A widget to display bootlogo."""

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)

    def render(self):
        grid = """
                                                   
         ██████ ███    ███  ██████  ███████        
        ██      ████  ████ ██    ██ ██             
        ██      ██ ████ ██ ██    ██ ███████        
        ██      ██  ██  ██ ██    ██      ██        
         ██████ ██      ██  ██████  ███████        
                                                   
          Creation Media Operating System          
                                                   
"""

        # Map non-space characters to black on yellow and spaces to yellow on yellow
        mapping_defaults = {
            " ": Segment(" ", Style.parse("on #f4ed11")),
            "█": Segment("█", Style.parse("black on #f4ed11")),
        }
        logo_mapping = mapping_defaults.copy()

        # Add mapping for all other characters in 'Creation Media Operating System' text
        for character in 'Creation Media Operating System':
            logo_mapping[character] = Segment(character, Style.parse("#0d553c on #f4ed11"))

        logo_pixels = Pixels.from_ascii(grid, logo_mapping)
        created_by_grid = """     Created by """
        created_by_grid2 = """warfront1"""
        created_by_grid3 = """ at"""
        created_by_grid4 = """ EliteScripts LLC.     
                                                   """
        created_by_mapping = mapping_defaults.copy()
        for character in 'Created by':
            created_by_mapping[character] = Segment(character, Style.parse("#0d553c on #f4ed11"))

        created_by_grid2_mapping = mapping_defaults.copy()
        for character in 'warfront1':
            created_by_grid2_mapping[character] = Segment(character, Style.parse("black on #f4ed11"))

        created_by_grid3_mapping = mapping_defaults.copy()
        for character in 'at':
            created_by_grid3_mapping[character] = Segment(character, Style.parse("#0d553c on #f4ed11"))

        created_by_grid4_mapping = mapping_defaults.copy()
        for character in 'EliteScripts LLC.':
            created_by_grid4_mapping[character] = Segment(character, Style.parse("#05281d on #f4ed11"))

        created_by_pixels = Pixels.from_ascii(created_by_grid, created_by_mapping)
        created_by_pixels2 = Pixels.from_ascii(created_by_grid2, created_by_grid2_mapping)
        created_by_pixels3 = Pixels.from_ascii(created_by_grid3, created_by_grid3_mapping)
        created_by_pixels4 = Pixels.from_ascii(created_by_grid4, created_by_grid4_mapping)
        return Pixels.from_segments(
            logo_pixels._segments.segments + created_by_pixels._segments.segments + created_by_pixels2._segments.segments + created_by_pixels3._segments.segments + created_by_pixels4._segments.segments)
