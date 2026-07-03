"""Locate a circular object in a frame via contour circularity (not Hough transform)."""

import math
from typing import NamedTuple, Optional

import cv2
import numpy as np

import config


class Circle(NamedTuple):
    cx: float
    cy: float
    r: float


def find_circle(bgr_frame: np.ndarray) -> Optional[Circle]:
    gray = cv2.cvtColor(bgr_frame, cv2.COLOR_BGR2GRAY)
    blurred = cv2.GaussianBlur(gray, config.GAUSSIAN_BLUR_KSIZE, 0)
    _, binary = cv2.threshold(blurred, 0, 255, cv2.THRESH_BINARY + cv2.THRESH_OTSU)

    min_diameter = bgr_frame.shape[0] * config.MIN_CIRCLE_DIAMETER_RATIO

    best_circle: Optional[Circle] = None
    best_area = 0.0

    # The object may be lighter or darker than its background (e.g. OK/NG parts of
    # different colors on the same belt), so check both thresholding polarities.
    for mask in (binary, cv2.bitwise_not(binary)):
        contours, _ = cv2.findContours(mask, cv2.RETR_EXTERNAL, cv2.CHAIN_APPROX_SIMPLE)
        for contour in contours:
            area = cv2.contourArea(contour)
            if not (config.MIN_CONTOUR_AREA <= area <= config.MAX_CONTOUR_AREA):
                continue
            perimeter = cv2.arcLength(contour, True)
            if perimeter == 0:
                continue
            circularity = 4 * math.pi * area / (perimeter ** 2)
            # Among everything that looks round enough, prefer the largest one
            # (e.g. concentric circles: pick the outer ring, not the inner disk).
            if circularity < config.CIRCULARITY_THRESHOLD or area <= best_area:
                continue
            (cx, cy), r = cv2.minEnclosingCircle(contour)
            if 2 * r < min_diameter:
                continue
            best_circle = Circle(cx, cy, r)
            best_area = area

    return best_circle
