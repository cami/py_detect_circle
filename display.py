"""Shared pygame-based display: no X11/Wayland dependency, matching the RPi's SDL/DRM production display."""

import glob
import os

import cv2
import pygame

import config


def _select_spi_display_driver() -> None:
    """Point SDL at the SPI-connected DRM card so it doesn't fall back to the wrong output.

    No-ops if SDL_VIDEODRIVER is already set, or a usable DISPLAY/Wayland session is
    present (a local X server, or one reached via SSH -X/-Y forwarding, which sets
    DISPLAY to "host:N" rather than the local ":N" form), so it never overrides an
    explicit/desktop setup -- unless FORCE_SPI_DISPLAY is set, which asks for the SPI
    panel regardless (e.g. to preview on the physical screen from an SSH -X/-Y session
    without disabling forwarding). Otherwise scans /sys/class/drm/card*-SPI-* for a DRM
    card whose device node is accessible and selects it via SDL_VIDEO_KMSDRM_DEVICE_INDEX.
    """
    if "SDL_VIDEODRIVER" in os.environ:
        return
    if not os.environ.get("FORCE_SPI_DISPLAY") and (
        "WAYLAND_DISPLAY" in os.environ or os.environ.get("DISPLAY")
    ):
        return
    for spi_conn in sorted(glob.glob("/sys/class/drm/card*-SPI-*")):
        card_num = spi_conn.split("/card")[1].split("-")[0]
        if os.access(f"/dev/dri/card{card_num}", os.R_OK | os.W_OK):
            os.environ["SDL_VIDEODRIVER"] = "kmsdrm"
            os.environ["SDL_VIDEO_KMSDRM_DEVICE_INDEX"] = card_num
            return
    # No SPI card found: leave SDL's driver selection to its own defaults.


class PygameDisplay:
    def __init__(self, caption: str):
        _select_spi_display_driver()
        pygame.init()
        pygame.display.set_caption(caption)
        self._screen: pygame.Surface | None = None

    def show(self, frame) -> None:
        """Render frame at any size; internally resized to the physical display
        resolution, since the SPI panel's DRM connector only exposes that one mode
        (an unsupported set_mode() causes stray console/getty content to flash
        through instead of the frame)."""
        if frame.shape[:2] != (config.DISPLAY_HEIGHT, config.DISPLAY_WIDTH):
            frame = cv2.resize(frame, (config.DISPLAY_WIDTH, config.DISPLAY_HEIGHT))
        height, width = frame.shape[:2]
        if self._screen is None or self._screen.get_size() != (width, height):
            self._screen = pygame.display.set_mode((width, height))
        rgb = cv2.cvtColor(frame, cv2.COLOR_BGR2RGB)
        self._screen.blit(pygame.surfarray.make_surface(rgb.swapaxes(0, 1)), (0, 0))
        pygame.display.flip()

    def poll_events(self) -> list[pygame.event.Event]:
        return pygame.event.get()

    def close(self) -> None:
        pygame.quit()
