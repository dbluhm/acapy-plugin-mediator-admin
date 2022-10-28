"""Test out the mediator admin functionality."""

import asyncio
import json
from os import getenv
from controller.controller import Controller
from controller.models import InvitationResult
from controller.protocols import connection, request_mediation_v1


async def main():
    """Test mediator admin functionality."""
    alice_url = getenv("ALICE")
    if not alice_url:
        raise ValueError("ALICE env var not set")

    mediator_url = getenv("MEDIATOR")
    if not mediator_url:
        raise ValueError("MEDIATOR env var not set")

    alice = Controller(alice_url)
    mediator = Controller(mediator_url)
    async with alice, mediator:
        alice_conn, mediator_conn = await connection(alice, mediator)
        med_med, alice_med = await request_mediation_v1(
            mediator, alice, mediator_conn.connection_id, alice_conn.connection_id
        )

        invitation = await alice.post(
            "/connections/create-invitation",
            json={"mediation_id": alice_med.mediation_id},
            response=InvitationResult,
        )
        assert invitation.invitation.recipient_keys
        result = await mediator.post(
            f"/mediation/mediator/update-keylist/{med_med.mediation_id}",
            json={
                "updates": [
                    {
                        "recipient_key": invitation.invitation.recipient_keys[0].__root__,
                        "action": "add"
                    }
                ]
            }
        )
        print(json.dumps(result, indent=2, sort_keys=True))


if __name__ == "__main__":
    asyncio.run(main())
