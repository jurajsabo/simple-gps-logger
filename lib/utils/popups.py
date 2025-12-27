from kivy.animation   import Animation
from kivy.clock       import Clock
from kivy.core.window import Window
from kivy.properties  import StringProperty, NumericProperty, ListProperty, ObjectProperty
from kivy.utils       import get_color_from_hex

from kivymd.app                  import MDApp
from kivymd.color_definitions    import colors
from kivymd.material_resources   import dp, DEVICE_TYPE
from kivymd.icon_definitions     import md_icons
from kivymd.theming_dynamic_text import get_contrast_text_color

from kivymd.uix.dialog   import MDDialog
from kivymd.uix.label    import MDLabel
from kivymd.uix.menu     import MDDropdownMenu
from kivymd.uix.snackbar import MDSnackbar, MDSnackbarCloseButton


class CustomDropdownMenu(MDDropdownMenu):
    menu_texts     = ListProperty(None)
    callback_owner = ObjectProperty(None)

    def __init__(self, **kwargs):
        super().__init__(**kwargs)

        menu_items = \
        [
            {
                'text':       self.menu_texts[i],
                'viewclass':  'OneLineListItem',
                'on_release': lambda x = self.menu_texts[i]: self.callback_owner.menu_callback(x)

            } for i in range(len(self.menu_texts))
        ]

        self.items      = menu_items
        self.hor_growth = 'left'
        self.ver_growth = 'down'
        self.position   = 'center'
        self.width      = dp(140)


class CustomDialog(MDDialog):
    def __init__(self, **kwargs):
        super().__init__(**kwargs)

        # Always manually control size
        self.size_hint = [None, None]

        # Default width/height setup
        self.width  = self.adjust_width()
        self.height = self.adjust_height()

        # Schedule dynamic update once layout is ready
        Clock.schedule_once(self.update_size, 0)

    def adjust_width(self):
        result = Window.width - self.width_offset
        return result

    def on_size(self, *args):
        self.update_size()

    def adjust_height(self):
        return self.ids.container.height

    def update_size(self, *args):
        self.width  = self.adjust_width()
        self.height = self.ids.container.height
