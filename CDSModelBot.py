from __future__ import annotations

from typing import AsyncIterable

from fastapi_poe import PoeBot
from fastapi_poe.client import MetaMessage, stream_request
from fastapi_poe.types import (
    ProtocolMessage,
    QueryRequest,
    SettingsRequest,
    SettingsResponse,
)
from sse_starlette.sse import ServerSentEvent

BOT = "claude-instant"


def get_cds_model_prompt(description: str):
    return f"""
You are a CDS model generator for SAP CAP projects. Based on the provided description, generate the corresponding CDS model like on this repository https://cap.cloud.sap/docs/cds/cdl
Description: {description}
"""


def _get_description_message(query: QueryRequest):
    for message in reversed(query.query):
        if message.role == "user":
            return message


def _get_relevant_subchat(query: QueryRequest) -> list[ProtocolMessage]:
    subchat = []
    for message in reversed(query.query):
        subchat.append(message)
        if message.role == "user":
            return list(reversed(subchat))
    return []


class CDSModelBot(PoeBot):
    async def get_response(self, query: QueryRequest) -> AsyncIterable[ServerSentEvent]:
        relevant_subchat = _get_relevant_subchat(query)
        if not relevant_subchat:
            yield self.text_event(
                "Please provide a description of the CDS model you would like me to generate."
            )
            return

        description_message = relevant_subchat[0]
        description = description_message.content

        cds_model_prompt = get_cds_model_prompt(description)
        description_message.content = cds_model_prompt

        query.query = relevant_subchat
        async for msg in stream_request(query, BOT, query.access_key):
            if isinstance(msg, MetaMessage):
                continue
            elif msg.is_suggested_reply:
                yield self.suggested_reply_event(msg.text)
            elif msg.is_replace_response:
                yield self.replace_response_event(msg.text)
            else:
                yield self.text_event(msg.text)

    async def get_settings(self, settings: SettingsRequest) -> SettingsResponse:
        return SettingsResponse(
            introduction_message=(
                "Hi, I am the CDS Model Generator Bot. Provide me with a description of the CDS model you need for your SAP CAP project, and I will generate the corresponding CDS model in Java for you."
            ),
            server_bot_dependencies={BOT: 1},
        )

