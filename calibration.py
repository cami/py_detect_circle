"""Interactive tool to tune detection/classification thresholds against the live camera feed.

Displays via the shared display.PygameDisplay (see DESIGN.md for why). No sliders/widgets:
values are burned into the frame as text, and are changed with the keyboard.

Controls: Up/Down selects a parameter, Left/Right changes its value, 'h' shows a help screen
(description/min/max/current value for each parameter), 's' prints the current values in a
config.py-ready format, 'q'/Esc quits (Esc returns from the help screen instead, if it's open).

Help screen text is kept in plain ASCII: cv2.putText (OpenCV's Hershey fonts) cannot render
non-ASCII glyphs, and a CJK-capable font is not guaranteed to be installed on the RPi target.
"""

import cv2
import numpy as np
import pygame

import config
from annotation import draw_judgment
from camera.factory import open_camera_source
from detection.circle_detector import find_circle
from detection.color_classifier import classify
from display import PygameDisplay


class _Param:
    """A config.py scalar tunable via getattr/setattr, except GAUSSIAN_BLUR_KSIZE,
    which is stored as an (n, n) tuple and is kept odd."""

    def __init__(self, name: str, description: str, step, minimum, maximum):
        self.name = name
        self.description = description
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
    _Param("CIRCULARITY_THRESHOLD",
           "Min circularity (4*pi*area/perimeter^2) to accept a contour as a circle",
           0.01, 0.0, 1.0),
    _Param("MIN_CONTOUR_AREA", "Minimum contour area in pixels^2 to be considered",
           100, 0, 100_000),
    _Param("MAX_CONTOUR_AREA", "Maximum contour area in pixels^2 to be considered",
           1000, 1000, 500_000),
    _Param("GAUSSIAN_BLUR_KSIZE", "Blur kernel size before thresholding (kept odd)",
           2, 1, 31),
    _Param("MASK_SHRINK_RATIO", "Shrink ratio applied to the circle radius before sampling color",
           0.05, 0.1, 1.0),
    _Param("WHITE_SAT_MAX", "Max HSV saturation to classify as white (OK)",
           5, 0, 255),
    _Param("WHITE_VAL_MIN", "Min HSV value/brightness to classify as white (OK)",
           5, 0, 255),
    _Param("ORANGE_HUE_MIN", "Min HSV hue to classify as orange (NG)",
           1, 0, 179),
    _Param("ORANGE_HUE_MAX", "Max HSV hue to classify as orange (NG)",
           1, 0, 179),
    _Param("ORANGE_SAT_MIN", "Min HSV saturation to classify as orange (NG)",
           5, 0, 255),
]

# Snapshot of config.py's values as loaded at startup -- i.e. what a freshly started
# main.py currently uses, independent of whatever this session goes on to try live.
_BASELINE_VALUES = {param.name: param.get() for param in _PARAMS}


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


def _format_value(name: str, value):
    return f"({value}, {value})" if name == "GAUSSIAN_BLUR_KSIZE" else value


def _print_current_values() -> None:
    print("# --- config.py に貼り付け可能な現在値 ---")
    for param in _PARAMS:
        print(f"{param.name} = {_format_value(param.name, param.get())}")
    print("# ---------------------------------------")


def _draw_help_screen(width: int, height: int):
    frame = np.zeros((height, width, 3), dtype=np.uint8)
    cv2.putText(frame, "HELP  (Esc: back, q: quit)", (10, 25),
                cv2.FONT_HERSHEY_SIMPLEX, 0.65, (255, 255, 255), 2)

    y = 50
    for param in _PARAMS:
        current = _format_value(param.name, param.get())
        baseline = _format_value(param.name, _BASELINE_VALUES[param.name])
        header = (
            f"{param.name}  cur={current}  main.py={baseline}  "
            f"range=[{param.minimum}, {param.maximum}]"
        )
        cv2.putText(frame, header, (10, y), cv2.FONT_HERSHEY_SIMPLEX, 0.42, (0, 255, 255), 1)
        y += 16
        cv2.putText(frame, f"  {param.description}", (10, y),
                    cv2.FONT_HERSHEY_SIMPLEX, 0.4, (200, 200, 200), 1)
        y += 22

    return frame


def main() -> None:
    display = PygameDisplay("calibration")
    selected_index = 0
    showing_help = False
    running = True

    with open_camera_source() as camera:
        print("Up/Downでパラメータ選択、Left/Rightで値を変更、'h'でヘルプ、"
              "'s'で現在値を出力、'q'/Escで終了します。")
        while running:
            frame = camera.capture_frame()

            if showing_help:
                display.show(_draw_help_screen(frame.shape[1], frame.shape[0]))
            else:
                circle = find_circle(frame)
                judgment = None
                if circle is not None:
                    judgment, _mean_hsv = classify(frame, circle)
                display.show(_draw_overlay(frame, circle, judgment, selected_index))

            for event in display.poll_events():
                if event.type == pygame.QUIT:
                    running = False
                elif event.type != pygame.KEYDOWN:
                    continue
                elif showing_help:
                    if event.key == pygame.K_ESCAPE:
                        showing_help = False
                    elif event.key == pygame.K_q:
                        running = False
                elif event.key in (pygame.K_q, pygame.K_ESCAPE):
                    running = False
                elif event.key == pygame.K_h:
                    showing_help = True
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
