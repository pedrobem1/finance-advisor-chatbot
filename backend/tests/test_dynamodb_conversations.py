import asyncio
from uuid import UUID

from app.conversations.dynamodb import DynamoDBConversationStore, DynamoDBSession
from app.schemas.source import WebSource


class FakeDynamoTable:
    def __init__(self) -> None:
        self.items: dict[tuple[str, str], dict] = {}

    def update_item(self, *, Key, ExpressionAttributeValues, **_) -> None:
        item = self.items.setdefault(tuple(Key.values()), dict(Key))
        item.update(
            {
                "title": item.get("title", ExpressionAttributeValues[":title"]),
                "created_at": item.get("created_at", ExpressionAttributeValues[":created_at"]),
                "updated_at": ExpressionAttributeValues[":updated_at"],
                "client_id": ExpressionAttributeValues[":client_id"],
                "gsi1pk": ExpressionAttributeValues[":gsi1pk"],
                "gsi1sk": ExpressionAttributeValues[":gsi1sk"],
            }
        )

    def put_item(self, *, Item) -> None:
        self.items[(Item["pk"], Item["sk"])] = Item

    def get_item(self, *, Key) -> dict:
        item = self.items.get((Key["pk"], Key["sk"]))
        return {"Item": item} if item else {}

    def delete_item(self, *, Key) -> None:
        self.items.pop((Key["pk"], Key["sk"]), None)

    def query(self, **kwargs) -> dict:
        if kwargs.get("IndexName"):
            index_key = kwargs["KeyConditionExpression"]._values[1]
            rows = [item for item in self.items.values() if item.get("gsi1pk") == index_key]
            rows.sort(key=lambda item: item["gsi1sk"], reverse=not kwargs.get("ScanIndexForward", True))
        else:
            condition = kwargs["KeyConditionExpression"]
            values = getattr(condition, "_values", ())
            if len(values) == 2 and hasattr(values[0], "_values"):
                partition_key = values[0]._values[1]
                prefix = values[1]._values[1]
            else:
                partition_key = values[1]
                prefix = ""
            rows = [
                item
                for item in self.items.values()
                if item["pk"] == partition_key and item["sk"].startswith(prefix)
            ]
            rows.sort(key=lambda item: item["sk"], reverse=not kwargs.get("ScanIndexForward", True))
        limit = kwargs.get("Limit")
        return {"Items": rows[:limit] if limit else rows}


def test_dynamodb_conversation_store_saves_lists_loads_and_deletes() -> None:
    table = FakeDynamoTable()
    store = DynamoDBConversationStore("mnc-conversations", table=table)
    client_id = UUID("054b7140-516a-456c-a5f6-3cc2f2a0a9a5")
    other_client_id = UUID("a4e6aa9e-bf42-48f8-930d-8d94a6f38814")
    conversation_id = UUID("a2eb2b69-9a4b-4e76-9090-5936f73bc117")

    store.save_exchange(
        client_id=client_id,
        conversation_id=conversation_id,
        user_message="Explique o P/L da PETR4",
        answer="P/L compara preco e lucro.",
        tools_used=["finance_specialist"],
        charts=[],
        sources=[WebSource(url="https://b3.com.br/noticia", domain="b3.com.br")],
    )

    summaries = store.list_conversations(client_id)
    detail = store.get_conversation(client_id, conversation_id)

    assert summaries[0].conversation_id == conversation_id
    assert detail is not None
    assert [message.role for message in detail.messages] == ["user", "assistant"]
    assert detail.messages[1].tools == ["finance_specialist"]
    assert detail.messages[1].sources[0].domain == "b3.com.br"
    assert store.list_conversations(other_client_id) == []
    assert store.get_conversation(other_client_id, conversation_id) is None
    assert store.delete_conversation(other_client_id, conversation_id) is False
    assert store.delete_conversation(client_id, conversation_id) is True
    assert store.get_conversation(client_id, conversation_id) is None


def test_dynamodb_session_keeps_agent_history_in_order() -> None:
    session = DynamoDBSession(
        session_id="conversation-123",
        table_name="mnc-conversations",
        history_limit=40,
        table=FakeDynamoTable(),
    )

    asyncio.run(session.add_items([{"role": "user", "content": "Ola"}, {"role": "assistant", "content": "Oi"}]))

    assert asyncio.run(session.get_items()) == [
        {"role": "user", "content": "Ola"},
        {"role": "assistant", "content": "Oi"},
    ]
    assert asyncio.run(session.pop_item()) == {"role": "assistant", "content": "Oi"}
    asyncio.run(session.clear_session())
    assert asyncio.run(session.get_items()) == []
