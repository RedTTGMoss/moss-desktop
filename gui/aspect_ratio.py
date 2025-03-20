import pygameextra as pe


class Ratios:
    def __init__(self, scale):
        """
        Keep in mind that the aspect ratio is 0.75
        The default height is 1000
        The default width is 750 due to the aspect ratio
        These values are then multiplied by the scale
        """

        self.scale = scale

        self.line = int(2 * scale)
        self.seperator = self.line * 2

        # GENERAL
        self.bottom_bar_height = int(40 * scale)
        self.bottom_loading_bar_height = int(10 * scale)
        self.bottom_bar_size = int(15 * scale)
        self.bottom_loading_bar_padding = (self.bottom_bar_height - self.bottom_loading_bar_height) / 2
        self.bottom_loading_bar_rounding = int(5 * scale)
        self.bottom_loading_bar_width = int(100 * scale)

        # DEBUG
        self.small_debug_text_size = int(10 * scale)
        self.debug_text_size = int(15 * scale)

        # LOADER
        self.loader_logo_text_size = int(50 * scale)
        self.loader_motivational_text_size = int(15 * scale)
        self.loader_loading_bar_width = int(200 * scale)
        self.loader_loading_bar_height = int(10 * scale)
        self.loader_loading_bar_big_width = int(500 * scale)
        self.loader_loading_bar_big_height = int(30 * scale)
        self.loader_loading_bar_padding = int(20 * scale)
        self.loader_loading_bar_rounding = int(10 * scale)
        self.loader_loading_bar_thickness = int(2 * scale)

        # CODE SCREEN
        self.code_screen_header_padding = int(50 * scale)
        self.code_screen_spacing = int(10 * scale)
        self.code_screen_info_size = int(30 * scale)

        # INSTALLER
        self.installer_buttons_width = int(280 * scale)  # FOR BOTH BUTTONS
        self.installer_buttons_height = int(35 * scale)
        self.installer_buttons_size = int(25 * scale)  # text size
        self.installer_buttons_padding = int(30 * scale)  # IN BETWEEN THE BUTTONS

        # MAIN MENU
        self.main_menu_top_height = int(64 * scale)
        self.main_menu_side_bar_width = int(185 * scale)
        self.main_menu_top_padding = int(21 * scale)
        self.main_menu_my_files_folder_padding = int(28 * scale)
        self.main_menu_path_padding = int(0 * scale)
        self.main_menu_path_first_padding = int(5 * scale)
        self.main_menu_folder_padding = int(6 * scale)
        self.main_menu_folder_margin_x = int(12 * scale)
        self.main_menu_folder_margin_y = int(20 * scale)
        self.main_menu_document_padding = int(15 * scale)
        self.main_menu_document_rounding = 0.1 * scale  # 10% of the width
        self.main_menu_folder_distance = int(184 * scale)
        self.main_menu_folder_height_distance = int(41 * scale)
        self.main_menu_folder_height_last_distance = int(38 * scale)
        self.main_menu_document_height_distance = int(50 * scale)
        self.main_menu_document_width = int(168 * scale)
        self.main_menu_document_height = int(223 * scale)
        self.main_menu_x_padding = int(17 * scale)
        self.main_menu_button_padding = self.main_menu_x_padding / 2
        self.main_menu_button_margin = self.main_menu_button_padding
        self.main_menu_my_files_size = int(24 * scale)
        self.main_menu_document_title_height_margin = int(8 * scale)
        self.main_menu_document_title_padding = int(4 * scale)
        self.main_menu_document_cloud_padding = int(20 * scale)  # 10 on each size (left and right) / (top and bottom)
        self.main_menu_path_size = int(15.8 * scale)
        self.main_menu_bar_size = self.main_menu_path_size
        self.main_menu_bar_padding = int(20 * scale)
        self.document_sync_progress_height = int(8 * scale)
        self.document_sync_progress_margin = int(10 * scale)
        self.document_sync_progress_rounding = int(8 * scale)
        self.document_sync_progress_outline = int(3 * scale)

        # Document Tree View
        self.document_tree_view_document_title_size = int(14 * scale)
        self.document_tree_view_folder_title_size = int(14 * scale)
        self.document_tree_view_list_text_height = int(60 * scale)
        self.document_tree_view_small_info_size = int(12 * scale)

        # Document Viewer
        self.document_viewer_top_draggable_height = int(48 * scale)  # Accurate to device
        self.document_viewer_top_arrow_rounding = int(20 * scale)
        self.document_viewer_loading_square = int(100 * scale)
        self.document_viewer_loading_circle_radius = int(5 * scale)
        self.document_viewer_error_font_size = int(20 * scale)
        self.document_viewer_top_margin = int(10 * scale)
        self.document_viewer_top_rounding = int(5 * scale)
        self.document_viewer_top_outline = int(2 * scale)
        self.document_viewer_hint_size = int(15 * scale)
        self.document_viewer_top_height = int(40 * scale)
        self.document_viewer_notebook_shadow_size = int(10 * scale)
        self.document_viewer_notebook_shadow_radius = int(7 * scale)

        # Import Screen
        self.import_screen_button_padding = int(20 * scale)
        self.import_screen_button_margin = int(20 * scale) + self.import_screen_button_padding
        self.import_screen_button_size = int(18 * scale)

        # Name Field Screen
        self.field_screen_title_size = int(30 * scale)
        self.field_screen_input_height = int(40 * scale)
        self.field_screen_input_size = int(20 * scale)
        self.field_screen_input_padding = int(30 * scale)

        # Titled Mixin
        self.titled_mixin_title_size = int(30 * scale)
        self.titled_mixin_title_padding = int(25 * scale)
        self.titled_mixin_margin = int(8 * scale)

        # Popup
        self.popup_description_size = int(15 * scale)
        self.popup_description_padding = int(10 * scale)

        # Settings / XML
        self.xml_title_size = int(30 * scale)
        self.xml_title_padding_x = int(15 * scale)
        self.xml_title_padding_y = int(25 * scale)

        self.xml_subtitle_size = int(20 * scale)
        self.xml_subtitle_padding_x = int(30 * scale)
        self.xml_subtitle_padding_y = 0

        self.xml_text_size = int(15 * scale)
        self.xml_text_padding_x = int(15 * scale)
        self.xml_text_padding_y = int(20 * scale)

        self.xml_subtext_size = int(14 * scale)
        self.xml_subtext_padding_x = int(20 * scale)
        self.xml_subtext_padding_y = int(7 * scale)

        self.xml_option_size = int(17 * scale)
        self.xml_option_padding_x = int(7 * scale)
        self.xml_option_padding_y = int(10 * scale)

        self.xml_full_text_size = int(14 * scale)

    def pixel(self, value):
        return max(1, int(value * self.scale))

    def pad_button_rect(self, rect: pe.Rect, amount: int = 20):
        return rect.inflate(self.pixel(amount), self.pixel(amount))

    @property
    def outline(self):
        return self.pixel(3)

    def rm_scaled(self, frame_width: int):
        # Moss runs on an initial height of 1000
        # But remarkable runs on a different initial height, also depends on the device (paper size)
        # This requires some modifications if we want to scale remarkable docs to the Moss scale
        return self.scale * 1000 / frame_width
