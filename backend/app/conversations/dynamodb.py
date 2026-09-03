import asyncio
import json
import time
from datetime import UTC, datetime
from decimal import Decimal
from math import isfinite
from typing import Any
from uuid import UUID, uuid4

import boto3
from agents import SessionSettings
from boto3.dynamodb.conditions import Key
from botocore.exceptions import BotoCoreError, ClientError

from app.conversations.errors import ConversationStoreError
from app.schemas.chart import ChartArtifact
from app.schemas.conversation import ConversationDetail, ConversationMessage, ConversationSummary
from app.schemas.source import WebSource


class DynamoDBConversationStore:
    """Stores chat history and agent session items in a single DynamoDB table."""

    _CONVERSATION_INDEX_PREFIX = "CLIENT"

    def __init__(self, table_name: str, table: Any | None = None) -> None:
        self.table = table or boto3.resource("dynamodb").Table(table_name)

    def save_exchange(
        self,
        client_id: UUID,
        conversation_id: UUID,
        user_message: str,
        answer: str,
        tools_used: list[str],
        charts: list[ChartArtifact],
        sources: list[WebSource],
    ) -> None:
        now = _utc_now()
        conversation_key = _conversation_key(conversation_id)
        try:
            self.table.update_item(
                Key={"pk": conversation_key, "sk": "METADATA"},
                UpdateExpression=(
                    "SET title = if_not_exists(title, :title), "
                    "created_at = if_not_exists(created_at, :created_at), "
                    "updated_at = :updated_at, client_id = :client_id, "
                    "gsi1pk = :gsi1pk, gsi1sk = :gsi1sk"
                ),
                ExpressionAttributeValues={
                    ":title": _make_title(user_message),
                    ":created_at": now,
                    ":updated_at": now,
                    ":client_id": str(client_id),
                    ":gsi1pk": self._conversation_index_key(client_id),
                    ":gsi1sk": f"{now}#{conversation_id}",
                },
            )
            self._put_display_message(
                conversation_key=conversation_key,
                role="user",
                content=user_message,
                tools=[],
                charts=[],
                sources=[],
                created_at=now,
                position=0,
            )
            self._put_display_message(
                conversation_key=conversation_key,
                role="assistant",
                content=answer,
                tools=tools_used,
                charts=[chart.model_dump() for chart in charts],
                sources=[source.model_dump() for source in sources],
                created_at=now,
                position=1,
            )
        except (BotoCoreError, ClientError) as error:
            raise ConversationStoreError("Nao foi possivel salvar a conversa.") from error

    def list_conversations(self, client_id: UUID, limit: int = 50) -> list[ConversationSummary]:
        try:
            response = self.table.query(
                IndexName="conversations_by_updated_at",
                KeyConditionExpression=Key("gsi1pk").eq(self._conversation_index_key(client_id)),
                ScanIndexForward=False,
                Limit=limit,
            )
        except (BotoCoreError, ClientError) as error:
            raise ConversationStoreError("Nao foi possivel listar as conversas.") from error

        try:
            return [self._to_summary(item) for item in response.get("Items", [])]
        except (KeyError, TypeError, ValueError) as error:
            raise ConversationStoreError("A conversa armazenada esta invalida.") from error

    def get_conversation(self, client_id: UUID, conversation_id: UUID) -> ConversationDetail | None:
        conversation_key = _conversation_key(conversation_id)
        try:
            metadata_response = self.table.get_item(
                Key={"pk": conversation_key, "sk": "METADATA"}
            )
            metadata = metadata_response.get("Item")
            if metadata is None or metadata.get("client_id") != str(client_id):
                return None
            messages = self._query_partition(conversation_key, "DISPLAY#")
        except (BotoCoreError, ClientError) as error:
            raise ConversationStoreError("Nao foi possivel abrir a conversa.") from error

        try:
            return ConversationDetail(
                **self._to_summary(metadata).model_dump(),
                messages=[
                    ConversationMessage(
                        id=message["message_id"],
                        role=message["role"],
                        content=message["content"],
                        tools=message.get("tools", []),
                        charts=[
                            ChartArtifact.model_validate(_from_dynamodb_value(chart))
                            for chart in message.get("charts", [])
                        ],
                        sources=[WebSource.model_validate(source) for source in message.get("sources", [])],
                        created_at=message["created_at"],
                    )
                    for message in messages
                ],
            )
        except (KeyError, TypeError, ValueError) as error:
            raise ConversationStoreError("A conversa armazenada esta invalida.") from error

    def delete_conversation(self, client_id: UUID, conversation_id: UUID) -> bool:
        conversation_key = _conversation_key(conversation_id)
        try:
            metadata_response = self.table.get_item(
                Key={"pk": conversation_key, "sk": "METADATA"}
            )
            metadata = metadata_response.get("Item")
            if metadata is None or metadata.get("client_id") != str(client_id):
                return False
            for item in self._query_partition(conversation_key):
                self.table.delete_item(Key={"pk": item["pk"], "sk": item["sk"]})
        except (BotoCoreError, ClientError) as error:
            raise ConversationStoreError("Nao foi possivel excluir a conversa.") from error
        return True

    def _put_display_message(
        self,
        *,
        conversation_key: str,
        role: str,
        content: str,
        tools: list[str],
        charts: list[dict[str, Any]],
        sources: list[dict[str, Any]],
        created_at: str,
        position: int,
    ) -> None:
        order = f"{time.time_ns():020d}-{position:02d}"
        self.table.put_item(
            Item=_to_dynamodb_value(
                {
                    "pk": conversation_key,
                    "sk": f"DISPLAY#{order}#{uuid4().hex}",
                    "message_id": str(uuid4()),
                    "role": role,
                    "content": content,
                    "tools": tools,
                    "charts": charts,
                    "sources": sources,
                    "created_at": created_at,
                }
            )
        )

    def _query_partition(self, partition_key: str, prefix: str | None = None) -> list[dict[str, Any]]:
        key_condition = Key("pk").eq(partition_key)
        if prefix is not None:
            key_condition = key_condition & Key("sk").begins_with(prefix)

        items: list[dict[str, Any]] = []
        query_args: dict[str, Any] = {
            "KeyConditionExpression": key_condition,
            "ScanIndexForward": True,
        }
        while True:
            response = self.table.query(**query_args)
            items.extend(response.get("Items", []))
            last_key = response.get("LastEvaluatedKey")
            if last_key is None:
                return items
            query_args["ExclusiveStartKey"] = last_key

    @staticmethod
    def _to_summary(item: dict[str, Any]) -> ConversationSummary:
        return ConversationSummary(
            conversation_id=UUID(item["pk"].removeprefix("CONVERSATION#")),
            title=item["title"],
            created_at=item["created_at"],
            updated_at=item["updated_at"],
        )

    @classmethod
    def _conversation_index_key(cls, client_id: UUID) -> str:
        return f"{cls._CONVERSATION_INDEX_PREFIX}#{client_id}"


def _to_dynamodb_value(value: Any) -> Any:
    """Converts values that DynamoDB cannot serialize in nested chart payloads."""
    if isinstance(value, float):
        return Decimal(str(value)) if isfinite(value) else None
    if isinstance(value, dict):
        return {key: _to_dynamodb_value(item) for key, item in value.items()}
    if isinstance(value, list):
        return [_to_dynamodb_value(item) for item in value]
    if isinstance(value, tuple):
        return [_to_dynamodb_value(item) for item in value]
    return value


def _from_dynamodb_value(value: Any) -> Any:
    """Restores decimal chart values to JSON-friendly numbers for the API response."""
    if isinstance(value, Decimal):
        return float(value)
    if isinstance(value, dict):
        return {key: _from_dynamodb_value(item) for key, item in value.items()}
    if isinstance(value, list):
        return [_from_dynamodb_value(item) for item in value]
    return value


class DynamoDBSession:
    """OpenAI Agents SDK session backed by DynamoDB."""

    def __init__(
        self,
        session_id: str,
        table_name: str,
        history_limit: int,
        table: Any | None = None,
    ) -> None:
        self.session_id = session_id
        self.session_settings = SessionSettings(limit=history_limit)
        self.table = table or boto3.resource("dynamodb").Table(table_name)
        self._partition_key = f"SESSION#{session_id}"

    async def get_items(self, limit: int | None = None) -> list[dict[str, Any]]:
        effective_limit = limit if limit is not None else self.session_settings.limit
        return await asyncio.to_thread(self._get_items, effective_limit)

    async def add_items(self, items: list[dict[str, Any]]) -> None:
        if items:
            await asyncio.to_thread(self._add_items, items)

    async def pop_item(self) -> dict[str, Any] | None:
        return await asyncio.to_thread(self._pop_item)

    async def clear_session(self) -> None:
        await asyncio.to_thread(self._clear_session)

    def close(self) -> None:
        """Keeps the same lifecycle interface as SQLiteSession."""

    def _get_items(self, limit: int | None) -> list[dict[str, Any]]:
        query_args: dict[str, Any] = {
            "KeyConditionExpression": Key("pk").eq(self._partition_key)
            & Key("sk").begins_with("SESSION#"),
            "ScanIndexForward": False,
        }
        if limit is not None and limit > 0:
            query_args["Limit"] = limit
        try:
            response = self.table.query(**query_args)
        except (BotoCoreError, ClientError) as error:
            raise ConversationStoreError("Nao foi possivel recuperar o historico da conversa.") from error

        decoded: list[dict[str, Any]] = []
        for item in reversed(response.get("Items", [])):
            try:
                decoded.append(json.loads(item["message_data"]))
            except (KeyError, TypeError, json.JSONDecodeError):
                continue
        return decoded

    def _add_items(self, items: list[dict[str, Any]]) -> None:
        try:
            for position, item in enumerate(items):
                self.table.put_item(
                    Item={
                        "pk": self._partition_key,
                        "sk": f"SESSION#{time.time_ns():020d}-{position:03d}#{uuid4().hex}",
                        "message_data": json.dumps(item),
                        "created_at": _utc_now(),
                    }
                )
        except (BotoCoreError, ClientError) as error:
            raise ConversationStoreError("Nao foi possivel salvar o historico da conversa.") from error

    def _pop_item(self) -> dict[str, Any] | None:
        try:
            response = self.table.query(
                KeyConditionExpression=Key("pk").eq(self._partition_key)
                & Key("sk").begins_with("SESSION#"),
                ScanIndexForward=False,
                Limit=1,
            )
            items = response.get("Items", [])
            if not items:
                return None
            item = items[0]
            self.table.delete_item(Key={"pk": item["pk"], "sk": item["sk"]})
            return json.loads(item["message_data"])
        except (BotoCoreError, ClientError) as error:
            raise ConversationStoreError("Nao foi possivel atualizar o historico da conversa.") from error
        except (KeyError, TypeError, json.JSONDecodeError):
            return None

    def _clear_session(self) -> None:
        try:
            response = self.table.query(
                KeyConditionExpression=Key("pk").eq(self._partition_key)
                & Key("sk").begins_with("SESSION#"),
                ScanIndexForward=True,
            )
            for item in response.get("Items", []):
                self.table.delete_item(Key={"pk": item["pk"], "sk": item["sk"]})
        except (BotoCoreError, ClientError) as error:
            raise ConversationStoreError("Nao foi possivel excluir o historico da conversa.") from error


def _conversation_key(conversation_id: UUID) -> str:
    return f"CONVERSATION#{conversation_id}"


def _make_title(message: str) -> str:
    normalized = " ".join(message.split())
    return normalized[:72] or "Nova conversa"


def _utc_now() -> str:
    return datetime.now(UTC).isoformat(timespec="milliseconds")
