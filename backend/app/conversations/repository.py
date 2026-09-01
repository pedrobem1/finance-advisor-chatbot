import json
import sqlite3
from contextlib import closing
from pathlib import Path
from uuid import UUID

from app.core.config import get_settings
from app.schemas.chart import ChartArtifact
from app.schemas.conversation import ConversationDetail, ConversationMessage, ConversationSummary


class ConversationStoreError(RuntimeError):
    """Raised when conversation data cannot be stored or retrieved."""


class ConversationStore:
    def __init__(self, database_path: Path) -> None:
        self.database_path = database_path
        self.database_path.parent.mkdir(parents=True, exist_ok=True)

    def save_exchange(
        self,
        conversation_id: UUID,
        user_message: str,
        answer: str,
        tools_used: list[str],
        charts: list[ChartArtifact],
    ) -> None:
        title = self._make_title(user_message)
        messages = [
            ("user", user_message, "[]", "[]"),
            (
                "assistant",
                answer,
                json.dumps(tools_used, ensure_ascii=False),
                json.dumps([chart.model_dump() for chart in charts], ensure_ascii=False),
            ),
        ]

        try:
            with closing(self._connect()) as connection, connection:
                self._initialize(connection)
                connection.execute(
                    """
                    INSERT OR IGNORE INTO conversations (conversation_id, title)
                    VALUES (?, ?)
                    """,
                    (str(conversation_id), title),
                )
                connection.executemany(
                    """
                    INSERT INTO conversation_messages (conversation_id, role, content, tools_json, charts_json)
                    VALUES (?, ?, ?, ?, ?)
                    """,
                    [(str(conversation_id), *message) for message in messages],
                )
                connection.execute(
                    "UPDATE conversations SET updated_at = CURRENT_TIMESTAMP WHERE conversation_id = ?",
                    (str(conversation_id),),
                )
        except sqlite3.Error as error:
            raise ConversationStoreError("Nao foi possivel salvar a conversa.") from error

    def list_conversations(self, limit: int = 50) -> list[ConversationSummary]:
        try:
            with closing(self._connect()) as connection:
                self._initialize(connection)
                rows = connection.execute(
                    """
                    SELECT conversation_id, title, created_at, updated_at
                    FROM conversations
                    ORDER BY updated_at DESC, created_at DESC
                    LIMIT ?
                    """,
                    (limit,),
                ).fetchall()
        except sqlite3.Error as error:
            raise ConversationStoreError("Nao foi possivel listar as conversas.") from error

        return [self._to_summary(row) for row in rows]

    def get_conversation(self, conversation_id: UUID) -> ConversationDetail | None:
        try:
            with closing(self._connect()) as connection:
                self._initialize(connection)
                row = connection.execute(
                    """
                    SELECT conversation_id, title, created_at, updated_at
                    FROM conversations
                    WHERE conversation_id = ?
                    """,
                    (str(conversation_id),),
                ).fetchone()
                if row is None:
                    return None

                message_rows = connection.execute(
                    """
                    SELECT id, role, content, tools_json, charts_json, created_at
                    FROM conversation_messages
                    WHERE conversation_id = ?
                    ORDER BY id ASC
                    """,
                    (str(conversation_id),),
                ).fetchall()
        except sqlite3.Error as error:
            raise ConversationStoreError("Nao foi possivel abrir a conversa.") from error

        try:
            return ConversationDetail(
                **self._to_summary(row).model_dump(),
                messages=[
                    ConversationMessage(
                        id=str(message_row["id"]),
                        role=message_row["role"],
                        content=message_row["content"],
                        tools=json.loads(message_row["tools_json"]),
                        charts=[
                            ChartArtifact.model_validate(chart)
                            for chart in json.loads(message_row["charts_json"])
                        ],
                        created_at=message_row["created_at"],
                    )
                    for message_row in message_rows
                ],
            )
        except (TypeError, ValueError, json.JSONDecodeError) as error:
            raise ConversationStoreError("A conversa armazenada esta invalida.") from error

    def delete_conversation(self, conversation_id: UUID) -> bool:
        try:
            with closing(self._connect()) as connection, connection:
                self._initialize(connection)
                connection.execute(
                    "DELETE FROM conversation_messages WHERE conversation_id = ?",
                    (str(conversation_id),),
                )
                cursor = connection.execute(
                    "DELETE FROM conversations WHERE conversation_id = ?",
                    (str(conversation_id),),
                )
        except sqlite3.Error as error:
            raise ConversationStoreError("Nao foi possivel excluir a conversa.") from error

        return cursor.rowcount > 0

    def _connect(self) -> sqlite3.Connection:
        connection = sqlite3.connect(self.database_path, timeout=5)
        connection.row_factory = sqlite3.Row
        connection.execute("PRAGMA busy_timeout = 5000")
        connection.execute("PRAGMA journal_mode = WAL")
        return connection

    @staticmethod
    def _initialize(connection: sqlite3.Connection) -> None:
        connection.executescript(
            """
            CREATE TABLE IF NOT EXISTS conversations (
                conversation_id TEXT PRIMARY KEY,
                title TEXT NOT NULL,
                created_at TEXT NOT NULL DEFAULT CURRENT_TIMESTAMP,
                updated_at TEXT NOT NULL DEFAULT CURRENT_TIMESTAMP
            );

            CREATE TABLE IF NOT EXISTS conversation_messages (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                conversation_id TEXT NOT NULL,
                role TEXT NOT NULL,
                content TEXT NOT NULL,
                tools_json TEXT NOT NULL,
                charts_json TEXT NOT NULL,
                created_at TEXT NOT NULL DEFAULT CURRENT_TIMESTAMP
            );

            CREATE INDEX IF NOT EXISTS idx_conversation_messages_conversation_id
            ON conversation_messages (conversation_id, id);
            """
        )

    @staticmethod
    def _make_title(message: str) -> str:
        normalized = " ".join(message.split())
        return normalized[:72] or "Nova conversa"

    @staticmethod
    def _to_summary(row: sqlite3.Row) -> ConversationSummary:
        return ConversationSummary(
            conversation_id=UUID(row["conversation_id"]),
            title=row["title"],
            created_at=row["created_at"],
            updated_at=row["updated_at"],
        )


def get_conversation_store() -> ConversationStore:
    return ConversationStore(get_settings().conversation_database_path)
