# -*- coding: utf-8 -*-
"""
Handbook generator package for ViTrueVoice v0.9.4 Defense & Study Handbook.
"""
from .styles import (
    set_cell_background,
    set_cell_margins,
    set_table_borders,
    add_rich_runs,
    add_callout_box,
    add_prerequisite_box,
    add_foundation_primer,
    add_term_glossary,
    add_figure,
    omml_r,
    omml_frac,
    omml_sub,
    omml_sup,
    omml_subsup,
    omml_sqrt,
    omml_delim,
    add_omml_equation,
    add_styled_paragraph,
    add_bullet_item,
    add_heading_part,
    add_heading_chapter,
    add_heading_section,
    add_heading_subsection,
    add_styled_table,
)
from .diagrams import generate_all_handbook_diagrams
from .global_foundations import add_global_foundations
from .chapters_1_to_3 import add_chapters_1_to_3
from .chapters_4_to_6 import add_chapters_4_to_6
from .chapters_7_to_9 import add_chapters_7_to_9
from .chapters_10_to_12 import add_chapters_10_to_12
from .chapter_13_inverted import add_chapter_13_inverted
