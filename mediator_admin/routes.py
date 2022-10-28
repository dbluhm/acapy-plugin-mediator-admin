"""Endpoints for interacting directly with a mediator.

Useful for modifying keylists directly rather than over DIDComm.
"""

from typing import Sequence

from aiohttp import web
from aiohttp_apispec.decorators import (
    docs,
    match_info_schema,
    request_schema,
    response_schema,
)
from aries_cloudagent.admin.request_context import AdminRequestContext
from aries_cloudagent.messaging.models.openapi import OpenAPISchema
from aries_cloudagent.protocols.coordinate_mediation.v1_0.manager import (
    MediationManager,
)
from aries_cloudagent.protocols.coordinate_mediation.v1_0.messages.inner.keylist_update_rule import (
    KeylistUpdateRule,
    KeylistUpdateRuleSchema,
)
from aries_cloudagent.protocols.coordinate_mediation.v1_0.messages.inner.keylist_updated import (
    KeylistUpdatedSchema,
)
from aries_cloudagent.protocols.coordinate_mediation.v1_0.models.mediation_record import (
    MediationRecord,
)
from aries_cloudagent.protocols.coordinate_mediation.v1_0.routes import (
    MediationIdMatchInfoSchema,
)
from aries_cloudagent.storage.error import StorageNotFoundError
from marshmallow import fields

SPEC_URI = (
    "https://github.com/hyperledger/aries-rfcs/tree/"
    "fa8dc4ea1e667eb07db8f9ffeaf074a4455697c0/features/0211-route-coordination"
)


class RouteInfoSchema(OpenAPISchema):
    """Response to get route info request."""

    routing_keys = fields.List(fields.Str(), required=True)
    endpoint = fields.Str(required=True)


@docs(tags=["mediation"], summary="Get route info for mediator")
@response_schema(RouteInfoSchema(), 200, description="")
async def get_route_info(request: web.Request):
    """Get route info for mediator."""
    context: AdminRequestContext = request["context"]
    manager = MediationManager(context.profile)
    async with context.session() as session:
        routing_did = await manager._retrieve_routing_did(session)
        if not routing_did:
            routing_did = await manager._create_routing_did(session)

    return web.json_response(
        {
            "routing_keys": [routing_did.verkey],
            "endpoint": context.settings.get("default_endpoint"),
        }
    )


class ManualKeylistUpdateSchema(OpenAPISchema):
    """Request schema for manual keylist update."""

    updates = fields.List(fields.Nested(KeylistUpdateRuleSchema()), required=True)


class KeylistUpdateResultSchema(OpenAPISchema):
    """Response schema for manual keylist update."""

    updated = fields.List(
        fields.Nested(KeylistUpdatedSchema()),
        description="List of update results for each update",
    )


@docs(tags=["mediation"], summary="Manually update a keylist held by mediator")
@match_info_schema(MediationIdMatchInfoSchema())
@request_schema(ManualKeylistUpdateSchema())
@response_schema(KeylistUpdateResultSchema(), 200, description="")
async def post_update_keylist(request: web.Request):
    """Manually update keylist for mediation client."""
    body = await request.json()
    context: AdminRequestContext = request["context"]
    manager = MediationManager(context.profile)
    try:
        mediation_id = request.match_info["mediation_id"]
    except KeyError:
        raise web.HTTPBadRequest(reason="mediation_id missing")

    try:
        updates: Sequence[KeylistUpdateRule] = [
            KeylistUpdateRule(**update) for update in body["updates"]
        ]
    except KeyError:
        raise web.HTTPBadRequest(reason="updates missing from request body")

    async with context.session() as session:
        try:
            mediation_record = await MediationRecord.retrieve_by_id(
                session, mediation_id
            )
        except StorageNotFoundError as err:
            raise web.HTTPNotFound(reason=err.roll_up) from err

    result = await manager.update_keylist(mediation_record, updates)
    return web.json_response(
        {"updated": [update.serialize() for update in result.updated]}
    )


async def register(app: web.Application):
    """Register routes."""
    app.add_routes(
        [
            web.get("/mediation/mediator/route-info", get_route_info, allow_head=False),
            web.post(
                "/mediation/mediator/update-keylist/{mediation_id}", post_update_keylist
            ),
        ]
    )


def post_process_routes(app: web.Application):
    """Amend swagger API."""
    # Add top-level tags description
    if "tags" not in app._state["swagger_dict"]:
        app._state["swagger_dict"]["tags"] = []
    app._state["swagger_dict"]["tags"].append(
        {
            "name": "mediation",
            "description": "Mediation management",
            "externalDocs": {"description": "Specification", "url": SPEC_URI},
        }
    )
