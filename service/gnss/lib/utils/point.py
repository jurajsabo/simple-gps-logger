
def get_sattelites(loc):
    # Get satellite count from extras Bundle (GPS_PROVIDER includes this)
    try:
        extras = loc.getExtras()
        if extras.containsKey('satellites'):
            return extras.getInt('satellites')

    except Exception as e:
        print(f'[GNSS] extras Bundle: {e}')
        return None

def get_safe(value, cast = float, check = None, fallback = None):
    try:
        if value is None:
            return fallback
        else:
            if check is None:
                return cast(value)
            else:
                return cast(value) if check else fallback

    except Exception as e:
        print(f"[GNSS] Failed to get location update: {e}")
        return fallback

def gnss_transformer(loc, last = False):
    point = \
    {
        'latitude':                     get_safe(loc.getLatitude(),   float),
        'longitude':                    get_safe(loc.getLongitude(),  float),
        'altitude_m':                   get_safe(loc.getAltitude(),   float, loc.hasAltitude()),
        'time_ms_utc':                  get_safe(loc.getTime(),       int),
        'speed_mps':                    get_safe(loc.getSpeed(),      float, loc.hasSpeed()),
        'accuracy_m':                   get_safe(loc.getSpeed(),      float, loc.hasSpeed()),
        'bearing_deg':                  get_safe(loc.getAccuracy(),   float, loc.hasAccuracy()),
        'satellites_used_in_fix':       get_safe(get_sattelites(loc), int),
        'provider': 'last' if last else get_safe(loc.getProvider(),   str)
    }
    return point
