"""Tunable constants for capture, detection, color classification and triggering."""

# --- Camera capture ---
CAMERA_DEVICE_INDEX = 0
CAPTURE_WIDTH = 640
CAPTURE_HEIGHT = 480
# Caps exposure time (reduces motion blur on fast-moving objects) by forcing a
# minimum frame rate; auto-exposure compensates for less light via gain instead.
MAX_FRAME_DURATION_US = 20_000  # ~50 fps floor, i.e. exposure capped at ~20 ms

# --- Display (physical screen may differ from capture resolution) ---
DISPLAY_WIDTH = 480
DISPLAY_HEIGHT = 320

# --- Circle detection (grayscale -> blur -> Otsu threshold -> contours) ---
GAUSSIAN_BLUR_KSIZE = (9, 9)
# Lowered from 0.8: a moving object's contour is often slightly skewed/blurred
# (rolling shutter, motion blur), which drops a true circle's score below 0.8.
CIRCULARITY_THRESHOLD = 0.65
MIN_CONTOUR_AREA = 500
MAX_CONTOUR_AREA = 200_000
# Discard circles smaller than this fraction of the frame height (rejects small
# spurious detections, e.g. finger joints, in favor of the actual target object).
MIN_CIRCLE_DIAMETER_RATIO = 0.5

# --- Color classification (HSV, OpenCV ranges: H 0-179, S/V 0-255) ---
MASK_SHRINK_RATIO = 0.8

# Kept below ORANGE_SAT_MIN so a widened white band can never overlap the NG check
# (NG is evaluated first in classify() regardless).
WHITE_SAT_MAX = 90
WHITE_VAL_MIN = 120

ORANGE_HUE_MIN = 5
# Real orange parts drift up to ~H29 under lighting seen so far (looks yellowish) but
# stay highly saturated (S>240); widened further to H45 (~90 deg, well past pure
# yellow at H30) as headroom for stronger lighting shifting it further. White (OK)
# is judged purely on saturation/value, so this doesn't risk misclassifying it.
ORANGE_HUE_MAX = 45
ORANGE_SAT_MIN = 100

# --- Trigger state machine (belt conveyor, single object at a time) ---
# Judge zone: fraction of frame width, centered, where a circle must be to trigger judgment.
# Widened from 0.4-0.6: a moving object only has TRIGGER_CONFIRM_FRAMES frames' worth of
# dwell time inside this zone to trigger, so a narrow zone missed fast-moving objects.
JUDGE_ZONE_X_MIN_RATIO = 0.15
JUDGE_ZONE_X_MAX_RATIO = 0.85

TRIGGER_CONFIRM_FRAMES = 2
EXIT_CONFIRM_FRAMES = 3

# --- Output ---
OUTPUT_DIR = "output"

# --- Preview display ---
LIVE_PREVIEW_FPS = 10  # screen refresh rate while no object is being judged
JUDGMENT_HOLD_SECONDS = 1.0  # how long the judged frame stays on screen
