from kivy   import platform
from config import SERVICE


if platform == 'android':
    from jnius import autoclass

    # Register with Android application
    PythonActivity = autoclass('org.kivy.android.PythonActivity')

    # Service class
    service_class = autoclass(SERVICE)

    # Activity manager
    Context          = autoclass('android.content.Context')
    activity_manager = PythonActivity.mActivity.getSystemService(Context.ACTIVITY_SERVICE)

    def gnss_check(self):
        '''
            Check if GNSS service is currently running.
            Returns True if service is running, False otherwise.

            Note: On Android 8.0+, getRunningServices() only returns the caller's own services
        '''
        running_services = activity_manager.getRunningServices(109)
        python_list      = list(running_services)

        for service_info in python_list:
            name    =  str(service_info.service.getClassName())
            started = bool(service_info.started)

            if name == SERVICE:
                return started

        return False

    def gnss_start(self):
        '''
            Start GNSS service
        '''
        # Use the p4a service infrastructure
        service_class.start(PythonActivity.mActivity, '')
        print('[APP]', 'Service start requested')

    def gnss_stop(self):
        '''
            Stop GNSS service
        '''
        # Use the p4a service infrastructure
        service_class.stop(PythonActivity.mActivity)
        print('[APP]', 'Service stop requested')

else:
    def gnss_check(self):
        '''
            Desktop fallback
        '''
        if hasattr(self, 'gnssSender'):
            is_running = self.gnssSender.is_running
            return is_running

        return False

    def gnss_start(self):
        '''
            Start GNSS service
        '''
        self.gnssSender.start_updates()

    def gnss_stop(self):
        '''
            Stop GNSS service
        '''
        self.gnssSender.stop_updates()
