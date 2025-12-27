import os

from kivy       import platform
from config     import points_limit, toast_duration
from kivy.clock import Clock

from kivymd.material_resources import dp
from kivymd.toast              import toast

from kivymd.uix.boxlayout  import MDBoxLayout
from kivymd.uix.list       import MDList
from kivymd.uix.screen     import MDScreen
from kivymd.uix.scrollview import MDScrollView

from lib.gpx.csvRecorder  import CSVRecorder
from lib.gpx.gpxRecorder  import GPXRecorder
from lib.gpx.gpxRecorder1 import GPXRecorder1

from lib.utils.buttons  import CustomFlatButton
from lib.utils.label    import MockBanner
from lib.utils.listItem import ListItem
from lib.utils.paths    import tracks_folder, working_path, load_path, track_stats_json
from lib.utils.popups   import CustomDialog
from lib.utils.saver    import Saver

from lib.gpx.csv_stat_parser import parse_csv_dict, parse_all_csv_statistics
from lib.gpx.gpx_stat_parser import parse_all_gpx_statistics, parse_gpx_trkseg


if platform == 'android':
    from android.permissions import check_permission, Permission
    from jnius               import autoclass

    Build_VERSION = autoclass('android.os.Build$VERSION')


class TracksScreen(MDScreen, Saver):

    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        print('[TRACK]', 'init')

        # storage init
        self.folder  = load_path(tracks_folder)
        self.storage = load_path(track_stats_json)

        self.dialog = CustomDialog \
        (
            buttons = \
            [
                CustomFlatButton(id = 'delete',   text = 'delete',   on_press = self.on_press, disabled = False),
                CustomFlatButton(id = 'download', text = 'download', on_press = self.on_press, disabled = False),
            ]

        )
        self.dialog_download = self.dialog.children[0].children[0].children[0].children[0]

        # Tracks init
        self.track          = None
        self.last_signature = None  # signature for change tracking

        # Main layout
        main_layout = MDBoxLayout(orientation = 'vertical', spacing = 0)

        # Mock banner
        self.mock_banner = MockBanner()

        # Remaining layout
        main_layout.add_widget(self.mock_banner)
        main_layout.add_widget \
        (
            MDScrollView \
            (
                MDList(spacing = dp(2))
            )

        )

        # Add the main layout to screen
        self.add_widget(main_layout)
        self.list = main_layout.children[0].children[0]

        if platform == 'android':
            from androidstorage4kivy import SharedStorage
            self.Environment = autoclass('android.os.Environment')
            self.ss          = SharedStorage()

    def name_extraction(self, track, sep = '.'):
        name_split = track.split(sep)
        name       = name_split[0]
        suffix     = name_split[1]
        return name, suffix

    def name_reconstruction(self, name, suffix, sep = '.'):
        return f'{name}{sep}{suffix}'

    def finalize(self):
        try:
            for track in os.listdir(self.folder):
                if track.endswith('_metric') or track.endswith('_imperial'):
                    try:
                        track_name, suffix = self.name_extraction(track)
                        format,     units  = self.name_extraction(suffix, '_')

                        extension = format[:3]
                        name_file = self.name_reconstruction(track_name, extension)

                        if format == 'gpx1':
                            recorder = GPXRecorder1(output_file = name_file, work_path = self.folder, units = units)
                        elif format == 'csv':
                            recorder = CSVRecorder(output_file = name_file, work_path = self.folder, units = units)
                        else:
                            recorder = GPXRecorder(output_file = name_file, work_path = self.folder, units = units)

                        recorder.generate_final_file(True)
                        print('[TRACK]', f'File {name_file} reconstructed')
                        toast(f'{name_file} reconstructed')

                    except Exception as e:
                        print('[TRACK]', f"File {track} couldn't be reconstructed and will be deleted: {e}")
                        toast(f"{track} couldn't be reconstructed")

                        try:
                            track_path = os.path.join(self.folder, track)
                            os.remove(track_path)
                            print('[TRACK]', f'File {track} was deleted')
                        except Exception as e:
                            print('[TRACK]', f"File {track} couldn't be deleted: {e}")

        except Exception as e:
            print('[TRACK]', f'Finalization error: {e}')

    def scan_tracks(self):
        return [track for track in os.listdir(self.folder) if track.endswith('.gpx') or track.endswith('.csv')]

    def scan_storage(self):
        tracks  = []
        for name in self.storage:
            format = self.storage[name]['format']['value']
            track  = self.name_reconstruction(name, format)
            tracks.append(track)
        return tracks

    def signature(self, tracks):
        tracks_sorted = sorted(tracks, reverse = True)
        sig = None
        for track in tracks_sorted:
            if sig is None:
                sig = track
            else:
                sig += f'|{track}'
        return sig

    def synchronize(self):
        # synchronize the storage (or in-memory dict storage) with the track folder
        try:
            tracks    = self.scan_tracks()
            signature = self.signature(tracks)

            if signature == self.last_signature:
                print('[TRACK]', 'no changes:', signature)
            else:
                print('[TRACK]', 'changes detected:', f'{self.last_signature} -> {signature}')
                storage = self.scan_storage()

                for track in tracks:
                    if track not in storage:
                        self.put_storage(track)

                for track in storage:
                    if track not in tracks:
                        self.remove_storage(track)

                self.show()
                self.last_signature = signature

        except Exception as e:
            print('[TRACK]', f'Synchronization error: {e}')

    def put_storage(self, track):
        try:
            track_path = os.path.join(self.folder, track)
            mtime      = os.path.getmtime(track_path)

            with open(track_path, 'r', encoding = 'utf-8') as f:
                content = f.read()

            if track.endswith('.csv'):
                stats  = parse_all_csv_statistics(content)
                loc    = parse_csv_dict(content)
                format = 'csv'
            else:
                stats  = parse_all_gpx_statistics(content)
                loc    = parse_gpx_trkseg(content)
                format = 'gpx'

            points_total = len(loc)
            if points_total <= points_limit:
                points_to_show = loc
            else:
                step = max(1, points_total // points_limit)
                points_to_show = loc[::step]

            track_data = \
            {
                'mtime':          {'value': mtime},
                'format':         {'value': format},
                'units':          {'value': stats['units']['value']},
                'points':         {'value': stats['track_points']['value']},
                'duration':       {'value': stats['duration']['value']},
                'distance':       {
                                      'value': stats['distance']['value'],
                                      'unit':  stats['distance']['unit']
                                  },
                'altitude_gap':   {
                                      'value': stats['net_elevation_change']['value'],
                                      'unit':  stats['net_elevation_change']['unit']
                                  },
                'speed_max':      {
                                      'value': stats['speed_max']['value'],
                                      'unit':  stats['speed_max']['unit']
                                  },
                'speed_avg':      {
                                      'value': stats['speed_avg']['value'],
                                      'unit':  stats['speed_avg']['unit']
                                  },
                'points_to_show': {'value': points_to_show}
            }
            if format == 'gpx':
                track_data.update({'version': {'value': stats['version']['value']}})

            track_name = self.name_extraction(track)[0]
            self.instant_save(track_name, track_data)

        except Exception as e:
            print('[TRACK]', f"File {track} couldn't be inserted into the storage: {e}")

    def remove_storage(self, track):
        try:
            track_name = self.name_extraction(track)[0]

            if isinstance(self.storage, dict):
                self.storage.pop(track_name)
                print('[TRACK]', f'File {track} removed from the in-memory dict storage')
            else:
                self.storage.delete(track_name)
                print('[TRACK]', f'File {track} removed from the storage')

        except Exception as e:
            print('[TRACK]', f"File {track} couldn't be removed from the storage: {e}")

    def delete_track(self, track):
        try:
            track_path = os.path.join(self.folder, track)
            os.remove(track_path)
            print('[TRACK]', f'File {track} deleted from the folder')
            toast(f'{track} deleted')

        except Exception as e:
            print('[TRACK]', f"File {track} couldn't be deleted from the folder: {e}")
            toast(f"{track} couldn't be deleted")

    def show(self):
        self.list.clear_widgets()
        storaged        = [{'name': name, 'mtime': self.storage[name]['mtime']['value']} for name in self.storage]
        storaged_sorted = sorted(storaged, key = lambda d: d['mtime'], reverse = True)

        for d in storaged_sorted:
            name      = d['name']
            stats     = self.storage[name]
            format    = stats['format']['value']
            file_name = self.name_reconstruction(name, format)
            self.list.add_widget(ListItem(txt = file_name, stats = stats, item_press = self.on_press))

    def download(self, track):
        try:
            track_path = os.path.join(self.folder, track)
            if platform == 'android':
                SDK_INT = int(Build_VERSION.SDK_INT)

                if 23 <= SDK_INT <= 29 and not check_permission(Permission.WRITE_EXTERNAL_STORAGE):
                    track_storage = None
                else:
                    track_storage = self.ss.copy_to_shared(track_path, collection = self.Environment.DIRECTORY_DOWNLOADS) # copy to shared dir downloads

            else:
                track_storage = os.path.join(working_path, track)
                with open(track_path, 'r', encoding = 'utf-8') as src, open(track_storage, 'w', encoding = 'utf-8') as dst:
                    source = src.read() # read the whole file at once
                    dst.write(source)


            print('[TRACK]', f'Track copied: {track} -> {track_storage}')
            if track_storage is not None:
                if track_storage.lower().endswith(track.lower()):
                    toast('downloaded to')
                    Clock.schedule_once(lambda dt: toast(f'{track_storage}'), toast_duration)
                else:
                    toast(f'{track} downloaded...')

            else:
                toast('external storage access DENIED')


        except Exception as e:
            print('[TRACK]', f"File {track} couldn't be downloaded: {e}")
            toast(f"{track} couldn't be downloaded")

    def stats(self, track):
        try:
            track_name  = self.name_extraction(track)[0]
            track_stats = self.storage[track_name]

            text = \
            (
                '\n'
                f"units: {track_stats['units']['value']}\n"
                f"points: {track_stats['points']['value']}\n"
                f"duration: {track_stats['duration']['value']}\n"
                f"distance: {track_stats['distance']['value']} {track_stats['distance']['unit']}\n"
                f"alt. gap: {track_stats['altitude_gap']['value']} {track_stats['altitude_gap']['unit']}\n"
                f"max. speed: {track_stats['speed_max']['value']} {track_stats['speed_max']['unit']}\n"
                f"avg. speed: {track_stats['speed_avg']['value']} {track_stats['speed_avg']['unit']}"
            )
            if track.endswith('.gpx'):
                text = f"\nversion: {track_stats['version']['value']} {text}"
            return text

        except Exception as e:
            print('[TRACK]', f"File statistics for {track} can't be displayed: {e}")
            toast(f"{track} statistics can't be displayed")

    def stats_pop(self, track):
        text = self.stats(track)
        self.dialog.text  = text
        self.dialog.title = track
        self.dialog.open()

    def on_press(self, btn):
        if btn.id == 'delete':
            self.delete_track(self.track)
            self.dialog.dismiss()
            self.synchronize()
        elif btn.id == 'download':
            self.download(self.track)
        else:
            self.track = btn.children[0].children[0].children[0].text
            self.stats_pop(self.track)

    def on_size(self, *args):
        self.mock_banner.update_banner_height()
