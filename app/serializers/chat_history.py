from ..models import ChatHistoryModel
from .interfaces import SerializerInterface


class ChatHistorySerializer(SerializerInterface):
    def serialize(
        self,
        user: ChatHistoryModel,
        id_is_null: bool = False,
        original_message_is_null: bool = False,
        response_message_is_null: bool = False,
        links_is_null: bool = False,
        is_image_is_null: bool = False,
        created_at_is_null: bool = False,
        updated_at_is_null: bool = False,
        deleted_at_is_null: bool = False,
    ) -> dict:
        data = {}
        if not id_is_null:
            data["id"] = str(user.id) if user.id else None
        if not original_message_is_null:
            data["original_message"] = user.original_message
        if not response_message_is_null:
            data["response_message"] = user.response_message
        if not is_image_is_null:
            data["is_image"] = user.is_image
        if not links_is_null:
            data["links"] = user.links
        if not created_at_is_null:
            data["created_at"] = (
                None if not user.created_at else user.created_at.isoformat()
            )
        if not updated_at_is_null:
            data["updated_at"] = (
                None if not user.updated_at else user.updated_at.isoformat()
            )
        if not deleted_at_is_null:
            data["deleted_at"] = (
                None if not user.deleted_at else user.deleted_at.isoformat()
            )
        return data
