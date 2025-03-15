from .view_objects import *
from ..scrollable_view import ScrollableView

if TYPE_CHECKING:
    from . import Settings


class SettingsView(ScrollableView):
    LAYER = pe.BEFORE_LOOP_LAYER
    VIEW_OBJECTS = {
        'title': Title,
        'subtitle': Subtitle,
        'text': Text,
        'subtext': Subtext,
    }

    def __init__(self, settings: 'Settings', xml_tree, interactor=None):
        self.settings = settings
        self.interactor = interactor
        self.elements = []

        self.AREA = (
            settings.ratios.main_menu_side_bar_width, 0, settings.width - settings.ratios.main_menu_side_bar_width,
            settings.height
        )

        super().__init__(settings.parent_context)

        for element in xml_tree:
            tag = element.tag
            if tag in self.VIEW_OBJECTS:
                self.elements.append(self.VIEW_OBJECTS[tag](element, self))
            elif self.gui.config.debug:
                print(f"Unknown view tag: {tag}")

    def loop(self):
        y = self.top
        for element in self.elements:
            y += element.display(0, y)
        self.bottom = y

    def handle_resize(self):
        self.resize((
            self.settings.width - self.settings.ratios.main_menu_side_bar_width,
            self.settings.height
        ))

        for element in self.elements:
            element.on_resize()
