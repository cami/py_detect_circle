"""Pick the best available camera backend: CSI (Picamera2) first, USB webcam as fallback."""

from camera.base import CameraSource
from camera.usb_camera import UsbCameraSource


def open_camera_source() -> CameraSource:
    try:
        from camera.csi_camera import CsiCameraSource
    except ImportError:
        # picamera2 isn't installed (e.g. developing on a plain Debian box) -- USB only.
        return UsbCameraSource()

    if CsiCameraSource.is_available():
        return CsiCameraSource()
    return UsbCameraSource()
