import time
from dataclasses import dataclass, field
from typing import Optional, List


@dataclass
class Song:
    title: str
    url: str            # playable audio URL (Jamendo stream URL or /uploads/xxx.mp3)
    source: str          # "jamendo" | "upload"
    added_by: str = ""
    duration: Optional[float] = None  # seconds, if known


@dataclass
class RoomState:
    token: str
    group_id: int
    group_title: str = ""
    queue: List[Song] = field(default_factory=list)
    current_index: int = -1
    is_playing: bool = False
    position: float = 0.0            # seconds into current song
    last_update_ts: float = field(default_factory=time.time)
    volume: int = 100
    loop: bool = False

    @property
    def current_song(self) -> Optional[Song]:
        if 0 <= self.current_index < len(self.queue):
            return self.queue[self.current_index]
        return None

    def elapsed_position(self) -> float:
        """Current playback position, accounting for real time elapsed if playing."""
        if not self.is_playing:
            return self.position
        return self.position + (time.time() - self.last_update_ts)
