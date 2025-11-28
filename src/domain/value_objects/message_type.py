# src/domain/value_objects/message_type.py

from enum import Enum
from typing import Dict

class MessageType(str, Enum):
    TEXT = "text"
    IMAGE = "image"
    VIDEO = "video"
    AUDIO = "audio"
    DOCUMENT = "document"
    STICKER = "sticker"
    LOCATION = "location"
    CONTACT = "contact"
    PTT = "ptt"
    REACTION = "reaction"  # 🔥 NUEVO
    UNKNOWN = "unknown"

TYPE_MAPPINGS: Dict[str, MessageType] = {
    'ptt': MessageType.AUDIO,
    'voiceMessage': MessageType.AUDIO,
    'audioMessage': MessageType.AUDIO,
    'imageMessage': MessageType.IMAGE,
    'videoMessage': MessageType.VIDEO,
    'documentMessage': MessageType.DOCUMENT,
    'documentWithCaptionMessage': MessageType.DOCUMENT,
    'stickerMessage': MessageType.STICKER,
    'locationMessage': MessageType.LOCATION,
    'contactMessage': MessageType.CONTACT,
    'reactionMessage': MessageType.REACTION,  # 🔥 NUEVO
    'reaction': MessageType.REACTION,  # 🔥 NUEVO (por Info.Type)
    'url': MessageType.TEXT,
}