"""Camera source abstraction so USB (cv2.VideoCapture) and Picamera2 backends share one interface."""

from abc import ABC, abstractmethod

import numpy as np


class CameraSource(ABC):
    @abstractmethod
    def open(self) -> None:
        ...

    @abstractmethod
    def capture_frame(self) -> np.ndarray:
        """Return a single BGR frame."""
        ...

    @abstractmethod
    def close(self) -> None:
        ...

    def __enter__(self) -> "CameraSource":
        self.open()
        return self

    def __exit__(self, exc_type, exc_val, exc_tb) -> None:
        self.close()
