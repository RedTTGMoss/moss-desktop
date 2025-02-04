"""Common code for writing tools.

Code originally from https://github.com/lschwetlick/maxio through
https://github.com/chemag/maxio .
"""

import math

# color_id to RGB conversion
# 1. we use "color_id" for a unique, proprietary ID for colors,
#   (see scene_stream.py):
remarkable_palette = {
    # BLACK = 0
    0: [0, 0, 0],
    # GRAY = 1
    1: [125, 125, 125],
    # WHITE = 2
    2: [255, 255, 255],
    # YELLOW = 3
    3: [255, 255, 99],
    # GREEN = 4
    4: [0, 255, 0],
    # PINK = 5
    5: [255, 20, 147],
    # BLUE = 6
    6: [0, 98, 204],
    # RED = 7
    7: [217, 7, 7],
    # GRAY_OVERLAP = 8
    8: [125, 125, 125],
}
MAGIC_PENCIL_SIZE = 44.6 * 2.3


class Pen:
    def __init__(self, base_width, base_color_id):
        self.base_width = base_width
        self.base_color = remarkable_palette[base_color_id]
        self.segment_length = 1000
        self.base_opacity = 1
        self.name = "Basic Pen"
        # initial stroke values
        self.stroke_linecap = "round"
        self.stroke_linejoin = "round"
        self.stroke_opacity = 1
        self.stroke_width = base_width
        self.stroke_color = base_color_id

    # note that the units of the points have had their units converted
    # in scene_stream.py
    # speed = d.read_float32() * 4
    # ---> replace speed with speed / 4 [input]
    # direction = 255 * d.read_float32() / (math.pi * 2)
    # ---> replace tilt with direction_to_tilt() [input]
    @classmethod
    def direction_to_tilt(cls, direction):
        return direction * (math.pi * 2) / 255

    # width = int(round(d.read_float32() * 4))
    # ---> replace width with width / 4 [input]
    # ---> replace width with 4 * width [output]
    # pressure = d.read_float32() * 255
    # ---> replace pressure with pressure / 255 [input]

    def get_segment_width(self, speed, direction, width, pressure, last_width):
        return self.base_width

    def get_segment_color(self, speed, direction, width, pressure, last_width):
        return "rgb" + str(tuple(self.base_color))

    def get_segment_opacity(self, speed, direction, width, pressure, last_width):
        return self.base_opacity

    def cutoff(self, value):
        """must be between 1 and 0"""
        value = 1 if value > 1 else value
        value = 0 if value < 0 else value
        return value

    @classmethod
    def create(cls, pen_nr, color_id, width):
        # print(f'----> create(cls, pen_nr: {pen_nr}, color_id: {color_id}, width: {width})')
        # Brush
        if pen_nr == 0 or pen_nr == 12:
            return Brush(width, color_id)
        # caligraphy
        elif pen_nr == 21:
            return Caligraphy(width, color_id)
        # Marker
        elif pen_nr == 3 or pen_nr == 16:
            return Marker(width, color_id)
        # BallPoint
        elif pen_nr == 2 or pen_nr == 15:
            return Ballpoint(width, color_id)
        # Fineliner
        elif pen_nr == 4 or pen_nr == 17:
            return Fineliner(width, color_id)
        # Pencil
        elif pen_nr == 1 or pen_nr == 14:
            return Pencil(width, color_id)
        # Mechanical Pencil
        elif pen_nr == 7 or pen_nr == 13:
            return MechanicalPencil(width, color_id)
        # Highlighter
        elif pen_nr == 5 or pen_nr == 18:
            width = 15
            return Highlighter(width, color_id)
        # Erase area
        elif pen_nr == 8:
            return Erase_Area(width, color_id)
        # Eraser
        elif pen_nr == 6:
            color_id = 2
            return Eraser(width, color_id)
        raise Exception(f'Unknown pen_nr: {pen_nr}')


class Fineliner(Pen):
    last = 0

    def __init__(self, base_width, base_color_id):
        super().__init__(base_width, base_color_id)
        self.base_width = base_width * MAGIC_PENCIL_SIZE
        self.name = "Fineliner"


class Ballpoint(Pen):
    def __init__(self, base_width, base_color_id):
        super().__init__(base_width, base_color_id)
        self.segment_length = 5
        self.name = "Ballpoint"
        self.alternate = 0  # 0 or 1
        """
        The pen is both solid but has different densities.
        To make this work, we alternate between the a solid smaller size and a opaque larger size
        """

    #     TODO: Maybe implement a way for pens to have densities

    def get_segment_width(self, speed, direction, width, pressure, last_width):
        segment_width = (0.5 + pressure / 100) + (1 * width / 4) - 0.5 * ((speed / 4) / 50)
        segment_width *= 2
        intensity = self.get_intensity(speed, pressure)
        return segment_width * (1 if self.alternate == 0 else intensity) * 2.3

    def get_intensity(self, speed, pressure):
        return self.cutoff((0.1 * - ((speed / 4) / 35)) + (1.2 * pressure / 255) + 0.5)

    def get_segment_opacity(self, speed, direction, width, pressure, last_width):
        intensity = self.get_intensity(speed, pressure)
        if self.alternate == 0:
            self.alternate = 1
            return intensity
        else:
            self.alternate = 0
            return 1

    # def get_segment_color(self, speed, direction, width, pressure, last_width):
    #     segment_color = tuple(int(v * alpha) for v in self.base_color)
    #     return "rgb"+str(tuple(segment_color))

    # def get_segment_opacity(self, speed, direction, width, pressure, last_width):
    #     segment_opacity = (0.2 * - ((speed / 4) / 35)) + (0.8 * pressure / 255)
    #     segment_opacity *= segment_opacity
    #     segment_opacity = self.cutoff(segment_opacity)
    #     return segment_opacity


class Marker(Pen):
    def __init__(self, base_width, base_color_id):
        super().__init__(base_width, base_color_id)
        self.segment_length = 3
        self.name = "Marker"

    def get_segment_width(self, speed, direction, width, pressure, last_width):
        segment_width = 3.36 * ((width / 4) - 0.4 * self.direction_to_tilt(direction)) + (0.1 * last_width)
        return segment_width


class Pencil(Pen):
    def __init__(self, base_width, base_color_id):
        super().__init__(base_width, base_color_id)
        self.segment_length = 2
        self.name = "Pencil"

    def get_segment_width(self, speed, direction, width, pressure, last_width):
        segment_width = 10 * ((((0.8 * self.base_width) + (0.5 * pressure / 255)) * (width / 3)) - (
                0.25 * self.direction_to_tilt(direction) ** 2.1) - (0.6 * (speed / 4) / 10))
        # segment_width = 1.3*(((self.base_width * 0.4) * pressure) - 0.5 * ((self.direction_to_tilt(direction) ** 0.5)) + (0.5 * last_width))
        max_width = self.base_width * MAGIC_PENCIL_SIZE
        segment_width = segment_width if segment_width < max_width else max_width
        return max(3, segment_width)

    def get_segment_opacity(self, speed, direction, width, pressure, last_width):
        segment_opacity = (0.1 * - ((speed / 4) / 35)) + (1 * pressure / 255)
        segment_opacity = self.cutoff(segment_opacity) - 0.1
        return segment_opacity


class MechanicalPencil(Pen):
    def __init__(self, base_width, base_color_id):
        super().__init__(base_width, base_color_id)
        self.base_width = self.base_width * MAGIC_PENCIL_SIZE * 1.01
        self.base_opacity = 0.85
        self.segment_length = 2
        self.name = "Mechanical Pencil"

    def get_segment_width(self, speed, direction, width, pressure, last_width):
        width = super().get_segment_width(speed, direction, width, pressure, last_width)
        return max(5, width)

    def get_segment_opacity(self, speed, direction, width, pressure, last_width):
        if direction / 255 < 0.5:
            return max(0.3, self.cutoff(speed / 50 * pressure / 255))
        else:
            return 0.85


class Brush(Pen):
    def __init__(self, base_width, base_color_id):
        super().__init__(base_width, base_color_id)
        self.segment_length = 2
        self.stroke_linecap = "round"
        self.opacity = 1
        self.name = "Brush"

    def get_segment_width(self, speed, direction, width, pressure, last_width):
        segment_width = 1.68 * (
                ((1 + (1.4 * pressure / 255)) * (width / 4)) - (0.5 * self.direction_to_tilt(direction)) - (
                (speed / 4) / 50))  # + (0.2 * last_width)
        return segment_width

    def get_segment_color(self, speed, direction, width, pressure, last_width):
        intensity = ((pressure / 255) ** 1.5 - 0.2 * ((speed / 4) / 50)) * 1.5
        intensity = self.cutoff(intensity)
        # using segment color not opacity because the dots interfere with each other.
        # Color must be 255 rgb
        segment_color = [int(intensity * i) for i in self.base_color]

        return "rgb" + str(tuple(segment_color))


class Highlighter(Pen):
    def __init__(self, base_width, base_color_id):
        super().__init__(base_width, base_color_id)
        self.stroke_linecap = "square"
        self.base_opacity = 0.25
        self.stroke_opacity = 0.15
        self.base_width = self.base_width * 10
        self.name = "Highlighter"


class Eraser(Pen):
    def __init__(self, base_width, base_color_id):
        super().__init__(base_width, base_color_id)
        self.stroke_linecap = "square"
        self.base_width = self.base_width * 2
        self.name = "Eraser"


class Erase_Area(Pen):
    def __init__(self, base_width, base_color_id):
        super().__init__(base_width, base_color_id)
        self.stroke_linecap = "square"
        self.base_opacity = 0
        self.name = "Erase Area"


class Caligraphy(Pen):
    def __init__(self, base_width, base_color_id):
        super().__init__(base_width, base_color_id)
        self.segment_length = 2
        self.name = "Calligraphy"

    def get_segment_width(self, speed, direction, width, pressure, last_width):
        segment_width = 2.16 * (((1 + pressure / 255) * (width / 4)) - 0.3 * self.direction_to_tilt(direction)) + (
                0.1 * last_width)
        return segment_width
