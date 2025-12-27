from jnius import PythonJavaClass, java_method
from kivy  import platform

from service.gnss.lib.locationSender import LocationSender


if platform == 'android':
    from service.gnss.lib.utils.point import gnss_transformer

    class LocationListener(PythonJavaClass, LocationSender):
        '''
            Python implementation of Android's LocationListener.
            Receives location updates and writes them to the log file as JSONL.
        '''
        __javainterfaces__ = ['android/location/LocationListener']
        __javacontext__    = 'app'

        def __init__(self):
            # Explicitly initialize LocationSender (skip PythonJavaClass)
            LocationSender.__init__(self)

        @java_method('(Landroid/location/Location;)V')
        def onLocationChanged(self, loc):
            '''
                Callback triggered for each location update (single location)
            '''
            try:
                point = gnss_transformer(loc) # Transform gnss_log payload
                self.listen(point)

            except Exception as e:
                print(f'[GNSS] Exception in onLocationChanged: {e}')

        @java_method('(Ljava/util/List;)V', name = 'onLocationChanged')
        def onLocationChangedList(self, location_list):
            '''
                Callback for batch location updates (API 31+).
            '''
            try:
                # Get the most recent location from the list
                if location_list and location_list.size() > 0:
                    location = location_list.get(location_list.size() - 1)
                    self.onLocationChanged(location)
                else:
                    print(f'[GNSS] Empty location list received')

            except Exception as e:
                print(f'[GNSS] Error processing location list: {e}')

        @java_method('(Ljava/lang/String;)V')
        def onProviderEnabled(self, provider):
            print(f'[GNSS] onProviderEnabled: {provider}')

        @java_method('(Ljava/lang/String;)V')
        def onProviderDisabled(self, provider):
            print(f'[GNSS] onProviderDisabled: {provider}')

        @java_method('(Ljava/lang/String;ILandroid/os/Bundle;)V')
        def onStatusChanged(self, provider, status, extras):
            status_names = {0: 'OUT_OF_SERVICE', 1: 'TEMPORARILY_UNAVAILABLE', 2: 'AVAILABLE'}
            status_str   = status_names.get(status, f'UNKNOWN({status})')
            print(f'[GNSS] onStatusChanged: {provider} -> {status_str}')

else:
    from kivy.clock import Clock
    from service.gnss.lib.utils.simulation import gnss_sim

    class LocationListener(LocationSender):

        def schedule(self, interval_ms):
            Clock.schedule_interval(self.onLocationChanged, interval_ms / 1000)

        def unschedule(self):
            Clock.unschedule(self.onLocationChanged)

        def onLocationChanged(self, dt):
            '''
                Location update simulation (single location)
            '''
            try:
                point = gnss_sim()
                self.listen(point)
            except Exception as e:
                print(f'[GNSS] Exception in onLocationChanged: {e}')
