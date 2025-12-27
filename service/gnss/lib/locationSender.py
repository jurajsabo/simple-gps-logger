import json
from lib.utils.paths import load_path, tracks_folder, gnss_log

from lib.gpx.csvRecorder  import CSVRecorder
from lib.gpx.gpxRecorder  import GPXRecorder
from lib.gpx.gpxRecorder1 import GPXRecorder1


class LocationSender:
    def __init__(self):
        print('[GNSS]', 'Location sender init')

        # Settings init
        self.folder   = load_path(tracks_folder)
        self.gnss_log = load_path(gnss_log, path_only = True)

        # Last init
        self.point_last = None

        # States init
        self.is_recording = 0

    def gnss_recorder(self, point):
        try:
            if self.is_recording == 1:
                self.recorder.start_recording()
                self.recorder.resume_recording()
                self.recorder.add_point(point)

            elif self.is_recording == -1:
                self.recorder.pause_recording()

            else:
                self.recorder.stop_recording()

        except Exception as e:
            print('[GNSS]', f'Recorder: {e}')

    def gnss_sender(self, point):
        try:
            with open(self.gnss_log, 'w', encoding = 'utf-8') as f:
                json.dump(point, f, indent = 2)

        except Exception as e:
            print('[GNSS]', f'Sender: {e}')

    def listen(self, point):
        # Point check
        if point and point != self.point_last:
            # Record point
            self.gnss_recorder(point)
            # Send point
            self.gnss_sender(point)

        self.point_last = point

    def settings_recorder(self, format, units, output_file = None):
        if format == 'GPX 1.1':
            self.recorder = GPXRecorder1(output_file = output_file, work_path = self.folder, units = units)
        elif format == 'CSV':
            self.recorder = CSVRecorder(output_file = output_file, work_path = self.folder, units = units)
        else:
            self.recorder = GPXRecorder(output_file = output_file, work_path = self.folder, units = units)
