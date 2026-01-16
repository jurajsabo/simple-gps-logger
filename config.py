
author = 'Juraj Sabo'
year   = '2026'

app_name    = 'Simple GPS Logger'
app_version = '1.0.2'

urls = \
{
    'web':     f'https://{author.lower().replace(" ", "")}.github.io/{app_name.lower().replace(" ", "-")}',
    'privacy': f'https://{author.lower().replace(" ", "")}.github.io/{app_name.lower().replace(" ", "-")}/privacy-policy.html',
	'license': f'https://{author.lower().replace(" ", "")}.github.io/{app_name.lower().replace(" ", "-")}/LICENSE',
	'code':    f'https://github.com/{author.lower().replace(" ", "")}/{app_name.lower().replace(" ", "-")}'
}


ADMOB_BANNER_ID_default = 'ca-app-pub-3940256099942544/6300978111'

params = \
{
	'interval': {'min': 1, 'max': 60},
	'distance': {'min': 0, 'max': 1000},
	'screen':   ['always on', 'timeout'],
	'theme':    {'dark': 'red', 'light': 'blue'},
	'units':    ['metric', 'imperial'],
	'format':   ['GPX 1.0', 'GPX 1.1', 'CSV']
}

default_settings = \
{
	'app_state':    {'value': 0},
	'is_recording': {'value': 0},
	'interval':     {'value': 1},
	'distance':     {'value': 0},
	'screen':       {'value': 'always on'},
	'theme':        {'value': 'dark'},
	'units':        {'value': 'metric'},
	'format':       {'value': 'GPX 1.0'}
}

# Package and generated service class
PKG     =    'org.prod.simplegpslogger'
SERVICE = f'{PKG}.ServiceGpsservice'

# Theme
default_material_style = 'M3'

# Toast
toast_duration = 2.5

# fps
FPS = 10

# Track thumbnail
points_limit = 1200
