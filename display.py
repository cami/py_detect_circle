"""Shared pygame-based display: no X11/Wayland dependency, matching the RPi's SDL/DRM production display."""

import cv2
import pygame


class PygameDisplay:
    def __init__(self, caption: str):
        pygame.init()
        pygame.display.set_caption(caption)
        self._screen: pygame.Surface | None = None

    def show(self, frame) -> None:
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
