from abc import abstractmethod, ABC
from typing import TYPE_CHECKING

import pygameextra as pe

from gui.defaults import Defaults
from gui.helpers import dynamic_text
from . import xml_tools as tools

if TYPE_CHECKING:
    from gui import GUI
    from .settings_view import SettingsView


class ViewObject(ABC):
    VALUE_TYPE_KEY = 'any'

    def __init__(self, element, settings_view: 'SettingsView'):
        self.gui: 'GUI' = settings_view.settings.parent_context
        self.settings_view = settings_view
        self.element = element

    def on_resize(self):
        ...

    @abstractmethod
    def display(self, x, y) -> int:
        """
        Display the object at the given x and y coordinates
        :param x: x coordinate
        :param y: y coordinate
        :return: The height of the object
        """
        ...

    @property
    def id(self) -> str:
        return self.element.get('id')

    @property
    def key(self) -> str:
        return self.element.get('key')

    def make_full_text(self, text):
        return pe.Text(
            text,
            Defaults.XML_FULL_TEXT_FONT,
            self.gui.ratios.xml_full_text_size,
            colors=Defaults.TEXT_COLOR
        )

    # Access to the value of the current setting if applicable
    @property
    def value(self):
        if not (key := self.key):
            raise ValueError("The element must have a key to get the value")
        return self.settings_view.interactor.get(key)

    @value.setter
    def value(self, value):
        if not (key := self.key):
            raise ValueError("The element must have a key to set the value")
        self.settings_view.interactor.set(key, value, self.VALUE_TYPE_KEY)

    # Quick getters
    @property
    def end(self):
        """The end of the settings view"""
        return self.settings_view.width

    @property
    def ratios(self):
        """The aspect ratios of the GUI"""
        return self.settings_view.gui.ratios

    @property
    def delta_time(self):
        """The delta time of the GUI"""
        return self.settings_view.gui.delta_time


class GenericText(ViewObject, ABC):
    SIZE = 'xml_title_size'
    PADDING = 'xml_title_padding'
    FONT = 'XML_TITLE_FONT'
    COLORS = 'TEXT_COLOR'
    ALPHA = 255

    text: pe.Text

    def __init__(self, element, settings_view):
        self.inverted = element.get("inverted")
        super().__init__(element, settings_view)
        self.make_texts()

    def make_texts(self):
        formatted = dynamic_text(
            self.element.text,
            self.font, self.size,
            self.settings_view.width - self.padding_x - self.padding_end,
            new_line=True
        )
        self.text = pe.Text(
            formatted,
            self.font, self.size,
            colors=self.colors
        )
        if self.ALPHA != 255:
            self.text.obj.set_alpha(self.ALPHA)

    def on_resize(self):
        self.make_texts()

    @property
    def padding_x(self):
        return getattr(self.gui.ratios, f'{self.PADDING}_x')

    @property
    def padding_end(self):
        return 0

    @property
    def padding_y(self):
        return getattr(self.gui.ratios, f'{self.PADDING}_y')

    @property
    def padding_bottom(self):
        return 0

    @property
    def size(self):
        return getattr(self.gui.ratios, self.SIZE)

    @property
    def font(self):
        return getattr(Defaults, self.FONT)

    @property
    def colors(self):
        fore, back = getattr(Defaults, self.COLORS)
        different_fore = self.element.get('fore')
        different_back = self.element.get('back')

        if different_fore:
            fore = tools.get_single_color(different_fore)
        if different_back:
            back = tools.get_single_color(different_back)

        if self.inverted:
            return fore if different_fore else tuple(
                255 - c if i < 3 else c
                for i, c in enumerate(fore)
            ), back if different_back else tuple(
                255 - c if i < 3 else c
                for i, c in enumerate(back)
            )
        return fore, back

    def display(self, x, y):
        self.text.rect.topleft = (x + self.padding_x, y + self.padding_y)
        self.text.display()
        return self.text.rect.height + self.padding_y + self.padding_bottom


class Title(GenericText):
    pass


class Subtitle(GenericText):
    SIZE = 'xml_subtitle_size'
    PADDING = 'xml_subtitle_padding'
    FONT = 'XML_SUBTITLE_FONT'


class Text(GenericText):
    SIZE = 'xml_text_size'
    PADDING = 'xml_text_padding'
    FONT = 'XML_TEXT_FONT'


class Subtext(GenericText):
    SIZE = 'xml_subtext_size'
    PADDING = 'xml_subtext_padding'
    FONT = 'XML_SUBTEXT_FONT'
    ALPHA = 150


class OptionText(GenericText):
    SIZE = 'xml_option_size'
    PADDING = 'xml_option_padding'
    FONT = 'XML_OPTION_FONT'


class Toggle(OptionText):
    COLOR_OFF = 'BACKGROUND'
    COLOR_ON = 'SELECTED'
    HANDLE_OFF = 'SELECTED'
    HANDLE_ON = 'BACKGROUND'
    SPEED = 5

    left: int
    right: int
    left_end: int
    right_end: int
    handle_left: int
    handle_right: int

    def __init__(self, element, settings_view: 'SettingsView'):
        super().__init__(element, settings_view)

        self.outer_rect = pe.Rect(
            0, 0,
            self.ratios.xml_toggle_outer_width,
            self.ratios.xml_toggle_outer_height
        )

        self.inner_rect = pe.Rect(
            0, 0,
            self.ratios.xml_toggle_inner_width,
            self.ratios.xml_toggle_inner_height
        )

        self.align_toggle_handle()

        self.t = 0.99 if self.value else 0.01  # leave some space to correct positions
        self.icon = self.gui.icons['checkmark'].copy()
        self.icon_rect = pe.Rect(0, 0, *self.icon.size)

    def align_toggle_handle(self):
        self.outer_rect.topleft = (0, 0)
        self.inner_rect.center = self.outer_rect.center

        self.left = self.inner_rect.left
        self.right = self.inner_rect.right

        self.left_end = self.inner_rect.left + self.inner_rect.height
        self.right_end = self.inner_rect.right - self.inner_rect.height

        self.handle_left = self.left
        self.handle_right = self.left_end

    def on_resize(self):
        super().on_resize()
        self.align_toggle_handle()

    @property
    def color_on(self):
        if different_color := self.element.get('color_on'):
            color = tools.get_single_color(different_color)
        else:
            color = getattr(Defaults, self.COLOR_ON)

        return tools.invert_color(color) if self.inverted and not different_color else color

    @property
    def color_off(self):
        if different_color := self.element.get('color_off'):
            color = tools.get_single_color(different_color)
        else:
            color = getattr(Defaults, self.COLOR_OFF)

        return tools.invert_color(color) if self.inverted and not different_color else color

    @property
    def padding_end(self):
        return (
                self.ratios.xml_toggle_outer_width +
                self.ratios.xml_toggle_margin * 2
        )

    @property
    def handle_off(self):
        if different_color := self.element.get('handle_off'):
            color = tools.get_single_color(different_color)
        else:
            color = getattr(Defaults, self.HANDLE_OFF)

        return tools.invert_color(color) if self.inverted and not different_color else color

    @property
    def handle_on(self):
        if different_color := self.element.get('handle_on'):
            color = tools.get_single_color(different_color)
        else:
            color = getattr(Defaults, self.HANDLE_ON)

        return tools.invert_color(color) if self.inverted and not different_color else color

    @property
    def handle_blend(self):
        return self.handle_off if self.t == 0 else self.handle_on

    @property
    def color_blend(self):
        return tools.lerp_color(self.color_off, self.color_on, self.t)

    @property
    def handle_width(self):
        return self.handle_right - self.handle_left

    @property
    def inner_rect_animation(self):
        return pe.Rect(
            self.outer_rect.left + self.handle_left, self.inner_rect.top,
            self.handle_width, self.inner_rect.height
        )

    def toggle(self):
        self.value = not self.value

    def handle_animation(self):
        if self.value and self.t < 1:
            self.handle_left = tools.lerp(self.left, self.right_end, tools.ease_in_quad(self.t))
            self.handle_right = tools.lerp(self.left_end, self.right, tools.ease_out_quad(self.t))
            if self.t > 0.5:
                self.icon.set_alpha(int(255 * tools.lerp(-1, 1, self.t)))  # go from 0 to 1 after t=0.5
            self.t += self.delta_time * self.SPEED
            if self.t >= 1:
                self.t = 1
                self.handle_left = self.right_end
                self.handle_right = self.right
                self.icon.set_alpha(255)
        elif not self.value and self.t > 0:
            self.handle_left = tools.lerp(self.right_end, self.left, 1 - tools.ease_in_quad(self.t))
            self.handle_right = tools.lerp(self.right, self.left_end, 1 - tools.ease_out_quad(self.t))
            if self.t > 0.5:
                self.icon.set_alpha(int(255 * tools.lerp(-1, 1, self.t)))  # go from 0 to 1 after t=0.5
            self.t -= self.delta_time * self.SPEED
            if self.t <= 0:
                self.t = 0
                self.handle_left = self.left
                self.handle_right = self.left_end

    def display(self, x, y) -> int:
        # Draw the text
        height = super().display(x, y)
        centery = self.text.rect.centery

        # Center the toggle on the right
        self.outer_rect.midright = (self.end - self.ratios.xml_toggle_margin, centery)
        self.inner_rect.center = self.outer_rect.center

        # Handle animating
        self.handle_animation()

        # Draw the toggle
        if self.t > 0:
            pe.draw.rect(  # Outer fill
                self.color_blend,
                self.outer_rect,
                edge_rounding=self.ratios.xml_toggle_outer_edge_rounding
            )

        pe.draw.rect(  # Outer outline
            self.color_on,
            self.outer_rect,
            w=self.ratios.line,
            edge_rounding=self.ratios.xml_toggle_outer_edge_rounding
        )

        handle_rect = self.inner_rect_animation
        self.icon_rect.center = handle_rect.center

        if self.t > 0:
            pe.draw.rect(  # Inner fill
                self.handle_on,
                handle_rect,
                w=0,
                edge_rounding=self.ratios.xml_toggle_inner_edge_rounding
            )

        pe.draw.rect(  # Inner outline
            self.handle_off,
            handle_rect,
            w=self.ratios.line,
            edge_rounding=self.ratios.xml_toggle_inner_edge_rounding
        )

        if self.t > 0.5:
            self.icon.display(self.icon_rect.topleft)

        # Handle the button
        pe.button.action(self.ratios.pad_button_rect(self.outer_rect), action=self.toggle, name=f'TOGGLE<{id(self)}>')

        return height
