from kivymd.uix.behaviors.toggle_behavior import MDToggleButton
from kivymd.uix.button                    import MDFillRoundFlatIconButton
from kivymd.uix.button.button             import ButtonElevationBehaviour, MDFlatButton
from kivymd.material_resources            import dp


class CustomToggleButton(MDFillRoundFlatIconButton, MDToggleButton, ButtonElevationBehaviour):
    '''
        A custom rounded toggle button with elevation and dynamic theming.
        This button combines:
          - `MDFillRoundFlatIconButton`: A Material Design round flat button.
          - `MDToggleButton`: Toggle behavior for on/off states.
          - `ButtonElevationBehaviour`: Adds shadow and elevation effects.

        Features:
            - Enlarged padding and icon size.
            - Rounded button style.
            - Custom elevation with shadow radius.
            - Binds to theme updates so colors change automatically.
    '''
    def __init__(self, *args, **kwargs):
        '''
            Initialize the custom toggle button and apply default styles.
        '''
        super().__init__(*args, **kwargs)

        self.padding = [dp(12), dp(0), dp(0), dp(1)]
        self.icon_size = dp(25)
        self.rounded_button = True
        self.text = ' '

        self.shadow_offset = [0, 0]
        self.shadow_radius = self._radius * 3
        self.elevation = 2

        self._min_height = dp(60)
        self._min_width  = dp(60)

        # Rebind theming colors so they change when theme_cls updates
        self.theme_cls.bind(primary_color = self._update_colors)
        self.theme_cls.bind(primary_dark  = self._update_colors)

        self._update_colors()

    def _update_colors(self, *args):
        '''
            Update button colors when the application's theme changes.
        '''
        self.background_normal = self.theme_cls.primary_color
        self.background_down   = self.theme_cls.primary_dark
        self.font_color_normal = self.theme_cls.primary_color

        # Force apply current theme colors immediately
        self._update_bg(self, self.state)

class CustomButton(MDFillRoundFlatIconButton, ButtonElevationBehaviour):
    '''
        A custom rounded flat button with elevation and consistent styling.
        This button provides a consistent style across the application with:
            - Enlarged padding and icon size.
            - Rounded appearance.
            - Shadow and elevation effects.
    '''
    def __init__(self, *args, **kwargs):
        '''
            Initialize the custom button and apply default styles.
        '''
        super().__init__(*args, **kwargs)
        self.padding = [dp(12), dp(0), dp(0), dp(1)]
        self.icon_size = dp(25)
        self.rounded_button = True
        self.text = ' '

        self.shadow_offset = [0, 0]
        self.shadow_radius = self._radius * 3
        self.elevation = 2

        self._min_height = dp(60)
        self._min_width = dp(60)


class CustomFlatButton(MDFlatButton):
    '''
        A custom flat button with theme-aware text color.

        This button extends the standard `MDFlatButton` to automatically
        update its text color whenever the application's theme changes.
    '''
    def __init__(self, *args, **kwargs):
        '''
            Initialize the custom flat button and bind to theme updates.
        '''
        super().__init__(*args, **kwargs)

        self.theme_text_color = 'Custom'
        self.theme_cls.bind(primary_color = self._update_colors)
        self._update_colors()

    def _update_colors(self, *args):
        '''
            Update text color when the application's theme changes.
            Args:
                *args: Unused, passed by the Kivy theme binding system.
        '''
        self.text_color = self.theme_cls.primary_color
