import secrets
import time
from typing import Dict, Optional

from .models import RoomState, Song


class RoomStore:
    """
    Keeps one room per Telegram group in memory.
    NOTE: this is in-memory only -> state resets if the process restarts.
    Good enough to start; swap for a DB/Redis later if you need persistence.
    """

    def __init__(self):
        self._rooms_by_group: Dict[int, RoomState] = {}
        self._rooms_by_token: Dict[str, RoomState] = {}

    def get_by_group(self, group_id: int) -> Optional[RoomState]:
        return self._rooms_by_group.get(group_id)

    def get_by_token(self, token: str) -> Optional[RoomState]:
        return self._rooms_by_token.get(token)

    def get_or_create(self, group_id: int, group_title: str = "") -> RoomState:
        room = self._rooms_by_group.get(group_id)
        if room:
            return room
        token = secrets.token_urlsafe(8)
        room = RoomState(token=token, group_id=group_id, group_title=group_title)
        self._rooms_by_group[group_id] = room
        self._rooms_by_token[token] = room
        return room

    def add_song(self, group_id: int, song: Song) -> RoomState:
        room = self.get_or_create(group_id)
        room.queue.append(song)
        if room.current_index == -1:
            room.current_index = 0
            room.is_playing = True
            room.position = 0.0
            room.last_update_ts = time.time()
        return room

    def _snapshot_position(self, room: RoomState):
        room.position = room.elapsed_position()
        room.last_update_ts = time.time()

    def pause(self, room: RoomState):
        if room.is_playing:
            self._snapshot_position(room)
            room.is_playing = False

    def resume(self, room: RoomState):
        if not room.is_playing and room.current_song:
            room.is_playing = True
            room.last_update_ts = time.time()

    def skip(self, room: RoomState) -> Optional[Song]:
        if not room.queue:
            return None
        if room.current_index + 1 < len(room.queue):
            room.current_index += 1
        elif room.loop:
            room.current_index = 0
        else:
            room.is_playing = False
            room.current_index = len(room.queue)  # past the end == nothing playing
            return None
        room.position = 0.0
        room.last_update_ts = time.time()
        room.is_playing = True
        return room.current_song

    def stop(self, room: RoomState):
        room.queue.clear()
        room.current_index = -1
        room.is_playing = False
        room.position = 0.0

    def remove(self, room: RoomState, index: int) -> bool:
        if 0 <= index < len(room.queue):
            room.queue.pop(index)
            if index < room.current_index:
                room.current_index -= 1
            elif index == room.current_index:
                room.position = 0.0
                room.last_update_ts = time.time()
            return True
        return False

    def set_volume(self, room: RoomState, volume: int):
        room.volume = max(0, min(100, volume))

    def toggle_loop(self, room: RoomState) -> bool:
        room.loop = not room.loop
        return room.loop

    def state_dict(self, room: RoomState) -> dict:
        return {
            "token": room.token,
            "group_title": room.group_title,
            "is_playing": room.is_playing,
            "position": room.elapsed_position(),
            "volume": room.volume,
            "loop": room.loop,
            "current_index": room.current_index,
            "queue": [
                {"title": s.title, "url": s.url, "source": s.source, "added_by": s.added_by}
                for s in room.queue
            ],
        }


store = RoomStore()
