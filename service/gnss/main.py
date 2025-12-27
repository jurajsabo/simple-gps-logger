import os
import time
import json

from jnius  import autoclass, cast
from kivy   import platform
from config import FPS

from lib.utils.paths import load_path, settings_json
from lib.utils.saver import Saver
from lib.utils.units import utc_ms_time, utc_ms_to_gpx_time

from service.gnss.lib.locationListener import LocationListener
from service.gnss.lib.utils.point      import gnss_transformer

if platform == 'android':
    from service.gnss.lib.utils.foreground_notification import promote_to_foreground, create_notification
    from service.gnss.lib.utils.wake_lock               import acquire_wake_lock, release_wake_lock

    # ---------- Android plumbing ----------
    PythonService   = autoclass('org.kivy.android.PythonService')
    Context         = autoclass('android.content.Context')
    Build_VERSION   = autoclass('android.os.Build$VERSION')
    LocationManager = autoclass('android.location.LocationManager')
    Handler         = autoclass('android.os.Handler')

    service = PythonService.mService

    class GnssSender:
        def __init__(self):

            print('[GNSS]', 'Gnss sender init')
            self.is_running = False
            self.wake_lock  = None

            # Register the actual location listener that logs data
            self.locationListener = LocationListener()

            # Last init
            self.format_last       = None
            self.units_last        = None
            self.is_recording_last = None
            self.mtime_last        = None

            # Params init
            self.distance_m      = None
            self.distance_m_last = None

            self.interval_ms      = None
            self.interval_ms_last = None

            # Settings init
            self.settings = load_path(settings_json, path_only = True)
            self.settings_watcher()

            self.executor = None
            self.looper   = None

            self.ht = None  # handler thread
            self.lm = None  # location manager

        def settings_watcher(self):
            try:
                if isinstance(self.settings, dict):
                    # Use default settings
                    self.params_updates(self.settings)

                else:
                    mtime = os.path.getmtime(self.settings)
                    if mtime != self.mtime_last:
                        with open(self.settings, 'r', encoding = 'utf-8') as f:
                            # Apply settings changes
                            content = json.load(f)  # Single JSON object
                        self.params_updates(content)

                    self.mtime_last = mtime

            except Exception as e:
                print('[GNSS]', f'Settings watcher: {e}')

        def params_updates(self, settings):
            is_recording = settings['is_recording']['value']
            format       = settings['format']['value']
            units        = settings['units']['value']

            self.interval_ms = settings['interval']['value'] * 1000  # Convert seconds to milliseconds
            self.distance_m  = settings['distance']['value']

            # Recording state check
            if self.is_recording_last != is_recording:
                self.locationListener.is_recording = is_recording

            # Settings check
            if self.format_last != format or self.units_last != units:
                self.locationListener.settings_recorder(format = format, units = units)

            # Service check (only restart if values actually changed)
            if self.interval_ms_last != self.interval_ms or self.distance_m_last != self.distance_m:
                self.settings_service()

            self.is_recording_last = is_recording

            self.format_last = format
            self.units_last  = units

        def settings_service(self):
            '''
                Update location service parameters. Restart if running, otherwise just log the change.
            '''
            if self.is_running:
                # Service is running - restart with new parameters
                self.stop_updates()
                self.start_updates(self.interval_ms, self.distance_m)

                if self.interval_ms_last != self.interval_ms:
                    print('[GNSS]', f'Interval changed: {self.interval_ms_last} -> {self.interval_ms} ms')

                if self.distance_m_last != self.distance_m:
                    print('[GNSS]', f'Distance changed: {self.distance_m_last} -> {self.distance_m} m')
            else:
                # Service not running yet - just log that parameters are ready
                print('[GNSS]', f'Parameters updated (service not running): interval = {self.interval_ms} ms, distance = {self.distance_m}  m')

            # Always update tracking variables after change
            self.interval_ms_last = self.interval_ms
            self.distance_m_last  = self.distance_m

        def ensure_thread(self):
            SDK_INT = int(Build_VERSION.SDK_INT)

            if SDK_INT >= 30:
                if self.executor is None:
                    Executors = autoclass('java.util.concurrent.Executors')
                    self.executor = Executors.newSingleThreadExecutor()
            else:
                if self.ht is None:
                    HandlerThread = autoclass('android.os.HandlerThread')
                    self.ht = HandlerThread('location-thread')
                    self.ht.start()
                    self.looper = self.ht.getLooper()

        def gps_provider_check(self):
            try:
                gps_enabled = self.lm.isProviderEnabled(LocationManager.GPS_PROVIDER)
                print('[GNSS]', f'GPS provider enabled: {gps_enabled}')
                if not gps_enabled:
                    print('[GNSS]', 'WARNING: GPS is not enabled in device settings!')

            except Exception as e:
                print('[GNSS]', f'Could not check GPS status: {e}')

        def avalilable_providers_check(self):
            try:
                all_providers = self.lm.getAllProviders()
                iterator = all_providers.iterator()

                provider_list = []
                while iterator.hasNext():
                    provider_list.append(str(iterator.next()))
                print('[GNSS]', f"Available providers: {', '.join(provider_list)}")

            except Exception as e:
                print('[GNSS]' f'Could not get providers: {e}')

        def last_known_location_verification(self):
            try:
                last_loc = self.lm.getLastKnownLocation(LocationManager.GPS_PROVIDER)
                if last_loc:
                    last_point = gnss_transformer(last_loc, True)
                    print('[GNSS]', f'Last known location: {last_point}')
                    self.locationListener.listen(last_point)

                else:
                    print('[GNSS]', 'No last known location available')

            except Exception as e:
                print('[GNSS]', f'getLastKnownLocation failed: {e}')

        def request_updates(self, interval_ms, distance_m):
            '''
                Request location updates in a version-safe way:
                - For API < 30, use the Looper-based overload.
                - For API >= 30, use the Executor-based overload.
            '''
            try:
                SDK_INT = int(Build_VERSION.SDK_INT)
                print('[GNSS]', f'Android SDK version: {SDK_INT}')

                if SDK_INT >= 30:
                    # Use the new API 30+ overload
                    self.lm.requestLocationUpdates \
                    (
                        LocationManager.GPS_PROVIDER,
                        int(interval_ms),
                        float(distance_m),
                        self.executor,
                        self.locationListener
                    )
                    print('[GNSS]', f'Started GPS listener using Executor (interval = {interval_ms} ms, distance = {distance_m} m)')

                else:
                    # Use the legacy overload with Looper
                    self.lm.requestLocationUpdates \
                    (
                        LocationManager.GPS_PROVIDER,
                        int(interval_ms),
                        float(distance_m),
                        self.locationListener,
                        self.looper
                    )
                    print('[GNSS]', f'Started GPS listener using Looper (interval = {interval_ms} ms, distance = {distance_m} m)')

            except Exception as e:
                print('[GNSS]', f'requestLocationUpdates failed: {e}')

        def start_updates(self, interval_ms, distance_m):
            '''
                Start listening for GPS location updates.
            '''
            if self.lm is None:
                self.lm = cast(LocationManager, service.getSystemService(Context.LOCATION_SERVICE))

            # Check if GPS provider is enabled
            self.gps_provider_check()

            # Check for available providers
            self.avalilable_providers_check()

            # Get last known location to verify GPS works
            self.last_known_location_verification()

            # Ensure a dedicated Thread exists for receiving location updates
            self.ensure_thread()

            # Request GPS provider only (includes satellite count in extras Bundle)
            self.request_updates(interval_ms, distance_m)

        def stop_updates(self):
            '''
                Stop listening for GPS location updates.
            '''
            try:
                if self.locationListener and self.lm:
                    self.lm.removeUpdates(self.locationListener)
                    print('[GNSS]', 'LocationListener removed')

            except Exception as e:
                print('[GNSS]', f'removeUpdates failed: {e}')

        def stop_service(self):
            self.stop_updates()
            release_wake_lock(self.wake_lock)
            self.is_running = False
            print('[GNSS]', 'Service stopped')

        def run_service(self):
            '''
                Main service loop. Promotes the service to foreground,
                registers location listeners, and runs an infinite loop.
            '''
            try:
                print('[GNSS]', 'Starting service...')
                notif = create_notification()
                promote_to_foreground(notif)

                self.wake_lock = acquire_wake_lock()

                self.start_updates(self.interval_ms, self.distance_m)
                self.is_running = True

                heartbeat_last = utc_ms_time()

                while self.is_running:
                    # Periodic heartbeat to prove service is running
                    current_time = utc_ms_time()
                    delta_time = (current_time - heartbeat_last) / 1000

                    if delta_time >= FPS:  # Log heartbeat every 10 second
                        current_time_gpx = utc_ms_to_gpx_time(current_time)
                        print('[GNSS]', f'Service heartbeat: {current_time_gpx}')
                        heartbeat_last = current_time

                    # Watch for settings changes
                    self.settings_watcher()

                    # 10 FPS equivalent
                    time.sleep(1 / FPS)

                else:
                    self.stop_service()

            except Exception as e:
                print('[GNSS]', f'GNSS ERROR: {e}')

            finally:
                self.stop_service()

    if __name__ == '__main__':
        gnssSender = GnssSender()
        gnssSender.run_service()


else:
    import threading

    class GnssSender(Saver):
        def __init__(self, **kwargs):
            super().__init__(**kwargs)
            print('[GNSS]', 'Gnss sender init')

            # Threading
            self.thread     = threading.Thread(target = self.run_service, daemon = True)
            self.is_running = False

            # Register the actual location listener that logs data
            self.locationListener = LocationListener()

            # Last init
            self.format_last         = None
            self.units_last          = None
            self.interval_ms_last    = None
            self.mtime_states_last   = None
            self.mtime_settings_last = None
            self.is_running_last     = None
            self.is_recording_last   = None

            # Settings init
            self.settings = load_path(settings_json, path_only = True)
            self.settings_watcher()

        def settings_watcher(self):
            try:
                if isinstance(self.settings, dict):
                    # Use default settings
                    self.settings_updates(self.settings)

                else:
                    mtime = os.path.getmtime(self.settings)
                    if mtime != self.mtime_settings_last:
                        with open(self.settings, 'r', encoding = 'utf-8') as f:
                            # Apply settings changes
                            content = json.load(f)  # Single JSON object

                        self.settings_updates(content)

                    self.mtime_settings_last = mtime

            except Exception as e:
                print('[GNSS]', f'Settings watcher: {e}')

        def settings_updates(self, content):
            format       = content['format']['value']
            units        = content['units']['value']
            is_recording = content['is_recording']['value']

            self.interval_ms = content['interval']['value'] * 1000 # Convert seconds to milliseconds

            # Settings check
            if self.format_last != format or self.units_last != units:
                self.locationListener.settings_recorder(format = format, units = units)

            # Recording state check
            if self.is_recording_last != is_recording:
                self.locationListener.is_recording = is_recording

            # Service check
            if self.interval_ms_last != self.interval_ms:
                self.settings_service()

            self.format_last       = format
            self.units_last        = units
            self.is_recording_last = is_recording
            self.interval_ms_last  = self.interval_ms

        def start_updates(self):
            self.settings_watcher()
            if not self.is_running:
                self.locationListener.schedule(self.interval_ms)
                self.is_running = True
                self.thread.start()
                print('[GNSS]', f'Service started')

        def stop_updates(self):
            if self.is_running:
                self.locationListener.unschedule()
                self.is_running = False
                print('[GNSS]', f'Service stopped')
                if self.thread:
                    self.thread.join()
                    self.thread = None

        def settings_service(self):
            if self.is_running:
                self.locationListener.unschedule()
                self.locationListener.schedule(self.interval_ms)
                print('[GNSS]', f'Interval changed: {self.interval_ms_last} -> {self.interval_ms} ms')

        def run_service(self):
            try:
                heartbeat_last = utc_ms_time()

                while self.is_running:
                    # Periodic heartbeat to prove service is running
                    current_time = utc_ms_time()
                    delta_time   = (current_time - heartbeat_last) / 1000

                    if delta_time >= FPS:  # Log heartbeat every 10 second
                        current_time_gpx = utc_ms_to_gpx_time(current_time)
                        print('[GNSS]', f'Service heartbeat: {current_time_gpx}')
                        heartbeat_last = current_time

                    # Watch for settings changes
                    self.settings_watcher()

                    # 10 FPS equivalent
                    time.sleep(1 / FPS)

                else:
                    self.stop_updates()

            except Exception as e:
                print('[GNSS]', f'Service run: {e}')
                self.stop_updates()
