"""State machine that fires a single judgment per object crossing the judge zone."""

from enum import Enum, auto
from typing import Optional

import config
from detection.circle_detector import Circle


class _State(Enum):
    WAITING = auto()
    COOLDOWN = auto()


class TriggerStateMachine:
    def __init__(self, frame_width: int):
        self._zone_x_min = frame_width * config.JUDGE_ZONE_X_MIN_RATIO
        self._zone_x_max = frame_width * config.JUDGE_ZONE_X_MAX_RATIO
        self._state = _State.WAITING
        self._present_count = 0
        self._absent_count = 0

    def step(self, circle: Optional[Circle]) -> bool:
        """Feed one frame's detection result. Returns True on the frame judgment should run."""
        in_zone = circle is not None and self._zone_x_min <= circle.cx <= self._zone_x_max

        if self._state == _State.WAITING:
            self._present_count = self._present_count + 1 if in_zone else 0
            if self._present_count >= config.TRIGGER_CONFIRM_FRAMES:
                self._present_count = 0
                self._absent_count = 0
                self._state = _State.COOLDOWN
                return True
            return False

        # COOLDOWN: wait for the object to fully leave the frame before rearming.
        self._absent_count = self._absent_count + 1 if circle is None else 0
        if self._absent_count >= config.EXIT_CONFIRM_FRAMES:
            self._absent_count = 0
            self._state = _State.WAITING
        return False
