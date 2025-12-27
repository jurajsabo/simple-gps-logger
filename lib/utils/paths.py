import os
import json

from kivy                   import platform
from kivy.storage.jsonstore import JsonStore

from config import default_settings


gnss_log         = 'gnss_log.json'
settings_json    = 'settings.json'
track_stats_json = 'track_stats.json'
tracks_folder    = 'tracks'
working_path     = os.getcwd()


def check_path(path, file, path_only = False):
    path_join = os.path.join(path, file)

    try:
        # GNSS
        if file == gnss_log:
            if path_only:
                print('[PATHS]', f'Gnss log path: {path_join}')
                return path_join # Returns path

            else:
                if not os.path.exists(path_join):
                    with open(path_join, 'w', encoding = 'utf-8') as f:
                        json.dump({}, f)
                        print('[PATHS]', f'Created new gnss_log log: {path_join}')
                else:
                    with open(path_join, 'r', encoding = 'utf-8') as f:
                        content = f.read().strip()
                    content_dict = json.loads(content)
                    if content_dict != {}:
                        with open(path_join, 'w', encoding = 'utf-8') as f:
                            json.dump({}, f)
                        print('[PATHS]', f'Log is not empty, new gnss_log log created: {path_join}')

                print('[PATHS]', f'Using gnss_log log on path: {path_join}')
                return path_join

        # SETTINGS
        if file == settings_json:
            if path_only:
                print('[PATHS]', f'Settings path: {path_join}')
                return path_join # Returns path

            else:
                if not os.path.exists(path_join):
                    with open(path_join, 'w', encoding = 'utf-8') as f:
                        json.dump(default_settings, f)
                        print('[PATHS]', f'Created new settings file: {path_join}')

                print('[PATHS]', f'Using settings store on: {path_join}')
                return JsonStore(path_join, indent = 2)  # Returns store

        # TRACK STATS
        if file == track_stats_json:
            if path_only:
                print('[PATHS]', f'Track stats path: {path_join}')
                return path_join # Returns path

            else:
                if not os.path.exists(path_join):
                    with open(path_join, 'w', encoding = 'utf-8') as f:
                        json.dump({}, f)
                        print('[PATHS]', f'Created new track stats file: {path_join}')

                print('[PATHS]', f'Using track stats store on: {path_join}')
                return JsonStore(path_join, indent = 2)  # Returns store

        # TRACK FOLDER
        if file == tracks_folder:
            if path_only:
                print('[PATHS]', f'Tracks folder path: {path_join}')
                return path_join  # Returns path

            else:
                if not os.path.exists(path_join):
                    os.makedirs(path_join)
                    print('[PATHS]', f'New track folder created: {path_join}')

                print('[PATHS]', f'Using tracks folder path: {path_join}')
                return path_join # Returns path

    except Exception as e:
        print('[PATHS]', f'Error loading from {path_join}: {e}')
        raise  # re-raise so caller can handle fallback


def load_path(file, path_only = False):
    try:
        if platform == 'android':
            from android.storage import app_storage_path

            # First attempt: Android app working
            android_storage_path = app_storage_path()
            return check_path(android_storage_path, file, path_only)
        else:
            return check_path(working_path, file, path_only)

    except Exception as e:
        # Fallback: just use in-memory alternatives
        print('[PATHS]', f'Storage not available. Using defaults only: {e}')
        if file == settings_json:
            return default_settings
        elif file == track_stats_json:
            return {}
