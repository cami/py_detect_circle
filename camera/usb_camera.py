"""USB camera backend using cv2.VideoCapture, for development on Debian."""

import time

import cv2
import numpy as np

import config
from camera.base import CameraSource

_WARMUP_ATTEMPTS = 10
_WARMUP_RETRY_DELAY_SECONDS = 0.1


class UsbCameraSource(CameraSource):
    def __init__(self, device_index: int = config.CAMERA_DEVICE_INDEX):
        self._device_index = device_index
        self._cap: cv2.VideoCapture | None = None

    def open(self) -> None:
        cap = cv2.VideoCapture(self._device_index)
        cap.set(cv2.CAP_PROP_FRAME_WIDTH, config.CAPTURE_WIDTH)
        cap.set(cv2.CAP_PROP_FRAME_HEIGHT, config.CAPTURE_HEIGHT)
        if not cap.isOpened():
            cap.release()
            raise RuntimeError(f"Could not open camera device {self._device_index}")

        # The first read(s) right after opening can fail while the sensor/driver
        # stabilizes (auto-exposure, USB stream negotiation); retry briefly here so
        # capture_frame() only raises for a genuinely unavailable camera.
        for _ in range(_WARMUP_ATTEMPTS):
            if cap.read()[0]:
                self._cap = cap
                return
            time.sleep(_WARMUP_RETRY_DELAY_SECONDS)

        cap.release()
        raise RuntimeError(
            f"Camera device {self._device_index} opened but never produced a valid frame"
        )

    def capture_frame(self) -> np.ndarray:
        if self._cap is None:
            raise RuntimeError("Camera not opened; call open() first")
        ok, frame = self._cap.read()
        if not ok:
            raise RuntimeError("Failed to read frame from camera")
        return frame

    def close(self) -> None:
        if self._cap is not None:
            self._cap.release()
            self._cap = None
