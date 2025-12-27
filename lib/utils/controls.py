from kivy.properties import StringProperty

from kivymd.uix.menu   import MDDropdownMenu
from kivymd.uix.slider import MDSlider


class CustomSlider(MDSlider):
    '''
        A customized MDSlider with an added `id` property.

        This subclass extends the base `MDSlider` widget by introducing a
        string-based `id` property. This makes it easier to identify and
        bind slider instances programmatically (e.g., linking them with
        labels or saving settings).

        Attributes:
            id (StringProperty): A unique identifier for the slider.
    '''
    id = StringProperty(None)
    def __init__(self, **kwargs):
        '''
            Initialize the custom slider.
        '''
        super().__init__(**kwargs)


class CustomMenu(MDDropdownMenu):
    '''
        A customized MDDropdownMenu with an added `id` property.

        This subclass extends the base `MDDropdownMenu` to support a
        string-based `id` property, allowing for easier identification
        and management of dropdown menus in complex UI screens.

        Attributes:
            id (StringProperty): A unique identifier for the menu.
    '''
    id = StringProperty(None)
    def __init__(self, **kwargs):
        '''
            Initialize the custom dropdown menu.
        '''
        super().__init__(**kwargs)
