"""Convert blocks to svg file.

Code originally from https://github.com/lschwetlick/maxio through
https://github.com/chemag/maxio .
"""
import io
import re
from pathlib import Path
from traceback import print_exc
from typing import Union

from rm_api.defaults import RM_SCREEN_SIZE
from rm_lines.inker.document_size_tracker import DocumentSizeTracker
from .writing_tools import (
    Pen, PenException,
)
from ..rmscene import scene_items as si
from ..rmscene.scene_tree import SceneTree
from ..rmscene.tagged_block_common import CrdtId
from ..rmscene.text import TextDocument

TEXT_TOP_Y = -88
LINE_HEIGHTS = {
    # Tuned this line height using template grid -- it definitely seems to be
    # 71, rather than 70 or 72. Note however that it does interact a bit with
    # the initial text y-coordinate below.
    si.ParagraphStyle.BASIC: 100,
    si.ParagraphStyle.PLAIN: 71,
    si.ParagraphStyle.HEADING: 150,
    si.ParagraphStyle.BOLD: 70,
    si.ParagraphStyle.BULLET: 35,
    si.ParagraphStyle.BULLET2: 35,
    si.ParagraphStyle.CHECKBOX: 100,
    si.ParagraphStyle.CHECKBOX_CHECKED: 100,

    # There appears to be another format code (value 0) which is used when the
    # text starts far down the page, which case it has a negative offset (line
    # height) of about -20?
    #
    # Probably, actually, the line height should be added *after* the first
    # line, but there is still something a bit odd going on here.
}

# <html>
# <body>
# <div style="border: 1px solid grey; margin: 2em; float: left;">
# <svg xmlns="http://www.w3.org/2000/svg" height="$height" width="$width">
SVG_HEADER = """<?xml version="1.0" encoding="UTF-8"?>
<svg xmlns="http://www.w3.org/2000/svg" height="{height}" width="{width}" viewBox="{viewbox}">\n
"""


class SvgWriter:
    def __init__(self):
        self._output = io.StringIO()

    def write(self, text):
        self._output.write(text)

    def format(self, **kwargs):
        return self._output.getvalue().format(**kwargs)


def read_template_svg(template_path: Path) -> str:
    lines = template_path.read_text().splitlines()
    return "\n".join(lines[2:-1])


def remove_template_background(template: str):
    re_string = f'<rect[^>]*width="{RM_SCREEN_SIZE[0]}"[^>]*height="{RM_SCREEN_SIZE[1]}"[^>]*>'
    return re.sub(re.compile(re_string, re.DOTALL), '', template)


def tree_to_svg(tree: SceneTree, output_file, track_xy: DocumentSizeTracker, template: str = None):
    """Convert Tree to SVG."""
    if tree.scene_info and tree.scene_info.paper_size:
        track_xy.frame_width, track_xy.frame_height = tree.scene_info.paper_size
    output = SvgWriter()
    priority_lines = io.StringIO()  # For lines that should be drawn first AKA Highlighter

    # add svg header
    # output.write('<svg xmlns="http://www.w3.org/2000/svg">\n')
    output.write(SVG_HEADER)

    output.write(
        '    <g id="template" transform="translate({template_transform_x}, {template_transform_y})">\n'
        f'    <g id="template2" transform="rotate({{template_rotate}}, {RM_SCREEN_SIZE[0]}, 0)">\n'
        f'{{template}}\n    </g></g>\n')
    output.write('    <g id="p1" style="display:inline" transform="translate({x_shift},0)">\n')

    output.write('    <g id="priority">\n{priority_lines}\n    </g>\n')

    # output.write('        <filter id="blurMe"><feGaussianBlur in="SourceGraphic" stdDeviation="10" /></filter>\n')

    # These special anchor IDs are for the top and bottom of the page.
    anchor_pos = {
        CrdtId(0, 281474976710654): 270,
        CrdtId(0, 281474976710655): 700,
    }

    if tree.root_text is not None:
        draw_text(tree.root_text, output, anchor_pos, track_xy)

    draw_group(tree.root, output, anchor_pos, track_xy, priority_lines)

    # # Overlay the page with a clickable rect to flip pages
    # output.write('\n')
    # output.write('        <!-- clickable rect to flip pages -->\n')
    # output.write(f'        <rect x="0" y="0" width="{svg_doc_info.width}" height="{svg_doc_info.height}" fill-opacity="0"/>\n')
    # Closing page group
    output.write('    </g>\n')
    # END notebook
    output.write('</svg>\n')

    final = output.format(
        **track_xy.format_kwargs,
        priority_lines=priority_lines.getvalue(),
        template=remove_template_background(template) if template else ''
    )
    output_file.write(final)


def draw_group(item: si.Group, output, anchor_pos, track_xy: DocumentSizeTracker, priority_lines: io.StringIO):
    anchor_x = 0.0
    anchor_y = 0.0
    if item.anchor_id is not None:
        assert item.anchor_origin_x is not None
        anchor_x = item.anchor_origin_x.value
        if item.anchor_id.value in anchor_pos:
            anchor_y = anchor_pos[item.anchor_id.value]
    output.write(f'    <g id="{item.node_id}" transform="translate({track_xy.x(anchor_x)}, {track_xy.y(anchor_y)})">\n')
    for child_id in item.children:
        child = item.children[child_id]
        output.write(f'    <!-- child {child_id} -->\n')
        if isinstance(child, si.Group):
            draw_group(child, output, anchor_pos, track_xy=track_xy, priority_lines=priority_lines)
        elif isinstance(child, si.Line):
            try:
                draw_stroke(child, output, track_xy, priority_lines)
            except PenException:
                print_exc()
    output.write(f'    </g>\n')


def draw_stroke(item: si.Line, output, track_xy: DocumentSizeTracker, priority_lines: io.StringIO):
    # initiate the pen
    pen = Pen.create(item.tool.value, item.color.value, item.rgba_color, item.thickness_scale / 10)

    if item.tool == si.Pen.HIGHLIGHTER_2:
        output = priority_lines
    K = 5

    # BEGIN stroke
    output.write(
        f'        <!-- Stroke tool: {item.tool.name} color: {item.color.name} thickness_scale: {item.thickness_scale} -->\n')
    output.write('        <polyline ')
    output.write(
        f'style="fill:none;stroke:{pen.stroke_color};stroke-width:{pen.stroke_width / K};opacity:{pen.stroke_opacity}" ')
    output.write(f'stroke-linecap="{pen.stroke_linecap}" ')
    output.write(f'stroke-linejoin="{pen.stroke_linejoin}" ')
    output.write('points="')

    last_xpos = -1.
    last_ypos = -1.
    last_segment_width = segment_width = 0
    # Iterate through the point to form a polyline
    for point_id, point in enumerate(item.points):
        # align the original position
        xpos = point.x
        ypos = point.y
        if point_id % pen.segment_length == 0:
            segment_color = pen.get_segment_color(point.speed, point.direction, point.width, point.pressure,
                                                  last_segment_width)
            segment_width = pen.get_segment_width(point.speed, point.direction, point.width, point.pressure,
                                                  last_segment_width)
            segment_opacity = pen.get_segment_opacity(point.speed, point.direction, point.width, point.pressure,
                                                      last_segment_width)
            segment_blending_mode = pen.get_segment_blending_mode(point.speed, point.direction, point.width,
                                                                  point.pressure,
                                                                  last_segment_width)
            # print(segment_color, segment_width, segment_opacity, pen.stroke_linecap)
            # UPDATE stroke
            output.write('"/>\n')
            output.write('        <polyline ')
            output.write(
                f'style="fill:none; stroke:{segment_color} ;stroke-width:{segment_width / K:.3f};opacity:{segment_opacity};mix-blend-mode:{segment_blending_mode};" ')
            output.write(f'stroke-linecap="{pen.stroke_linecap}" ')
            output.write(f'stroke-linejoin="{pen.stroke_linejoin}" ')
            output.write('points="')
            if last_xpos != -1.:
                # Join to previous segment
                output.write(a := f'{track_xy.x(last_xpos):.3f},{track_xy.y(last_ypos, ):.3f} ')
        # store the last position
        last_xpos = xpos
        last_ypos = ypos
        last_segment_width = segment_width

        # BEGIN and END polyline segment
        output.write(f'{track_xy.x(xpos):.3f},{track_xy.y(ypos):.3f} ')

    # END stroke
    output.write('" />\n')


def draw_text(text: Union[si.Text, TextDocument], output, anchor_pos, track_xy: DocumentSizeTracker):
    if isinstance(text, si.Text):
        text = TextDocument.from_scene_item(text)
    output.write('    <g class="root-text" style="display:inline">\n')

    # add some style to get readable text
    output.write('''
    <style>
        text.heading {{
            font: 14pt serif;
        }}
        text.bold {{
            font: 8pt sans-serif bold;
        }}
        text, text.plain {{
            font: 7pt sans-serif;
        }}
    </style>
    ''')

    y_offset = TEXT_TOP_Y
    pos_x = 0
    pos_y = 0
    for paragraph in text.contents:
        fmt = paragraph.style.value
        line = paragraph.contents[0].s if paragraph.contents else None
        if line:
            ids = paragraph.contents[0].i
        else:
            ids = []
        y_offset += LINE_HEIGHTS[fmt]

        pos_x += 0
        pos_y += y_offset
        cls = fmt.name.lower()
        if line:
            output.write(f'        <!-- Text line char_id: {ids[0]} -->\n')
            output.write(
                f'        <text x="{track_xy.x(pos_x)}" y="{track_xy.y(pos_y)}" class="{cls}">{line.strip()}</text>\n')

        # Save y-coordinates of potential anchors
        for k in ids:
            anchor_pos[k] = pos_y

    output.write('    </g>\n')
