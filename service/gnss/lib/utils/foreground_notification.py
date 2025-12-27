from jnius import autoclass, cast
from config import app_name

# ---------- Android plumbing ----------
PythonService    = autoclass('org.kivy.android.PythonService')
Context          = autoclass('android.content.Context')
Build_VERSION    = autoclass('android.os.Build$VERSION')
NotificationMgr  = autoclass('android.app.NotificationManager')
NotificationBldr = autoclass('android.app.Notification$Builder')
PendingIntent    = autoclass('android.app.PendingIntent')
Intent           = autoclass('android.content.Intent')
PythonActivity   = autoclass('org.kivy.android.PythonActivity')
ServiceCompat    = autoclass('androidx.core.app.ServiceCompat')
ServiceInfo      = autoclass('android.content.pm.ServiceInfo')

service = PythonService.mService


def create_notification():
    '''
        Create a persistent foreground notification for the service.
    '''
    nm         = cast(NotificationMgr, service.getSystemService(Context.NOTIFICATION_SERVICE))
    channel_id = 'gnss_location_channel'
    SDK_INT    = int(Build_VERSION.SDK_INT)

    if SDK_INT >= 26:
        NotificationChan = autoclass('android.app.NotificationChannel')
        ch               = NotificationChan(channel_id, 'GNSS Location', NotificationMgr.IMPORTANCE_LOW)

        nm.createNotificationChannel(ch)
        builder = NotificationBldr(service, channel_id)
    else:
        builder = NotificationBldr(service)

    app_intent = Intent(service, PythonActivity)
    flags      = PendingIntent.FLAG_IMMUTABLE if SDK_INT >= 23 else 0
    pi         = PendingIntent.getActivity(service, 0, app_intent, flags)

    # Use Android's built-in GPS icon
    resources = service.getResources()
    gps_icon_id = resources.getIdentifier('ic_menu_mylocation', 'drawable', 'android')

    # Fallback to app icon if system icon not found
    icon = gps_icon_id if gps_icon_id != 0 else service.getApplicationInfo().icon

    return builder.setContentTitle(app_name) \
                  .setContentText('GNSS service is running') \
                  .setSmallIcon(icon) \
                  .setOngoing(True) \
                  .setContentIntent(pi) \
                  .build()

def promote_to_foreground(notif):
    '''
        Promote the Python service to a foreground service.
    '''
    SDK_INT = int(Build_VERSION.SDK_INT)

    if SDK_INT >= 29:
        # API 29+ requires service type
        ServiceCompat.startForeground(service, 109, notif, ServiceInfo.FOREGROUND_SERVICE_TYPE_LOCATION)
    else:
        # API 24-28: No service type parameter
        ServiceCompat.startForeground(service, 109, notif, 0)
