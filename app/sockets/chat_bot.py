from flask_socketio import emit, join_room
from flask import request
import uuid
import datetime
from ..utils import GeminiAI


def register_chat_bot_socketio_events(socketio):
    NAMESPACE = "/chat-bot"
    api_gemini = GeminiAI()
    DEFAULT_ROOM = None  # kita tak pakai 'global' lagi sebagai default

    _HISTORY = []
    _HISTORY_CAP = 2000
    _ROOM_HAS_SYSTEM = set()

    def _now_iso():
        return (
            datetime.datetime.now(datetime.timezone.utc)
            .isoformat()
            .replace("+00:00", "Z")
        )

    def _append(room: str, role: str, text: str):
        if role == "system":
            return
        _HISTORY.append({"room": room, "role": role, "text": text, "ts": _now_iso()})
        if len(_HISTORY) > _HISTORY_CAP:
            del _HISTORY[: len(_HISTORY) - _HISTORY_CAP]

    def _history_for_room(room: str, limit: int = 200):
        items = [m for m in _HISTORY if m["room"] == room and m.get("role") != "system"]
        return items[-limit:]

    def _ensure_room(room: str) -> str:
        """Return given room or create a new one when falsy/invalid."""
        r = (room or "").strip()
        if not r:
            r = f"room-{uuid.uuid4().hex}"
        return r

    @socketio.on("connect", namespace=NAMESPACE)
    def handle_connect():
        sid = request.sid

        # coba ambil room dari query atau auth (opsional, sesuai client)
        room = request.args.get("room") or (request.args.get("room_id"))
        room = _ensure_room(room)

        # join (idempotent)
        join_room(room, sid=sid, namespace=NAMESPACE)

        print(
            f"[connect] ns={NAMESPACE} sid={sid} room={room} ip={request.remote_addr}"
        )

        # beritahu klien room mana yang dipakai (kalau klien belum punya)
        emit(
            "room_created",
            {"room": room, "ts": _now_iso()},
            to=sid,
            namespace=NAMESPACE,
        )

        history = _history_for_room(room)
        if history:
            emit(
                "chat",
                {"type": "history", "items": history, "ts": _now_iso()},
                to=sid,
                namespace=NAMESPACE,
            )
            _ROOM_HAS_SYSTEM.discard(room)
        else:
            system_msg = {
                "type": "system",
                "text": "Belum ada pesan. Mulai ngobrol di bawah ✨",
                "ts": _now_iso(),
            }
            emit("chat", system_msg, to=sid, namespace=NAMESPACE)
            _ROOM_HAS_SYSTEM.add(room)

    @socketio.on("disconnect", namespace=NAMESPACE)
    def handle_disconnect():
        sid = request.sid
        print(f"[disconnect] ns={NAMESPACE} sid={sid} ip={request.remote_addr}")

    @socketio.on("chat", namespace=NAMESPACE)
    def handle_chat(data):
        sid = request.sid
        # kalau klien tidak kirim room, kita buat baru dan join
        room = _ensure_room((data or {}).get("room"))
        text = (data or {}).get("text", "").strip()

        # pastikan sender sudah join room (aman dipanggil berkali-kali)
        join_room(room, sid=sid, namespace=NAMESPACE)

        if room in _ROOM_HAS_SYSTEM:
            emit(
                "chat",
                {"type": "system_clear", "ts": _now_iso()},
                to=room,
                namespace=NAMESPACE,
            )
            _ROOM_HAS_SYSTEM.discard(room)

        user_msg = {"type": "user", "text": text, "ts": _now_iso(), "room": room}
        emit("chat", user_msg, to=room, namespace=NAMESPACE)
        _append(room, "user", text)

        bot_response = api_gemini.generate_sync(text)

        assistant_msg = {
            "type": "assistant",
            "text": bot_response,
            "ts": _now_iso(),
            "room": room,
        }
        emit("chat", assistant_msg, to=room, namespace=NAMESPACE)
        _append(room, "assistant", bot_response)
