"""
Handbook generator package for VieTrueVoice v0.9.4 Defense & Study Handbook.
"""

from .chapter_13_inverted import add_chapter_13_inverted
from .chapters_1_to_3 import add_chapters_1_to_3
from .chapters_4_to_6 import add_chapters_4_to_6
from .chapters_7_to_9 import add_chapters_7_to_9
from .chapters_10_to_12 import add_chapters_10_to_12
from .diagrams import generate_all_handbook_diagrams
from .global_foundations import add_global_foundations
from .styles import (
    add_bullet_item,
    add_callout_box,
    add_defense_qa,
    add_figure,
    add_foundation_primer,
    add_heading_chapter,
    add_heading_part,
    add_heading_section,
    add_heading_subsection,
    add_omml_equation,
    add_rich_runs,
    add_styled_paragraph,
    add_styled_table,
    add_term_glossary,
    omml_delim,
    omml_frac,
    omml_r,
    omml_sqrt,
    omml_sub,
    omml_subsup,
    omml_sup,
    set_cell_background,
    set_cell_margins,
    set_table_borders,
)

__all__ = [
    "add_bullet_item",
    "add_callout_box",
    "add_chapter_13_inverted",
    "add_chapters_1_to_3",
    "add_chapters_4_to_6",
    "add_chapters_7_to_9",
    "add_chapters_10_to_12",
    "add_defense_qa",
    "add_figure",
    "add_foundation_primer",
    "add_global_foundations",
    "add_heading_chapter",
    "add_heading_part",
    "add_heading_section",
    "add_heading_subsection",
    "add_omml_equation",
    "add_rich_runs",
    "add_styled_paragraph",
    "add_styled_table",
    "add_term_glossary",
    "generate_all_handbook_diagrams",
    "omml_delim",
    "omml_frac",
    "omml_r",
    "omml_sqrt",
    "omml_sub",
    "omml_subsup",
    "omml_sup",
    "set_cell_background",
    "set_cell_margins",
    "set_table_borders",
]
