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
    font_scale: float = 6.0,
    text_y: Optional[int] = None,
):
    """text_y=None (main.py's default) centers the label on screen at 3x scale.
    calibration.py passes an explicit font_scale/text_y to keep its small,
    top-left label so it doesn't collide with the tuning overlay below it.
    """
    annotated = frame.copy()
    thickness = max(2, round(font_scale * 2))

    def _put_text(text: str, color) -> None:
        if text_y is None:
            (text_w, text_h), _ = cv2.getTextSize(text, cv2.FONT_HERSHEY_SIMPLEX, font_scale, thickness)
            x = (annotated.shape[1] - text_w) // 2
            y = (annotated.shape[0] + text_h) // 2
        else:
            x, y = 10, text_y
        cv2.putText(annotated, text, (x, y), cv2.FONT_HERSHEY_SIMPLEX, font_scale, color, thickness)

    if circle is None:
        _put_text("no circle", LABEL_COLORS[Judgment.ERROR])
        return annotated

    color = LABEL_COLORS[judgment]
    cv2.circle(annotated, (int(circle.cx), int(circle.cy)), int(circle.r), color, 2)
    cv2.circle(annotated, (int(circle.cx), int(circle.cy)), 3, color, -1)
    _put_text(judgment.value, color)
    return annotated
