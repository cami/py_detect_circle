"""Interactive tool to tune detection/classification thresholds against the live camera feed.

Displays via the shared display.PygameDisplay (see DESIGN.md for why). No sliders/widgets:
values are burned into the frame as text, and are changed with the keyboard.

Controls: Up/Down selects a parameter, Left/Right changes its value, 's' prints the current
values in a config.py-ready format, 'q'/Esc quits.
"""

import cv2
import pygame

import config
from annotation import draw_judgment
from camera.usb_camera import UsbCameraSource
from detection.circle_detector import find_circle
from detection.color_classifier import classify
from display import PygameDisplay


class _Param:
    """A config.py scalar tunable via getattr/setattr, except GAUSSIAN_BLUR_KSIZE,
    which is stored as an (n, n) tuple and is kept odd."""

    def __init__(self, name: str, step, minimum, maximum):
        self.name = name
        self.step = step
        self.minimum = minimum
        self.maximum = maximum

    def get(self):
        if self.name == "GAUSSIAN_BLUR_KSIZE":
            return config.GAUSSIAN_BLUR_KSIZE[0]
        return getattr(config, self.name)

    def adjust(self, direction: int) -> None:
        value = self.get() + direction * self.step
        value = max(self.minimum, min(self.maximum, value))
        value = round(value, 3) if isinstance(self.step, float) else int(value)
        if self.name == "GAUSSIAN_BLUR_KSIZE":
            value = value if value % 2 == 1 else value + 1
            value = (value, value)
        setattr(config, self.name, value)


_PARAMS = [
    _Param("CIRCULARITY_THRESHOLD", 0.01, 0.0, 1.0),
    _Param("MIN_CONTOUR_AREA", 100, 0, 100_000),
    _Param("MAX_CONTOUR_AREA", 1000, 1000, 500_000),
    _Param("GAUSSIAN_BLUR_KSIZE", 2, 1, 31),
    _Param("MASK_SHRINK_RATIO", 0.05, 0.1, 1.0),
    _Param("WHITE_SAT_MAX", 5, 0, 255),
    _Param("WHITE_VAL_MIN", 5, 0, 255),
    _Param("ORANGE_HUE_MIN", 1, 0, 179),
    _Param("ORANGE_HUE_MAX", 1, 0, 179),
    _Param("ORANGE_SAT_MIN", 5, 0, 255),
]


def _draw_overlay(frame, circle, judgment, selected_index: int):
    annotated = draw_judgment(frame, circle, judgment, font_scale=0.8, text_y=25)

    y = 50
    for i, param in enumerate(_PARAMS):
        marker = ">" if i == selected_index else " "
        text_color = (0, 255, 255) if i == selected_index else (255, 255, 255)
        cv2.putText(annotated, f"{marker} {param.name} = {param.get()}", (10, y),
                    cv2.FONT_HERSHEY_SIMPLEX, 0.45, text_color, 1)
        y += 18

    return annotated


def _print_current_values() -> None:
    print("# --- config.py に貼り付け可能な現在値 ---")
    for param in _PARAMS:
        value = param.get()
        formatted = f"({value}, {value})" if param.name == "GAUSSIAN_BLUR_KSIZE" else value
        print(f"{param.name} = {formatted}")
    print("# ---------------------------------------")


def main() -> None:
    display = PygameDisplay("calibration")
    selected_index = 0
    running = True

    with UsbCameraSource() as camera:
        print("Up/Downでパラメータ選択、Left/Rightで値を変更、's'で現在値を出力、'q'/Escで終了します。")
        while running:
            frame = camera.capture_frame()
            circle = find_circle(frame)
            judgment = None
            if circle is not None:
                judgment, _mean_hsv = classify(frame, circle)

            annotated = _draw_overlay(frame, circle, judgment, selected_index)
            display.show(annotated)

            for event in display.poll_events():
                if event.type == pygame.QUIT:
                    running = False
                elif event.type == pygame.KEYDOWN:
                    if event.key in (pygame.K_q, pygame.K_ESCAPE):
                        running = False
                    elif event.key == pygame.K_UP:
                        selected_index = (selected_index - 1) % len(_PARAMS)
                    elif event.key == pygame.K_DOWN:
                        selected_index = (selected_index + 1) % len(_PARAMS)
                    elif event.key == pygame.K_RIGHT:
                        _PARAMS[selected_index].adjust(1)
                    elif event.key == pygame.K_LEFT:
                        _PARAMS[selected_index].adjust(-1)
                    elif event.key == pygame.K_s:
                        _print_current_values()

    display.close()


if __name__ == "__main__":
    main()
