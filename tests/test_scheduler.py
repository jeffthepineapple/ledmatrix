import time

import pytest

from ledmatrix.exceptions import DeviceStalled
from ledmatrix.scheduler import FrameScheduler


def test_scheduler_runs_sender_and_tracks_success():
    scheduler = FrameScheduler(fps=1000, stalled_after=1)
    assert scheduler.submit(lambda: "ok") == "ok"
    assert scheduler.last_success is not None
    scheduler.check_watchdog()


def test_scheduler_watchdog():
    scheduler = FrameScheduler(fps=1000, stalled_after=0.001)
    scheduler.submit(lambda: None)
    time.sleep(0.003)
    with pytest.raises(DeviceStalled):
        scheduler.check_watchdog()
