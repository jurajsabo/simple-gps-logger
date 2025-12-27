from jnius import cast, autoclass

# ---------- Android plumbing ----------
PythonService = autoclass('org.kivy.android.PythonService')
Context       = autoclass('android.content.Context')
PowerManager  = autoclass('android.os.PowerManager')

service = PythonService.mService


def acquire_wake_lock():
    '''
        Acquire wake lock to keep CPU running when screen is off
    '''
    try:
        pm        = cast(PowerManager, service.getSystemService(Context.POWER_SERVICE))
        wake_lock = pm.newWakeLock(PowerManager.PARTIAL_WAKE_LOCK, 'simplegpslogger::GpsWakeLock')
        wake_lock.acquire()

        print('[GNSS] Wake lock acquired')
        return wake_lock

    except Exception as e:
        print(f'[GNSS] Failed to acquire wake lock: {e}')


def release_wake_lock(wake_lock):
    try:
        if wake_lock and wake_lock.isHeld():
            wake_lock.release()
            print('[GNSS]', 'Wake lock released')

    except Exception as e:
        print('[GNSS]', f'Failed to release wake lock: {e}')
