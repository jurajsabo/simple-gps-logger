# SPDX-License-Identifier: GPL-3.0-or-later
# Copyright (C) 2025 Juraj Sabo


from kivy       import platform
from kivymd.app import MDApp
from config     import default_material_style, params, toast_duration

from lib.utils.paths              import load_path, settings_json
from lib.utils.saver              import Saver
from lib.screens.navigationScreen import NavigationScreen
from lib.utils.service            import gnss_check, gnss_start, gnss_stop


if platform == 'android':
    from lib.utils.permissions import PermissionsManager

else: # test size
    from kivy.core.window  import Window
    from kivy.metrics      import Metrics
    from service.gnss.main import GnssSender

    # Define desired screen dimensions in dp
    desired_width_dp  = 380
    desired_height_dp = 800

    # Set window size (convert dp to pixels using density)
    Window.size = \
    [
        desired_width_dp  * Metrics.density,
        desired_height_dp * Metrics.density
    ]


class GpsApp(MDApp, Saver):
    '''
        Main application entry point for the GPS tracking app.

        This module defines the `GpsApp` class, which configures the application's
        theme, requests necessary permissions, and launches the navigation interface.
    '''

    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        print('[APP]', 'init')

        # Screen init
        self.navigationScreen = NavigationScreen()

        # Screens init
        self.DisplayScreen = self.navigationScreen.DisplayScreen
        self.TracksScreen  = self.navigationScreen.TracksScreen
        self.OptionsScreen = self.navigationScreen.OptionsScreen

        if platform == 'android':
            # Permission manager
            self.permissionsManager = PermissionsManager(self)
        else:
            self.gnssSender = GnssSender()
            self.DisplayScreen.gnssSender = self.gnssSender

        # Settings init
        self.storage = load_path(settings_json)

    def build(self):
        # Theme init
        theme   = self.storage['theme']['value']
        palette = params['theme'][theme]

        self.theme_cls.material_style  = default_material_style
        self.theme_cls.theme_style     = theme.capitalize()
        self.theme_cls.primary_palette = palette.capitalize()

        return self.navigationScreen

    def settings_init(self):
        '''
            Initialize all screen settings
        '''
        # Options screen
        self.OptionsScreen.storage   = self.storage
        self.OptionsScreen.threshold = max(toast_duration * 8, self.storage['interval']['value'])
        self.OptionsScreen.distance  = self.storage['distance']['value']
        self.OptionsScreen.screen    = self.storage['screen']['value']
        self.OptionsScreen.theme     = self.storage['theme']['value']
        self.OptionsScreen.units     = self.storage['units']['value']
        self.OptionsScreen.format    = self.storage['format']['value']
        self.OptionsScreen.controls_init()
        self.OptionsScreen.apply_screen_setting()
        print('[APP]', 'settings initiated:', 'Options screen')

        # Display screen
        self.DisplayScreen.storage      = self.storage
        self.DisplayScreen.is_recording = self.storage['is_recording']['value']
        self.DisplayScreen.interval     = self.storage['interval']['value']
        self.DisplayScreen.units        = self.storage['units']['value']
        print('[APP]', 'settings initiated:', 'Display screen')

    def on_location_granted(self):
        '''
            Called when location permission is granted - main initialization happens here
        '''
        # Check app state to determine how to initialize
        app_state    = self.storage['app_state']['value']
        is_recording = self.storage['is_recording']['value']
        print('[APP]', f'Location permission granted, previous state: app_state = {app_state}, is_recording = {is_recording}')

        # GNSS service check
        service_check = gnss_check(self)

        # Handle different startup scenarios
        if app_state == 0 and not service_check:
            # Clean shutdown - start fresh
            print('[APP]', 'Clean start - no state to restore')
            self.TracksScreen.finalize()
            self.instant_save('app_state', 1)
        else:
            # App was running - could be crash or system kill
            print('[APP]', 'App was running - restoring state')

            if is_recording == 1:
                # Was recording - resume recording
                print('[APP]', 'Resuming recording...')
                self.DisplayScreen.recording_start()
            elif is_recording == -1:
                # Was paused - resume paused state
                print('[APP]', 'Resuming paused recording...')
                self.DisplayScreen.recording_pause()
            else:
                # Was just running, no recording
                print('[APP]', 'Resuming stopped recording...')
                self.TracksScreen.finalize()

        # Keep state as running
        self.instant_save('app_state', 1)

        # Initialize settings first
        self.settings_init()

        # Start GNSS service
        if not service_check:
            gnss_start(self)
            gnss_check(self)

    def on_location_denied(self):
        '''
            Called when location permission is denied
        '''
        # Check app state
        app_state = self.storage['app_state']['value']
        print('[APP]', f'Location permission denied, previous state: {app_state}, no GPS permission - limited mode')

        # Keep state as running
        self.instant_save('app_state', 1)
        self.instant_save('is_recording', 0)

        # Track finalization
        self.TracksScreen.finalize()

        # Initialize settings first
        self.settings_init()

    def on_notifications_granted(self):
        '''
            Called when notification permission is granted
        '''
        print('[APP]', 'Notification permission granted')

    def on_notifications_denied(self):
        '''
            Called when notification permission is denied
        '''
        print('[APP]', 'Notification permission denied')
        
    def on_storage_granted(self):
        '''
            Called when storage permission is granted
        '''
        print('[APP]', 'Storage permission granted')

    def on_storage_denied(self):
        '''
            Called when storage permission is denied
        '''
        print('[APP]', 'Storage permission denied')

    def on_all_permissions_complete(self):
        '''
            Called when all permissions have been processed
        '''
        print('[APP]', 'All permissions processed - app ready')

    def on_start(self):
        '''
            Called when app starts - request permissions first
        '''
        if platform == 'android':
            print('[APP]', 'App starting - requesting permissions...')
            # Request permissions - callbacks will handle initialization
            self.permissionsManager.request_permissions()
        else:
            print('[APP]', 'App starting without permissions...')
            self.on_location_granted()
            self.on_notifications_granted()

        app_state = self.storage['app_state']['value']
        print('[APP]', f'app started: {app_state}')

    def on_stop(self):
        '''
            Called when app stops normally
        '''
        # Service stop
        gnss_stop(self)

        # Stop recording
        self.instant_save('is_recording', 0)

        # Stop state save
        self.instant_save('app_state', 0)

        app_state = self.storage['app_state']['value']
        print('[APP]', f'app stopped: {app_state}')

    def on_pause(self):
        '''
            Called when app is paused
        '''
        # Paused state save
        self.instant_save('app_state', -1)

        app_state = self.storage['app_state']['value']
        print('[APP]', f'paused: {app_state}')
        return True  # Allows app to pause

    def on_resume(self):
        '''
            Called when app resumes from pause
        '''
        # Resumed state save
        self.instant_save('app_state', 1)

        app_state = self.storage['app_state']['value']
        print('[APP]', f'resumed: {app_state}')


if __name__ == '__main__':
    app = GpsApp()
    app.run()
