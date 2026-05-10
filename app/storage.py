from __future__ import annotations

import re
import sqlite3
from dataclasses import dataclass
from datetime import datetime, timezone
from pathlib import Path

from app.config import get_settings


TOKEN_RE = re.compile(r"[A-Za-z0-9][A-Za-z0-9_\-]{1,48}")


@dataclass(frozen=True)
class SearchHit:
    citation_id: str
    title: str
    source_url: str | None
    content: str
    score: float


def utc_now_iso() -> str:
    return datetime.now(timezone.utc).isoformat()


def chunk_text(text: str, max_chars: int = 1100, overlap: int = 140) -> list[str]:
    paragraphs = [p.strip() for p in re.split(r"\n{2,}", text) if p.strip()]
    chunks: list[str] = []
    current = ""

    for paragraph in paragraphs or [text.strip()]:
        if len(current) + len(paragraph) + 2 <= max_chars:
            current = f"{current}\n\n{paragraph}".strip()
            continue
        if current:
            chunks.append(current)
        if len(paragraph) <= max_chars:
            current = paragraph
            continue
        start = 0
        while start < len(paragraph):
            chunks.append(paragraph[start : start + max_chars].strip())
            start += max_chars - overlap
        current = ""

    if current:
        chunks.append(current)
    return [c for c in chunks if c]


def fts_query(text: str) -> str:
    terms = TOKEN_RE.findall(text.lower())
    deduped = list(dict.fromkeys(terms))
    return " OR ".join(f'"{term}"' for term in deduped[:24]) or '"empty"'


class KnowledgeStore:
    def __init__(self, db_path: Path | None = None) -> None:
        self.db_path = db_path or get_settings().database_path
        self.db_path.parent.mkdir(parents=True, exist_ok=True)
        self._init_db()

    def _connect(self) -> sqlite3.Connection:
        conn = sqlite3.connect(self.db_path)
        conn.row_factory = sqlite3.Row
        conn.execute("PRAGMA foreign_keys = ON")
        return conn

    def _init_db(self) -> None:
        with self._connect() as conn:
            conn.executescript(
                """
                CREATE TABLE IF NOT EXISTS documents (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    title TEXT NOT NULL,
                    source_url TEXT,
                    created_at TEXT NOT NULL
                );

                CREATE TABLE IF NOT EXISTS chunks (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    document_id INTEGER NOT NULL REFERENCES documents(id) ON DELETE CASCADE,
                    ordinal INTEGER NOT NULL,
                    content TEXT NOT NULL
                );

                CREATE VIRTUAL TABLE IF NOT EXISTS chunks_fts USING fts5(
                    content,
                    title UNINDEXED,
                    source_url UNINDEXED,
                    chunk_id UNINDEXED,
                    document_id UNINDEXED
                );
                """
            )

    def add_document(self, title: str, content: str, source_url: str | None = None) -> dict:
        chunks = chunk_text(content)
        with self._connect() as conn:
            cursor = conn.execute(
                "INSERT INTO documents(title, source_url, created_at) VALUES (?, ?, ?)",
                (title.strip(), source_url, utc_now_iso()),
            )
            document_id = int(cursor.lastrowid)
            for ordinal, chunk in enumerate(chunks, start=1):
                chunk_cursor = conn.execute(
                    "INSERT INTO chunks(document_id, ordinal, content) VALUES (?, ?, ?)",
                    (document_id, ordinal, chunk),
                )
                chunk_id = int(chunk_cursor.lastrowid)
                conn.execute(
                    """
                    INSERT INTO chunks_fts(rowid, content, title, source_url, chunk_id, document_id)
                    VALUES (?, ?, ?, ?, ?, ?)
                    """,
                    (chunk_id, chunk, title.strip(), source_url, chunk_id, document_id),
                )
        return self.get_document(document_id)

    def has_document_source(self, source_url: str) -> bool:
        with self._connect() as conn:
            row = conn.execute("SELECT 1 FROM documents WHERE source_url = ? LIMIT 1", (source_url,)).fetchone()
        return row is not None

    def list_documents(self) -> list[dict]:
        with self._connect() as conn:
            rows = conn.execute(
                """
                SELECT d.id, d.title, d.source_url, d.created_at, COUNT(c.id) AS chunk_count
                FROM documents d
                LEFT JOIN chunks c ON c.document_id = d.id
                GROUP BY d.id
                ORDER BY d.created_at DESC
                """
            ).fetchall()
        return [dict(row) for row in rows]

    def get_document(self, document_id: int) -> dict:
        with self._connect() as conn:
            row = conn.execute(
                """
                SELECT d.id, d.title, d.source_url, d.created_at, COUNT(c.id) AS chunk_count
                FROM documents d
                LEFT JOIN chunks c ON c.document_id = d.id
                WHERE d.id = ?
                GROUP BY d.id
                """,
                (document_id,),
            ).fetchone()
        if row is None:
            raise KeyError(f"Document {document_id} not found")
        return dict(row)

    def delete_document(self, document_id: int) -> bool:
        with self._connect() as conn:
            chunk_ids = [
                row["id"]
                for row in conn.execute("SELECT id FROM chunks WHERE document_id = ?", (document_id,)).fetchall()
            ]
            for chunk_id in chunk_ids:
                conn.execute("DELETE FROM chunks_fts WHERE rowid = ?", (chunk_id,))
            cursor = conn.execute("DELETE FROM documents WHERE id = ?", (document_id,))
        return cursor.rowcount > 0

    def search(self, query: str, limit: int = 6) -> list[SearchHit]:
        expression = fts_query(query)
        with self._connect() as conn:
            rows = conn.execute(
                """
                SELECT rowid, title, source_url, content, chunk_id, document_id, bm25(chunks_fts) AS rank
                FROM chunks_fts
                WHERE chunks_fts MATCH ?
                ORDER BY rank
                LIMIT ?
                """,
                (expression, limit),
            ).fetchall()

        hits: list[SearchHit] = []
        for row in rows:
            rank = float(row["rank"])
            score = 1 / (1 + abs(rank))
            hits.append(
                SearchHit(
                    citation_id=f"D{row['document_id']}-C{row['chunk_id']}",
                    title=row["title"],
                    source_url=row["source_url"],
                    content=row["content"],
                    score=round(score, 4),
                )
            )
        return hits
