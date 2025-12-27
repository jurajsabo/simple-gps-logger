from kivy.clock import Clock
from config     import params, default_settings, toast_duration

from kivymd.app                  import MDApp
from kivymd.toast                import toast
from kivymd.uix.boxlayout        import MDBoxLayout
from kivymd.uix.screen           import MDScreen
from kivymd.uix.bottomnavigation import MDBottomNavigation, MDBottomNavigationItem

from lib.screens.aboutScreen   import AboutScreen
from lib.screens.displayScreen import DisplayScreen
from lib.screens.tracksScreen  import TracksScreen
from lib.screens.optionsScreen import OptionsScreen
from lib.utils.label           import MockNavigationBar


class NavigationScreen(MDScreen):
    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        print('[NAVIGATION]', 'init')

        # Screens Init
        self.DisplayScreen = DisplayScreen()
        self.TracksScreen  = TracksScreen()
        self.OptionsScreen = OptionsScreen()
        self.AboutScreen   = AboutScreen()

        # Main layout
        main_layout = MDBoxLayout(orientation = 'vertical', spacing = 0)

        # Bottom navigation bar spacer
        self.nav_bar = MockNavigationBar()

        # Bottom navigation
        main_layout.add_widget \
        (
            CustomBottomNavigation
            (
                MDBottomNavigationItem
                (
                    self.DisplayScreen,
                    name = 'DisplayScreen',
                    text = 'display',
                    icon = 'crosshairs',
                    on_tab_release = self.on_tab_release
                ),
                MDBottomNavigationItem
                (
                    self.TracksScreen,
                    name = 'TracksScreen',
                    text = 'tracks',
                    icon = 'go-kart-track',
                    on_tab_release = self.on_tab_release
                ),
                MDBottomNavigationItem
                (
                    self.OptionsScreen,
                    name = 'OptionsScreen',
                    text = 'options',
                    icon = 'cogs',
                    on_tab_release = self.on_tab_release
                ),
                MDBottomNavigationItem
                (
                    self.AboutScreen,
                    name = 'AboutScreen',
                    text = 'about',
                    icon = 'file-question',
                    on_tab_release = self.on_tab_release,
                ),

            )

        )

        # Add the main layout to screen
        self.add_widget(main_layout)

        # Remaining layout
        main_layout.add_widget(self.nav_bar)

        # Manager
        self.screenManager = self.children[0].children[1].children[1]

        # Bind OptionsScreen updates
        self.OptionsScreen.bind(format   = self.on_update_options)
        self.OptionsScreen.bind(units    = self.on_update_options)
        self.OptionsScreen.bind(interval = self.on_update_options)
        self.OptionsScreen.bind(shutdown = self.on_shut_down)

        # Bind DisplayScreen recording state
        self.DisplayScreen.bind(is_recording = self.on_recording_state)

        # Ensure widgets are not disabled
        self.children[0].children[1].disabled = False
        self.children[0].children[1].children[0].disabled = False
        self.children[0].children[1].children[1].children[0].disabled = False

    def on_tab_release(self, *args):
        if self.screenManager.current == 'TracksScreen':
            self.TracksScreen.synchronize()
        print('[NAVIGATION]', f'Current screen: {self.screenManager.current}')

    def on_update_options(self, screen, value):
        if value in params['format']:
            self.DisplayScreen.format = value
        elif value in params['units']:
            self.DisplayScreen.units = value
        else:
            self.DisplayScreen.threshold = max(toast_duration * 8, value)

    def on_shut_down(self, screen, value):
        if value:
            toast('shutting down...')
            Clock.schedule_once(lambda dt: MDApp.get_running_app().stop(), 1)

    def on_recording_state(self, screen, state):
        if state == default_settings['is_recording']['value']:
            Clock.schedule_once(lambda dt: self.btn_disabled(False), 1)
        else:
            self.btn_disabled(True)

    def btn_disabled(self, state):
        self.OptionsScreen.slider_interval.disabled = state
        self.OptionsScreen.slider_distance.disabled = state
        self.OptionsScreen.button_units   .disabled = state
        self.OptionsScreen.button_format  .disabled = state
        self.OptionsScreen.button_shutdown.disabled = state
        self.OptionsScreen.button_reset   .disabled = state

    def on_size(self, *args):
        self.nav_bar.update_navigation_height()


class CustomBottomNavigation(MDBottomNavigation):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)

        # Bind to primary color change (for selected background and text colors)
        self.theme_cls.bind(primary_color = self.update_colors)
        self.theme_cls.bind(theme_style   = self.update_colors)

        # Apply initially
        self.update_colors()

    def update_colors(self, *args):
        # Update background color of selected tab
        for tab in self.ids.tab_bar.children:
            tab.selected_color_background = self.theme_cls.primary_color

            # Force reapply the color to all headers
            tab.text_color_active = self.theme_cls.opposite_bg_dark
            if tab.active:
                tab._text_color_normal = self.theme_cls.opposite_bg_dark

        # Update text color for selected tab (active color)
        self.text_color_active = self.theme_cls.opposite_bg_dark
