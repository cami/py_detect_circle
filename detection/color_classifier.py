"""Classify the color inside a detected circle as OK (white) / NG (orange) / Error."""

from enum import Enum
from typing import NamedTuple, Tuple

import cv2
import numpy as np

import config
from detection.circle_detector import Circle


class Judgment(str, Enum):
    OK = "OK"
    NG = "NG"
    ERROR = "Error"


class ClassificationResult(NamedTuple):
    judgment: Judgment
    mean_hsv: Tuple[float, float, float]


def classify(bgr_frame: np.ndarray, circle: Circle) -> ClassificationResult:
    mask = np.zeros(bgr_frame.shape[:2], dtype=np.uint8)
    inner_radius = max(1, int(circle.r * config.MASK_SHRINK_RATIO))
    cv2.circle(mask, (int(circle.cx), int(circle.cy)), inner_radius, 255, thickness=-1)

    hsv = cv2.cvtColor(bgr_frame, cv2.COLOR_BGR2HSV)
    h, s, v, _ = cv2.mean(hsv, mask=mask)

    # NG is checked first: if the WHITE/ORANGE saturation bands are ever misconfigured
    # to overlap (e.g. while live-tuning in calibration.py), a real defect must not be
    # able to silently pass as OK.
    if config.ORANGE_HUE_MIN <= h <= config.ORANGE_HUE_MAX and s >= config.ORANGE_SAT_MIN:
        judgment = Judgment.NG
    elif s < config.WHITE_SAT_MAX and v > config.WHITE_VAL_MIN:
        judgment = Judgment.OK
    else:
        judgment = Judgment.ERROR

    return ClassificationResult(judgment, (h, s, v))
