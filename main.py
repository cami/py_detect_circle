"""Continuously watch the camera feed and judge each object once as it crosses the judge zone."""

import datetime
import time
from pathlib import Path

import cv2
import numpy as np
import pygame

import config
from annotation import draw_judgment
from camera.factory import open_camera_source
from detection.circle_detector import find_circle
from detection.color_classifier import classify
from display import PygameDisplay
from trigger import TriggerStateMachine


def _save_annotated(annotated) -> Path:
    output_dir = Path(config.OUTPUT_DIR)
    output_dir.mkdir(exist_ok=True)
    timestamp = datetime.datetime.now().strftime("%Y%m%d_%H%M%S_%f")
    path = output_dir / f"{timestamp}.png"
    cv2.imwrite(str(path), annotated)
    return path


def _show_preview(display: PygameDisplay, annotated) -> None:
    """Resize to the physical display resolution before rendering."""
    display_frame = cv2.resize(annotated, (config.DISPLAY_WIDTH, config.DISPLAY_HEIGHT))
    display.show(display_frame)


def main() -> None:
    display = PygameDisplay("detect_circle")
    # Open the window immediately (blank) so the quit key works even before the
    # first live frame.
    display.show(np.zeros((config.DISPLAY_HEIGHT, config.DISPLAY_WIDTH, 3), dtype=np.uint8))

    live_preview_interval = 1.0 / config.LIVE_PREVIEW_FPS
    last_preview_time = 0.0
    hold_until = 0.0

    trigger = None
    running = True
    with open_camera_source() as camera:
        print("Watching for circular objects. Press 'q' in the preview window to quit.")
        while running:
            try:
                frame = camera.capture_frame()
            except RuntimeError as exc:
                print(f"camera read failed, skipping frame: {exc}")
                continue

            # Built from the actual frame width rather than config.CAPTURE_WIDTH, since
            # the camera may silently deliver a different resolution than requested.
            if trigger is None:
                trigger = TriggerStateMachine(frame_width=frame.shape[1])

            circle = find_circle(frame)
            now = time.monotonic()

            if circle is not None:
                zone_min = frame.shape[1] * config.JUDGE_ZONE_X_MIN_RATIO
                zone_max = frame.shape[1] * config.JUDGE_ZONE_X_MAX_RATIO
                in_zone = zone_min <= circle.cx <= zone_max
                print(f"  circle seen: cx={circle.cx:.0f} r={circle.r:.0f} in_zone={in_zone}")

            if trigger.step(circle):
                judgment, mean_hsv = classify(frame, circle)
                print(
                    f"[{datetime.datetime.now().isoformat(timespec='seconds')}] "
                    f"judgment={judgment.value} "
                    f"circle=(cx={circle.cx:.1f}, cy={circle.cy:.1f}, r={circle.r:.1f}) "
                    f"mean_hsv=({mean_hsv[0]:.1f}, {mean_hsv[1]:.1f}, {mean_hsv[2]:.1f})"
                )
                annotated = draw_judgment(frame, circle, judgment)
                saved_path = _save_annotated(annotated)
                print(f"  saved: {saved_path}")
                _show_preview(display, annotated)
                last_preview_time = now
                hold_until = now + config.JUDGMENT_HOLD_SECONDS
            elif now >= hold_until and now - last_preview_time >= live_preview_interval:
                # No judgment this frame and the previous judgment's hold period (if
                # any) has elapsed: refresh with the live feed at LIVE_PREVIEW_FPS.
                _show_preview(display, frame)
                last_preview_time = now

            for event in display.poll_events():
                if event.type == pygame.QUIT:
                    running = False
                elif event.type == pygame.KEYDOWN and event.key in (pygame.K_q, pygame.K_ESCAPE):
                    running = False

    display.close()


if __name__ == "__main__":
    main()
