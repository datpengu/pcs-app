"""Single-camera worker shared by the API and dashboard."""

import threading
import time

import cv2

from config import settings
from counter import PeopleCounter
from detector import PersonDetector
from storage import CounterStorage


class CameraService:
    def __init__(self):
        self._lock = threading.Lock()
        self._frame_ready = threading.Condition(self._lock)
        self._running = False
        self._thread = None
        self._latest_jpeg = None
        self._storage = CounterStorage(settings.DATABASE_PATH)
        self._stats = {"inside": 0, "entered": 0, "exited": 0, "line_x": 0, "status": "stopped"}

    def start(self):
        if self._thread and self._thread.is_alive():
            return
        self._running = True
        self._thread = threading.Thread(target=self._run, name="camera-worker")
        self._thread.start()

    def stop(self):
        self._running = False
        with self._frame_ready:
            self._frame_ready.notify_all()
        if self._thread:
            self._thread.join(timeout=5)

    def stats(self):
        with self._lock:
            return self._stats.copy()

    def history(self, days):
        return self._storage.daily_history(days)

    def mjpeg_stream(self):
        previous_frame = None
        while self._running:
            with self._frame_ready:
                self._frame_ready.wait_for(
                    lambda: (self._latest_jpeg is not None and self._latest_jpeg is not previous_frame) or not self._running,
                    timeout=2,
                )
                frame = self._latest_jpeg
            if frame is None or frame is previous_frame:
                continue
            previous_frame = frame
            yield b"--frame\r\nContent-Type: image/jpeg\r\n\r\n" + frame + b"\r\n"

    def _run(self):
        camera = cv2.VideoCapture(settings.CAMERA_INDEX)
        camera.set(cv2.CAP_PROP_FRAME_WIDTH, settings.CAMERA_WIDTH)
        camera.set(cv2.CAP_PROP_FRAME_HEIGHT, settings.CAMERA_HEIGHT)
        if not camera.isOpened():
            self._set_status("camera_error")
            return

        try:
            restored = self._storage.restore_today()
            detector = PersonDetector(settings.MODEL_NAME, settings.CONFIDENCE)
            counter = PeopleCounter(
                line_position=settings.LINE_POSITION,
                margin=settings.LINE_MARGIN,
                confirmation_frames=settings.CONFIRMATION_FRAMES,
                initial_inside=restored["inside"],
                initial_entered=restored["entered"],
                initial_exited=restored["exited"],
            )
            self._set_status("running")
            while self._running:
                success, frame = camera.read()
                if not success:
                    self._set_status("camera_error")
                    time.sleep(0.2)
                    continue
                people = detector.track(frame)
                stats = counter.update(people, frame.shape[1])
                for event in stats.pop("events"):
                    self._storage.record_crossing(event)
                self._draw_overlay(frame, people, stats)
                encoded, jpeg = cv2.imencode(".jpg", frame)
                if encoded:
                    with self._frame_ready:
                        self._latest_jpeg = jpeg.tobytes()
                        self._stats = {**stats, "status": "running"}
                        self._frame_ready.notify_all()
        except Exception:
            self._set_status("processing_error")
        finally:
            camera.release()
            with self._frame_ready:
                self._frame_ready.notify_all()

    def _set_status(self, status):
        with self._lock:
            self._stats["status"] = status

    @staticmethod
    def _draw_overlay(frame, people, stats):
        cv2.line(frame, (stats["line_x"], 0), (stats["line_x"], frame.shape[0]), (255, 0, 0), 2)
        for person in people:
            x1, y1, x2, y2 = person["box"]
            cv2.rectangle(frame, (x1, y1), (x2, y2), (0, 255, 0), 2)
            cv2.putText(frame, f"ID: {person['id']}", (x1, y1 - 10), cv2.FONT_HERSHEY_SIMPLEX, 0.6, (0, 255, 0), 2)
        for text, position, color, scale in (
            (f"Inside: {stats['inside']}", (20, 40), (0, 255, 0), 0.9),
            (f"Entered: {stats['entered']}", (20, 75), (0, 255, 0), 0.7),
            (f"Exited: {stats['exited']}", (20, 105), (0, 0, 255), 0.7),
        ):
            cv2.putText(frame, text, position, cv2.FONT_HERSHEY_SIMPLEX, scale, color, 2)
