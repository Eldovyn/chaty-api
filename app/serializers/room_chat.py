from ..models import ChatRoomModel
from .interfaces import SerializerInterface
import datetime as dt


def _iso_or_none(value):
    return value.isoformat() if isinstance(value, dt.datetime) else None


class RoomChatSerializer(SerializerInterface):
    def serialize(
        self,
        user: ChatRoomModel,
        id_is_null: bool = False,
        title_is_null: bool = False,
        room_is_null: bool = False,
        created_at_is_null: bool = False,
        updated_at_is_null: bool = False,
        deleted_at_is_null: bool = False,
    ) -> dict:
        data = {}
        if not id_is_null:
            data["id"] = str(user.id) if user.id else None
        if not title_is_null:
            data["title"] = user.title
        if not room_is_null:
            data["room"] = user.room
        if not created_at_is_null:
            data["created_at"] = _iso_or_none(getattr(user, "created_at", None))
        if not updated_at_is_null:
            data["updated_at"] = _iso_or_none(getattr(user, "updated_at", None))
        if not deleted_at_is_null:
            data["deleted_at"] = _iso_or_none(getattr(user, "deleted_at", None))
        return data
