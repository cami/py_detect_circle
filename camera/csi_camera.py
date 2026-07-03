"""CSI camera backend using Picamera2, for the final RPi + Picamera2 target."""

import cv2
import numpy as np
from picamera2 import Picamera2

import config
from camera.base import CameraSource


class CsiCameraSource(CameraSource):
    @staticmethod
    def is_available() -> bool:
        try:
            return bool(Picamera2.global_camera_info())
        except Exception:
            return False

    def __init__(self) -> None:
        self._picam2: Picamera2 | None = None

    def open(self) -> None:
        picam2 = Picamera2()
        picam2.configure(picam2.create_preview_configuration(
            main={"size": (config.CAPTURE_WIDTH, config.CAPTURE_HEIGHT), "format": "BGR888"},
            # Cap max frame duration (-> max exposure time) to limit motion blur on
            # fast-moving objects; AE compensates for less light via gain instead.
            controls={"FrameDurationLimits": (8_333, config.MAX_FRAME_DURATION_US)},
        ))
        picam2.start()
        self._picam2 = picam2

    def capture_frame(self) -> np.ndarray:
        if self._picam2 is None:
            raise RuntimeError("Camera not opened; call open() first")
        # Despite the "BGR888" format name, Picamera2/libcamera actually delivers
        # pixels in R,G,B memory order here; convert so this matches the
        # CameraSource contract (BGR, like cv2.VideoCapture's USB backend).
        return cv2.cvtColor(self._picam2.capture_array(), cv2.COLOR_RGB2BGR)

    def close(self) -> None:
        if self._picam2 is not None:
            self._picam2.stop()
            self._picam2.close()
            self._picam2 = None
