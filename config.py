"""Tunable constants for capture, detection, color classification and triggering."""

# --- Camera capture ---
CAMERA_DEVICE_INDEX = 0
CAPTURE_WIDTH = 640
CAPTURE_HEIGHT = 480

# --- Display (physical screen may differ from capture resolution) ---
DISPLAY_WIDTH = 480
DISPLAY_HEIGHT = 320

# --- Circle detection (grayscale -> blur -> Otsu threshold -> contours) ---
GAUSSIAN_BLUR_KSIZE = (9, 9)
CIRCULARITY_THRESHOLD = 0.8
MIN_CONTOUR_AREA = 500
MAX_CONTOUR_AREA = 200_000

# --- Color classification (HSV, OpenCV ranges: H 0-179, S/V 0-255) ---
MASK_SHRINK_RATIO = 0.8

WHITE_SAT_MAX = 60
WHITE_VAL_MIN = 150

ORANGE_HUE_MIN = 5
ORANGE_HUE_MAX = 25
ORANGE_SAT_MIN = 100

# --- Trigger state machine (belt conveyor, single object at a time) ---
# Judge zone: fraction of frame width, centered, where a circle must be to trigger judgment.
JUDGE_ZONE_X_MIN_RATIO = 0.4
JUDGE_ZONE_X_MAX_RATIO = 0.6

TRIGGER_CONFIRM_FRAMES = 3
EXIT_CONFIRM_FRAMES = 3

# --- Output ---
OUTPUT_DIR = "output"
