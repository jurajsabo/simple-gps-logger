from config import default_settings
from datetime           import datetime, timezone


def dd_to_dms(decimal_degrees):
    '''
        Convert decimal degrees to degrees, minutes, seconds format.

        Args:
            decimal_degrees (float): Decimal degrees coordinate

        Returns:
            tuple: (degrees, minutes, seconds, direction)
            - degrees: int
            - minutes: int
            - seconds: float
            - direction: str ('N', 'S', 'E', 'W')
    '''
    # Determine if this is latitude or longitude based on range
    is_latitude = -90 <= decimal_degrees <= 90

    # Determine direction
    if is_latitude:
        direction = 'N' if decimal_degrees >= 0 else 'S'
    else:
        direction = 'E' if decimal_degrees >= 0 else 'W'

    # Work with absolute value
    abs_dd = abs(decimal_degrees)

    # Extract degrees
    degrees = int(abs_dd)

    # Extract minutes
    minutes_float = (abs_dd - degrees) * 60
    minutes = int(minutes_float)

    # Extract seconds
    seconds = (minutes_float - minutes) * 60
    return degrees, minutes, seconds, direction


def format_dms(degrees, minutes, seconds, direction):
    '''
        Format DMS components into a readable string.

        Args:
            degrees (int): Degrees
            minutes (int): Minutes
            seconds (float): Seconds
            direction (str): Direction ('N', 'S', 'E', 'W')

        Returns:
            str: Formatted DMS string
    '''
    return f"{degrees}°{minutes:02d}'{seconds:05.2f}\"{direction}"


def convert_lon(longitude):
    '''
        Convert longitude from decimal degrees to DMS format.

        Args:
            longitude (float): Longitude in decimal degrees

        Returns:
            lon_dms_string
    '''

    # Convert longitude
    lon_deg, lon_min, lon_sec, lon_dir = dd_to_dms(longitude)
    lon_dms = format_dms(lon_deg, lon_min, lon_sec, lon_dir)
    return lon_dms


def convert_lat(latitude):
    '''
        Convert latitude from decimal degrees to DMS format.

        Args:
            latitude (float): Latitude in decimal degrees

        Returns:
            lat_dms_string
    '''
    # Convert latitude
    lat_deg, lat_min, lat_sec, lat_dir = dd_to_dms(latitude)
    lat_dms = format_dms(lat_deg, lat_min, lat_sec, lat_dir)
    return lat_dms


def normalize_bearing(bearing):
    '''
        Convert bearing to standard 0-360 degree format.

        Args:
            bearing (float): Bearing in degrees (can be any value)

        Returns:
            float: Normalized bearing (0-360 degrees)
    '''
    # Normalize to 0-360 range
    normalized = bearing % 360
    return normalized


def bearing_to_cardinal(bearing):
    '''
        Convert bearing to cardinal direction.

        Args:
            bearing (float): Bearing in degrees (0-360)

        Returns:
            str: Cardinal direction (N, NE, E, SE, S, SW, W, NW)
    '''
    bearing = normalize_bearing(bearing)

    directions = \
    [
        "N", "NNE", "NE", "ENE",
        "E", "ESE", "SE", "SSE",
        "S", "SSW", "SW", "WSW",
        "W", "WNW", "NW", "NNW"
    ]

    # Each direction covers 22.5 degrees
    index = round(bearing / 22.5) % 16
    return directions[index]


def mps_to_kph(mps):
    '''
        Convert meters per second to kilometers per hour.

        Args:
            mps (float): Speed in meters per second

        Returns:
            float: Speed in kilometers per hour
    '''
    return mps * 3.6

def mps_to_miph(mps):
    '''
        Convert meters per second to miles per hour.

        Args:
            mps (float): Speed in meters per second

        Returns:
            float: Speed in miles per hour
    '''
    return mps * 2.237

def meters_to_feet(meters):
    '''
        Convert meters to feet.

        Args:
            meters (float): Distance/height in meters

        Returns:
            float: Distance/height in feet
    '''
    return meters * 3.281


def meters_to_km(meters):
    '''
        Convert meters to km.

        Args:
            meters (float): Distance/height in meters

        Returns:
            float: Distance/height in km
    '''
    return meters / 1000


def meters_to_miles(meters):
    '''
        Convert meters to miles.

        Args:
            meters (float): Distance/height in meters

        Returns:
            float: Distance/height in miles
    '''
    return meters / 1609


def mps_to_gpx_speed(units, speed):
    if units == default_settings['units']['value']:
        speed_unit = mps_to_kph(speed)
    else:
        speed_unit = mps_to_miph(speed)
    return speed_unit

def units_to_gpx_speed(units):
    if units == default_settings['units']['value']:
        speed_unit = 'km/h'
    else:
        speed_unit = 'mi/h'
    return speed_unit

def meters_to_gpx_distance(units, distance, threshold = False):
    if units == default_settings['units']['value']:
        if threshold:
            distance_value = distance if distance < threshold else meters_to_km(distance)
        else:
            distance_value = distance
    else:
        if threshold:
            distance_value = meters_to_feet(distance) if distance < threshold else meters_to_miles(distance)
        else:
            distance_value = meters_to_feet(distance)
    return distance_value

def units_to_gpx_distance(units, distance = None, threshold = False):
    if units == default_settings['units']['value']:
        if threshold:
            distance_unit = 'm' if distance < threshold else 'km'
        else:
            distance_unit = 'm'
    else:
        if threshold:
            distance_unit = 'ft' if distance < threshold else 'mi'
        else:
            distance_unit = 'ft'
    return distance_unit


def utc_ms_to_gpx_time(time_ms_utc, format = '%Y-%m-%dT%H:%M:%SZ'):
    dt = datetime.fromtimestamp(time_ms_utc / 1000, tz = timezone.utc)
    return dt.strftime(format)

def gpx_time_to_utc_ms(dt_str, format = '%Y-%m-%dT%H:%M:%SZ'):
    # Parse and convert to datetime object in UTC
    dt = datetime.strptime(dt_str, format).replace(tzinfo = timezone.utc)

    # Convert to Unix timestamp (seconds) and then to milliseconds
    return int(dt.timestamp() * 1000)

def utc_ms_time():
    return int(datetime.now(tz = timezone.utc).timestamp() * 1000)
