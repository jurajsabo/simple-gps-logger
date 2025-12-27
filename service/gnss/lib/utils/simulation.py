import random
from config          import FPS
from lib.utils.units import utc_ms_time

last_payload = None  # stored between calls

def gnss_sim(same_probability = 1/FPS):
    global last_payload

    # Return same payload with given probability (only if one exists)
    if last_payload is not None and random.random() < same_probability:
        return last_payload

    # Otherwise generate a new payload
    payload = \
    {
        'provider': 'test',
        'latitude': random.uniform(-90, 90),
        'longitude': random.uniform(-180, 180),
        'accuracy_m': random.uniform(25, 200),
        'time_ms_utc': utc_ms_time(),
        'altitude_m': random.uniform(500, 1500),
        'speed_mps': random.uniform(0, 50),
        'bearing_deg': random.uniform(0, 360),
        'satellites_used_in_fix': round(random.uniform(0, 10)),
    }

    last_payload = payload
    return payload
