import uuid
import json
import xml.etree.ElementTree as ET

import yaml
from aiohttp import web
import aiohttp_cors


SUPPORTED_TYPES = {
    "application/json",
    "application/xml",
    "application/yaml",
    "text/yaml",
}


def negotiate(request: web.Request) -> str:
    """Return best response media type."""

    accept = request.headers.get(
        "Accept",
        "application/json",
    )

    for media_type in accept.split(","):

        media_type = media_type.strip().split(";")[0]

        if media_type in SUPPORTED_TYPES:

            if media_type == "text/yaml":
                return "application/yaml"

            return media_type

    return "application/json"


def to_xml(payload) -> bytes:
    """Convert payload to XML."""

    root = ET.Element("response")

    if isinstance(payload, list):

        for item in payload:

            entry = ET.SubElement(root, "item")

            for key, value in item.items():

                child = ET.SubElement(entry, key)

                child.text = str(value)

    elif isinstance(payload, dict):

        for key, value in payload.items():

            child = ET.SubElement(root, key)

            child.text = str(value)

    return ET.tostring(root)


def serialize(payload, media_type: str) -> bytes:
    """Serialize payload."""

    if media_type == "application/json":
        return json.dumps(payload).encode()

    if media_type == "application/xml":
        return to_xml(payload)

    if media_type == "application/yaml":
        return yaml.dump(payload).encode()

    return json.dumps(payload).encode()


async def list_sensors(request: web.Request) -> web.Response:
    """GET /sensors"""

    storage = request.app["storage"]

    payload = await storage.list_sensors()

    media_type = negotiate(request)

    body = serialize(payload, media_type)

    return web.Response(
        body=body,
        content_type=media_type,
    )


async def get_readings(request: web.Request) -> web.Response:
    """GET /sensors/{id}/readings"""

    sensor_id = request.match_info["id"]

    storage = request.app["storage"]

    readings = await storage.get_readings(sensor_id)

    payload = {
        "sensor_id": sensor_id,
        "readings": list(readings),
    }

    media_type = negotiate(request)

    body = serialize(payload, media_type)

    return web.Response(
        body=body,
        content_type=media_type,
    )


async def register_sensor(request: web.Request) -> web.Response:
    """POST /sensors"""

    payload = await request.json()

    storage = request.app["storage"]

    await storage.add_sensor(payload)

    return web.json_response(
        payload,
        status=201,
    )


async def delete_sensor(request: web.Request) -> web.Response:
    """DELETE /sensors/{id}"""

    sensor_id = request.match_info["id"]

    storage = request.app["storage"]

    await storage.remove_sensor(sensor_id)

    return web.json_response(
        {
            "message": "sensor deleted successfully"
        }
    )


@web.middleware
async def session_cookie_middleware(request, handler):

    session_id = request.cookies.get("session_id")

    if not session_id:
        session_id = str(uuid.uuid4())

    request["session_id"] = session_id

    response = await handler(request)

    response.set_cookie(
        "session_id",
        session_id,
        httponly=True,
    )

    return response


def build_app(storage) -> web.Application:

    app = web.Application(
        middlewares=[
            session_cookie_middleware
        ]
    )

    app.router.add_get(
        "/sensors",
        list_sensors,
    )

    app.router.add_get(
        "/sensors/{id}/readings",
        get_readings,
    )

    app.router.add_post(
        "/sensors",
        register_sensor,
    )

    app.router.add_delete(
        "/sensors/{id}",
        delete_sensor,
    )

    app["storage"] = storage

    # Enable CORS
    cors = aiohttp_cors.setup(app)

    for route in list(app.router.routes()):

        cors.add(
            route,
            {
                "*": aiohttp_cors.ResourceOptions(
                    allow_credentials=True,
                    expose_headers="*",
                    allow_headers="*",
                )
            },
        )

    return app