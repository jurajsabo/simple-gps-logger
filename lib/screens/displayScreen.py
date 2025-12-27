import json
import os

from kivy   import platform
from config import default_settings, toast_duration, params, FPS

from kivy.properties        import BoundedNumericProperty, StringProperty
from kivy.core.window       import Window
from kivy.clock             import Clock
from kivy.storage.jsonstore import JsonStore

from kivymd.material_resources import dp
from kivymd.toast              import toast

from kivymd.uix.boxlayout   import MDBoxLayout
from kivymd.uix.floatlayout import MDFloatLayout
from kivymd.uix.gridlayout  import MDGridLayout
from kivymd.uix.scrollview  import MDScrollView
from kivymd.uix.screen      import MDScreen

from lib.utils.buttons import CustomToggleButton, CustomButton
from lib.utils.card    import GpsDisplay
from lib.utils.label   import MockBanner
from lib.utils.paths   import tracks_folder, load_path, gnss_log
from lib.utils.saver   import Saver
from lib.utils.service import gnss_check
from lib.utils.units   import \
(
    convert_lat,
    bearing_to_cardinal,
    convert_lon,
    units_to_gpx_distance,
    mps_to_gpx_speed,
    meters_to_gpx_distance,
    units_to_gpx_speed,
    utc_ms_time
)

if platform == 'android':
    from android.permissions import check_permission, Permission


class DisplayScreen(MDScreen, Saver):
    # Params init
    is_recording = BoundedNumericProperty(default_settings['is_recording']['value'], min = -1, max = 1) # -1... pause, 0... stop, 1... record
    units        = StringProperty(default_settings['units']['value'])
    interval     = BoundedNumericProperty(default_settings['interval']['value'], min = params['interval']['min'], max = params['interval']['max'])

    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        print('[DISPLAY]', 'init')

        # storage init
        self.storage      = default_settings
        self.is_recording = default_settings['is_recording']['value']

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
                MDGridLayout \
                    (
                        GpsDisplay(id = 'latitude',    text1 = 'latitude',  text2 = '00'),
                        GpsDisplay(id = 'longitude',   text1 = 'longitude', text2 = '00'),
                        GpsDisplay(id = 'speed_mps',   text1 = 'speed',     text2 = '00'),
                        GpsDisplay(id = 'bearing_deg', text1 = 'bearing',   text2 = '00'),
                        GpsDisplay(id = 'altitude_m',  text1 = 'altitude',  text2 = '00'),
                        GpsDisplay(id = 'accuracy_m',  text1 = 'accuracy',  text2 = 'XX'),
                        cols        = 2,
                        spacing     = dp(10),
                        padding     = dp(5),
                        size_hint_y = None,
                        height      = dp(550)
                    ),
                    MDBoxLayout \
                    (
                        MDFloatLayout \
                        (
                            CustomToggleButton \
                            (
                                icon     = 'record',
                                on_press = self.on_press,
                                id       = 'record',
                                disabled = False,
                                pos_hint = {'center_x': 0.7}
                            ),
                            size_hint_y = None
                        ),
                        MDFloatLayout \
                        (
                            CustomButton \
                            (
                                icon     = 'stop',
                                on_press = self.on_press,
                                id       = 'stop',
                                disabled = True,
                                pos_hint = {'center_x': 0.3}
                            ),
                            size_hint_y = None,
                        ),
                        size_hint_y = None,
                        height      = dp(65)
                    ),
                    orientation = 'vertical',
                    size_hint_y = None,
                ),
                size_hint   = [1, 1],
                bar_width   = dp(4),
                scroll_type = ['bars', 'content'],
                do_scroll_y = True
            )

        )

        # Add the main layout to screen
        self.add_widget(main_layout)

        # layout
        self.layout = main_layout.children[0].children[0]

        self.buttons  = self.layout.children[0].children
        self.displays = self.layout.children[1].children

        self.accuracy      = self.displays[0].children[0].children[0]
        self.button_record = self.buttons [1].children[0]
        self.button_stop   = self.buttons [0].children[0]

        # Bind the layout's height to its minimum_height (to the total height of all its children)
        self.layout.bind(minimum_height = self.layout.setter('height'))

        # GNSS init
        self.folder   = load_path(tracks_folder, path_only = True)
        self.gnss_log = load_path(gnss_log)

        # Last init
        self.mtime_gnss_last    = None
        self.is_recording_last  = None
        self.service_state_last = None
        self.gnss_check_last    = None

        # Toast show
        self.toast_recording_show = None
        self.toast_last_show      = None
        self.toast_error_show     = None
        self.toast_waiting_show   = None

        self.threshold = toast_duration * 8

        # Main loop init
        Clock.schedule_interval(self.loop_watcher, 1/FPS) # 10 FPS equivalent

    def toast_waiting_reset(self, dt):
        self.toast_waiting_show = False

    def toast_error_reset(self, dt):
        self.toast_error_show = False

    def toast_display(self, text, toast_show, toast_reset, duration, e = None, restart = False):
        if not toast_show:
            toast_show = True
            toast(text)

            if e is not None:
                print('[DISPLAY]', e)
            if restart:
                Clock.schedule_once(lambda dt: toast('restart the app'), duration)

            Clock.schedule_once(toast_reset, duration)

        return toast_show

    def display_drawer(self, point):
        if point['provider'] == 'last' and not self.toast_last_show:
            toast('last known location')
            self.toast_last_show = True

        for display in self.displays:
            for key, value in point.items():
                value = 0 if value is None else value

                if display.id == key:
                    if display.id == 'latitude':
                        display.children[0].children[0].text = \
                            str(convert_lat(value))
                    elif display.id == 'longitude':
                        display.children[0].children[0].text = \
                            str(convert_lon(value))
                    elif display.id == 'speed_mps':
                        display.children[0].children[0].text = \
                            f'{round(mps_to_gpx_speed(self.units, value))} {units_to_gpx_speed(self.units)}'
                    elif display.id == 'bearing_deg':
                        display.children[0].children[0].text = \
                            bearing_to_cardinal(value)
                    elif display.id == 'altitude_m':
                        display.children[0].children[0].text = \
                            f'{round(meters_to_gpx_distance(self.units, value))} {units_to_gpx_distance(self.units)}'
                    elif display.id == 'accuracy_m':
                        display.children[0].children[0].text = \
                            point['provider'].upper() if point['provider'] == 'test' else \
                                f'{round(meters_to_gpx_distance(self.units, value))} {units_to_gpx_distance(self.units)}'

    def loop_watcher(self, dt):
        self.gnss_watcher()
        self.recording_toast_watcher()

    def gnss_watcher(self):
        try:
            # gnss service check
            check = gnss_check(self)
            if check != self.gnss_check_last:
                if check:
                    toast('gnss service is running')
                else:
                    toast('gnss service is NOT running')

                self.gnss_check_last = check

            # gnss file mtime
            mtime        = os.path.getmtime(self.gnss_log)
            current_time = utc_ms_time() / 1000
            diff         = current_time - mtime

            if diff > self.threshold:
                text = 'waiting for location data...'

                if platform == 'android':
                    if not check_permission(Permission.ACCESS_FINE_LOCATION):
                        text = 'fine location access DENIED'

                self.toast_waiting_show = \
                    self.toast_display(text, self.toast_waiting_show, self.toast_waiting_reset, self.threshold, None)

            # file changed
            if mtime != self.mtime_gnss_last:
                with open(self.gnss_log, 'r', encoding = 'utf-8') as f:
                    point = json.load(f)

                # update display & mtime
                self.display_drawer(point)
                self.mtime_gnss_last = mtime

        except Exception as e:
            print('[DISPLAY]', f'Gnss watcher error: {e}')

    def recording_toast_watcher(self):
        try:
            is_recording = self.storage['is_recording']['value']

            if is_recording != self.is_recording:
                if not self.toast_recording_show:
                    self.toast_recording_show = True

            else:
                if self.toast_recording_show:
                    if is_recording == 1:
                        if self.is_recording_last == 0:
                            toast('recording started')
                        else:
                            toast('recording resumed')

                    elif is_recording == -1:
                        toast('recording paused')

                    elif is_recording == 0:
                        toast('recording stopped')

                    self.toast_recording_show = False

                self.is_recording_last = self.is_recording

        except Exception as e:
            self.toast_error_show = \
                self.toast_display('recording toast watcher', self.toast_error_show, self.toast_error_reset, toast_duration, e)

    def on_press(self, btn):
        try:
            if os.path.exists(self.folder) and isinstance(self.storage, JsonStore) and self.gnss_check_last:
                if btn.id == 'record':
                    if self.is_recording == 0:
                        self.recording_start()
                    elif self.is_recording == 1:
                        self.recording_pause()
                    else:
                        self.recording_resume()

                elif btn.id == 'stop':
                    self.recording_stop()

                else:
                    self.dialog.dismiss()

                # recording state save
                if btn.id != 'btn_warn':
                    id = f'{btn.id}|{btn.state}'
                    self.schedule_save(id, 'is_recording', self.is_recording)

            else:
                if not os.path.exists(self.folder):
                    print('[DISPLAY]', f"Track folder can't be found: {self.folder}")
                    toast('track folder is not initiated')

                if not isinstance(self.storage, JsonStore):
                    print('[DISPLAY]', f'Storage is not ready: {self.storage}')
                    toast('storage is not initiated')

                if not self.gnss_check_last:
                    print('[DISPLAY]', f'Gnss service state: {self.gnss_check_last}')
                    toast('gnss service is NOT running')

                self.recording_stop()
                Clock.schedule_once(lambda dt: toast('restart the app'), toast_duration)

        except Exception as e:
            self.toast_error_show = \
                self.toast_display('press error', self.toast_error_show, self.toast_error_reset, toast_duration, e, True)

    def recording_start(self):
        self.button_record.icon   = 'pause'
        self.button_stop.disabled = False
        self.is_recording         = 1

    def recording_resume(self):
        self.button_record.icon = 'pause'
        self.is_recording       = 1

    def recording_pause(self):
        self.button_record.icon = 'record'
        self.is_recording       = -1

    def recording_stop(self):
        self.button_stop.disabled = True
        self.button_record.state  = 'normal'
        self.button_record.icon   = 'record'
        self.is_recording         = 0

    def on_size(self, *args):
        self.mock_banner.update_banner_height()
        for b in self.buttons:
            b.children[0].width = max(Window.width / 8, b.children[0]._min_width)
