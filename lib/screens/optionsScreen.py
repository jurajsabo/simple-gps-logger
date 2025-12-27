from kivy            import platform
from kivy.clock      import Clock
from kivy.properties import StringProperty, BoundedNumericProperty, BooleanProperty

from kivymd.app                import MDApp
from kivymd.material_resources import dp
from kivymd.toast              import toast

from kivymd.uix.boxlayout        import MDBoxLayout
from kivymd.uix.button           import MDFillRoundFlatButton
from kivymd.uix.floatlayout      import MDFloatLayout
from kivymd.uix.navigationdrawer import MDNavigationDrawerDivider
from kivymd.uix.screen           import MDScreen
from kivymd.uix.scrollview       import MDScrollView

from lib.utils.controls import CustomSlider
from config import default_settings, params, toast_duration
from lib.utils.label    import CustomLabel, MockBanner
from lib.utils.popups   import CustomDropdownMenu
from lib.utils.saver    import Saver
from lib.utils.units    import meters_to_gpx_distance, units_to_gpx_distance

if platform == 'android':
    from android.runnable import run_on_ui_thread
    from jnius import autoclass

class OptionsScreen(MDScreen, Saver):
    # Params init
    interval = BoundedNumericProperty(default_settings['interval']['value'], min = params['interval']['min'], max = params['interval']['max'])
    distance = BoundedNumericProperty(default_settings['distance']['value'], min = params['distance']['min'], max = params['distance']['max'])

    screen = StringProperty(default_settings['screen']['value'])
    theme  = StringProperty(default_settings['theme'] ['value'])
    format = StringProperty(default_settings['format']['value'])
    units  = StringProperty(default_settings['units'] ['value'])

    shutdown = BooleanProperty(False)

    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        print('[OPTION]', 'init')

        # Storage init
        self.storage = default_settings

        # Main layout
        main_layout = MDBoxLayout(orientation = 'vertical', spacing = 0)

        # Mock banner
        self.mock_banner = MockBanner()

        # Remaining layout
        main_layout.add_widget(self.mock_banner)
        main_layout.add_widget \
        (

            MDScrollView \
            (

                MDBoxLayout \
                (
                    CustomLabel(text = 'time interval between updates'),
                    MDBoxLayout \
                    (
                        CustomLabel \
                        (
                            text        = self.label_interval_value(self.interval),
                            size_hint_x = 0.2
                        ),
                        CustomSlider \
                        (
                            id          = 'INTERVAL',
                            min         = params['interval']['min'],
                            max         = params['interval']['max'],
                            step        = 1,
                            hint        = False,
                            value       = self.interval,
                            disabled    = False,
                            size_hint_x = 0.8
                        ),
                        size_hint_y = None,
                        height      = dp(64)
                    ),
                    MDNavigationDrawerDivider(padding = [dp(0), dp(0), dp(3), dp(0)]),
                    CustomLabel(text = 'distance between updates'),
                    MDBoxLayout \
                    (
                        CustomLabel \
                        (
                            text        = self.label_distance_value(self.distance),
                            size_hint_x = 0.2
                        ),
                        CustomSlider \
                        (
                            id          = 'DISTANCE',
                            min         = params['distance']['min'],
                            max         = params['distance']['max'],
                            step        = 10,
                            hint        = False,
                            value       = self.distance,
                            disabled    = False,
                            size_hint_x = 0.8
                        ),
                        size_hint_y = None,
                        height      = dp(64)
                    ),
                    MDNavigationDrawerDivider(padding = [dp(0), dp(0), dp(3), dp(0)]),
                    CustomLabel(text = 'screen'),
                    MDFloatLayout \
                    (
                        MDFillRoundFlatButton \
                        (
                            id         = 'SCREEN',
                            text       = self.screen,
                            on_press   = self.on_btn_press,
                            _min_width = dp(110),
                            pos_hint   = {'right': 1, 'center_y': 0.6},  # adjust 0.6 to move it up
                            disabled   = False
                        ),
                        size_hint_y = None,
                        height      = dp(2)
                    ),
                    MDNavigationDrawerDivider(padding = [dp(0), dp(0), dp(3), dp(0)]),
                    CustomLabel(text = 'theme'),
                    MDFloatLayout \
                    (
                        MDFillRoundFlatButton \
                        (
                            id         = 'THEME',
                            text       = self.theme,
                            on_press   = self.on_btn_press,
                            _min_width = dp(110),
                            pos_hint   = {'right': 1, 'center_y': 0.6},  # adjust 0.6 to move it up
                            disabled   = False
                        ),
                        size_hint_y = None,
                        height      = dp(2)
                    ),
                    MDNavigationDrawerDivider(padding = [dp(0), dp(0), dp(3), dp(0)]),
                    CustomLabel(text = 'display units'),
                    MDFloatLayout \
                    (
                        MDFillRoundFlatButton \
                        (
                            id         = 'UNITS',
                            text       = self.units,
                            on_press   = self.on_btn_press,
                            _min_width = dp(110),
                            pos_hint   = {'right': 1, 'center_y': 0.6},
                            disabled   = False
                        ),
                        size_hint_y = None,
                        height      = dp(2)
                    ),
                    MDNavigationDrawerDivider(padding = [dp(0), dp(0), dp(3), dp(0)]),
                    CustomLabel(text = 'track format'),
                    MDFloatLayout \
                    (
                        MDFillRoundFlatButton \
                        (
                            id         = 'FORMAT',
                            text       = self.format,
                            on_press   = self.on_btn_press,
                            _min_width = dp(110),
                            pos_hint   = {'right': 1, 'center_y': 0.6},
                            disabled   = False
                        ),
                        size_hint_y = None,
                        height      = dp(2)
                    ),
                    MDNavigationDrawerDivider(padding = [dp(0), dp(0), dp(3), dp(0)]),
                    CustomLabel(text = 'shutdown'),
                    MDFloatLayout \
                    (
                        MDFillRoundFlatButton \
                        (
                            id         = 'SHUTDOWN',
                            text       = 'exit',
                            on_press   = self.on_btn_press,
                            _min_width = dp(110),
                            pos_hint   = {'right': 1, 'center_y': 0.6},
                            disabled   = False
                        ),
                        size_hint_y = None,
                        height      = dp(2)
                    ),
                    MDNavigationDrawerDivider(padding = [dp(0), dp(0), dp(3), dp(0)]),
                    CustomLabel(text = 'default settings'),
                    MDFloatLayout \
                    (
                        MDFillRoundFlatButton \
                        (
                            id         = 'RESET',
                            text       = 'reset',
                            on_press   = self.on_btn_press,
                            _min_width = dp(110),
                            pos_hint   = {'right': 1, 'center_y': 0.6},
                            disabled   = False
                        ),
                        size_hint_y = None,
                        height      = dp(2)

                    ),
                    orientation = 'vertical',
                    size_hint_y = None,
                    padding     = [dp(30), dp(30)],
                    spacing     = dp(25)
                ),
                do_scroll_y = True,
                bar_width   = dp(4),
                scroll_type = ['bars', 'content']
            ),


        )
        # Add the main layout to screen
        self.add_widget(main_layout)

        # layout
        self.layout = main_layout.children[0].children[0]

        # update interval
        self.label_interval  = self.layout.children[21].children[1]
        self.slider_interval = self.layout.children[21].children[0]

        # update distance
        self.label_distance  = self.layout.children[18].children[1]
        self.slider_distance = self.layout.children[18].children[0]

        # screen
        self.button_screen = self.layout.children[15].children[0]
        self.texts_screen  = params['screen']
        self.menu_screen   = CustomDropdownMenu \
        (
            menu_texts     = self.texts_screen,
            callback_owner = self,
            caller         = self.button_screen  # Set the caller to the button that was clicked on
        )

        # theme
        self.button_theme = self.layout.children[12].children[0]
        self.texts_theme  = params['theme']
        self.menu_theme   = CustomDropdownMenu \
        (
            menu_texts     = self.texts_theme,
            callback_owner = self,
            caller         = self.button_theme  # Set the caller to the button that was clicked on
        )

        # units
        self.button_units = self.layout.children[9].children[0]
        self.texts_units  = params['units']
        self.menu_units   = CustomDropdownMenu \
        (
            menu_texts     = self.texts_units,
            callback_owner = self,
            caller         = self.button_units  # Set the caller to the button that was clicked on
        )

        # record format
        self.button_format = self.layout.children[6].children[0]
        self.texts_format  = params['format']
        self.menu_format   = CustomDropdownMenu \
        (
            menu_texts     = self.texts_format,
            callback_owner = self,
            caller         = self.button_format  # Set the caller to the button that was clicked on
        )

        # shutdown & reset
        self.button_shutdown = self.layout.children[3].children[0]
        self.button_reset    = self.layout.children[0].children[0]

        # Bind the slider value to update text and property
        self.slider_interval.bind(value = self.on_controls_value_change)
        self.slider_distance.bind(value = self.on_controls_value_change)

        # Bind the layout's height to its minimum_height (to the total height of all its children)
        self.layout.bind(minimum_height = self.layout.setter('height'))

        # Initial screen setup
        if platform == 'android':
            from jnius import autoclass
            PythonActivity     = autoclass('org.kivy.android.PythonActivity')
            self.WindowManager = autoclass('android.view.WindowManager$LayoutParams')
            self.activity      = PythonActivity.mActivity


    def controls_init(self):
        # Sliders init
        self.slider_interval.value = self.interval
        self.slider_distance.value = self.distance
        self.label_distance .text  = self.label_distance_value(self.distance)

        # Buttons init
        self.button_screen.text = self.screen
        self.button_theme .text = self.theme
        self.button_units .text = self.units
        self.button_format.text = self.format

    def label_interval_value(self, value):
        return f'{int(value)} s'

    def label_distance_value(self, value):
        return f'{round(meters_to_gpx_distance(self.units, value))} {units_to_gpx_distance(self.units)}'

    def on_controls_value_change(self, slider, value):
        if slider.id == 'INTERVAL':
            self.interval              = int(value)
            self.label_interval .text  = self.label_interval_value(self.interval)
            self.slider_interval.value = self.interval
            print('[OPTION]', f'{slider.id} slider value: {self.interval} s')

        elif slider.id == 'DISTANCE':
            self.distance              = int(value)
            self.label_distance .text  = self.label_distance_value(self.distance)
            self.slider_distance.value = self.distance
            print('[OPTION]', f'{slider.id} slider value: {self.distance} m')

        if isinstance(self.storage, dict):
            slider_value = int(default_settings[slider.id.lower()]['value'])
        else:
            slider_value = int(slider.value)

        # Schedule delayed save
        self.schedule_save(slider.id, slider.id.lower(), slider_value)

    def on_btn_press(self, btn):
        if btn.id == 'SCREEN':
            self.menu_screen.open()
        elif btn.id == 'THEME':
            self.menu_theme.open()
        elif btn.id == 'UNITS':
            self.menu_units.open()
        elif btn.id == 'FORMAT':
            self.menu_format.open()
        elif btn.id == 'SHUTDOWN':
            self.shutdown = True
        else:
            # reset to default
            for i, j in default_settings.items():
                self.menu_callback(j['value'])
                # In case the attribute doesn't exist:
                slider = getattr(self, f'slider_{i}', None)
                if slider:
                    slider.value = int(j['value'])
                    self.schedule_save(slider.id, slider.id.lower(), slider.value)

            toast('default settings restored')

    def menu_callback(self, txt):
        # Screen Menu
        if txt in self.texts_screen:
            self.button_screen.text = txt
            self.screen             = self.button_screen.text

            self.apply_screen_setting()

            # Only save if we have a JsonStore (file exists)
            print('[OPTION]', f'Screen changed: {self.screen}')
            self.instant_save('screen', self.screen)
            toast(f'screen set to {self.screen}')
            self.menu_screen.dismiss()

        # Theme Menu
        elif txt in self.texts_theme:
            palette   = params['theme'][txt]
            theme_cls = MDApp.get_running_app().theme_cls

            self.button_theme.text = txt
            self.theme             = self.button_theme.text

            theme_cls.theme_style     = self.theme.capitalize()
            theme_cls.primary_palette =    palette.capitalize()

            # Only save if we have a JsonStore (file exists)
            print('[OPTION]', f'Theme changed: {self.theme}')
            self.instant_save('theme', self.theme)
            toast(f'theme set to {self.theme}')
            self.menu_theme.dismiss()

        # Units Menu
        elif txt in self.texts_units:
            self.button_units.text = txt
            self.units             = self.button_units.text

            self.label_distance.text = self.label_distance_value(self.distance)

            # Only save if we have a JsonStore (file exists)
            print('[OPTION]', f'Units changed: {self.units}')
            self.instant_save('units', self.units)
            toast(f'units set to {self.units}')
            self.menu_units.dismiss()

        # Format Menu
        elif txt in self.texts_format:
            self.button_format.text = txt
            self.format             = self.button_format.text

            # Only save if we have a JsonStore (file exists)
            print('[OPTION]', f'Track format changed: {self.format}')
            self.instant_save('format', self.format)
            toast(f'format set to {self.format}')
            self.menu_format.dismiss()

    def apply_screen_setting(self):
        if platform == 'android':

            @run_on_ui_thread
            def apply_on_ui_thread():
                try:
                    print('[OPTION]', 'Screen setting')

                    if self.screen == 'always on':
                        self.activity.getWindow().addFlags(self.WindowManager.FLAG_KEEP_SCREEN_ON)

                    else:
                        self.activity.getWindow().clearFlags(self.WindowManager.FLAG_KEEP_SCREEN_ON)

                except Exception as e:
                    print('[OPTION]', f'Screen setting: {e}')

            apply_on_ui_thread()

        else:
            print('[OPTION]', 'Screen setting not implemented.')

    def on_size(self, *args):
        self.mock_banner.update_banner_height()
