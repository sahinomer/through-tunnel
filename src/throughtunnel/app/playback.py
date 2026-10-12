"""Playback clock, independent of any UI framework (unit-testable)."""

from __future__ import annotations

from dataclasses import dataclass

SPEED_OPTIONS = (0.5, 1.0, 2.0, 5.0, 10.0, 20.0)


@dataclass
class PlaybackController:
    duration: float = 0.0
    t: float = 0.0
    playing: bool = False
    speed: float = 1.0

    def load(self, duration: float) -> None:
        """Attach a new trajectory: rewind and stop."""
        self.duration = max(0.0, float(duration))
        self.t = 0.0
        self.playing = False

    @property
    def at_end(self) -> bool:
        return self.duration > 0.0 and self.t >= self.duration

    @property
    def progress(self) -> float:
        return self.t / self.duration if self.duration > 0 else 0.0

    def play(self) -> None:
        if self.duration <= 0.0:
            return
        if self.at_end:
            self.t = 0.0
        self.playing = True

    def pause(self) -> None:
        self.playing = False

    def toggle(self) -> None:
        if self.playing:
            self.pause()
        else:
            self.play()

    def restart(self) -> None:
        self.t = 0.0
        self.play()

    def seek(self, t: float) -> None:
        self.t = min(max(float(t), 0.0), self.duration)

    def advance(self, wall_dt: float) -> bool:
        """Advance by ``wall_dt`` seconds of wall time; returns True if the playback time changed."""
        if not self.playing or wall_dt <= 0.0:
            return False
        self.t = min(self.t + wall_dt * self.speed, self.duration)
        if self.at_end:
            self.playing = False
        return True
