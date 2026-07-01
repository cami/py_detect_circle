"""Shared drawing of the detection/judgment overlay, used by main.py and calibration.py."""

from typing import Optional

import cv2

from detection.circle_detector import Circle
from detection.color_classifier import Judgment

LABEL_COLORS = {
    Judgment.OK: (0, 200, 0),
    Judgment.NG: (0, 0, 255),
    Judgment.ERROR: (0, 200, 200),
}


def draw_judgment(
    frame,
    circle: Optional[Circle],
    judgment: Optional[Judgment],
    font_scale: float = 1.0,
    text_y: int = 30,
):
    annotated = frame.copy()
    if circle is None:
        cv2.putText(annotated, "no circle", (10, text_y), cv2.FONT_HERSHEY_SIMPLEX,
                    font_scale, LABEL_COLORS[Judgment.ERROR], 2)
        return annotated

    color = LABEL_COLORS[judgment]
    cv2.circle(annotated, (int(circle.cx), int(circle.cy)), int(circle.r), color, 2)
    cv2.circle(annotated, (int(circle.cx), int(circle.cy)), 3, color, -1)
    cv2.putText(annotated, judgment.value, (10, text_y), cv2.FONT_HERSHEY_SIMPLEX, font_scale, color, 2)
    return annotated
