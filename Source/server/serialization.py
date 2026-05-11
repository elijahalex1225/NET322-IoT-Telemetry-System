"""Content negotiation for the REST API.

Maps the `Accept` header on a request to a serializer for the response.
Supported media types:
    application/json
    application/xml
    application/yaml   (also accepts text/yaml)

Falls back to JSON when no supported type matches.
"""
from __future__ import annotations

import json
import yaml
import xml.etree.ElementTree as ET

from aiohttp import web


SUPPORTED_TYPES = {
    "application/json",
    "application/xml",
    "application/yaml",
    "text/yaml",
}


def negotiate(request: web.Request) -> str:
    """Return the chosen response media type for `request`."""

    accept = request.headers.get("Accept", "application/json")

    # Split Accept header values
    media_types = [m.strip() for m in accept.split(",")]

    for media_type in media_types:

        # Remove quality values like ;q=0.8
        media_type = media_type.split(";")[0].strip()

        if media_type in SUPPORTED_TYPES:

            # Normalize text/yaml
            if media_type == "text/yaml":
                return "application/yaml"

            return media_type

    # Default fallback
    return "application/json"


def dict_to_xml(tag, data):
    """Convert dictionary to XML element."""

    elem = ET.Element(tag)

    if isinstance(data, dict):
        for key, value in data.items():
            child = dict_to_xml(key, value)
            elem.append(child)

    elif isinstance(data, list):
        for item in data:
            child = dict_to_xml("item", item)
            elem.append(child)

    else:
        elem.text = str(data)

    return elem


def serialize(payload, media_type: str) -> bytes:
    """Serialize payload into bytes."""

    if media_type == "application/json":
        return json.dumps(payload, indent=2).encode("utf-8")

    elif media_type == "application/xml":

        root = dict_to_xml("response", payload)

        return ET.tostring(
            root,
            encoding="utf-8",
            xml_declaration=True
        )

    elif media_type == "application/yaml":
        return yaml.dump(payload).encode("utf-8")

    else:
        raise ValueError(f"Unsupported media type: {media_type}")
