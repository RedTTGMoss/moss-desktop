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

    @property
    def value(self):
        if not (key := self.key):
            raise ValueError("The element must have a key to get the value")
        return self.settings_view.interactor.get(key)

    @value.setter
    def value(self, value):
        if not (key := self.key):
            raise ValueError("The element must have a key to set the value")
        return self.settings_view.interactor.set(key, value, self.VALUE_TYPE_KEY)


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
