"""SQLite archive with FTS5 and model-tagged dense vectors (cosine search)."""
import json
import math
import re
import sqlite3
from contextlib import contextmanager
from pathlib import Path
from db.models import EvidenceRecord, claim_key, source_id


class Archive:
    def __init__(self, path: str | Path):
        self.path = Path(path)

    @contextmanager
    def connection(self):
        self.path.parent.mkdir(parents=True, exist_ok=True)
        conn = sqlite3.connect(self.path, timeout=10)
        try:
            conn.row_factory = sqlite3.Row
            with conn:
                yield conn
        finally:
            conn.close()

    def initialize(self):
        with self.connection() as conn:
            conn.executescript("""
                CREATE TABLE IF NOT EXISTS evidence (
                    id TEXT PRIMARY KEY, source_url TEXT NOT NULL, claim_key TEXT NOT NULL,
                    document TEXT NOT NULL, embedding TEXT, embedding_model TEXT
                );
                CREATE INDEX IF NOT EXISTS evidence_claim_key ON evidence(claim_key);
                CREATE VIRTUAL TABLE IF NOT EXISTS evidence_fts USING fts5(id UNINDEXED, content);
            """)

    def import_records(self, records: list[EvidenceRecord]) -> int:
        self.initialize()
        with self.connection() as conn:
            for record in records:
                url = str(record.source_url)
                identifier = source_id(url + "|" + claim_key(record.claim_text))
                document = record.model_dump(mode="json")
                serialized = json.dumps(document, ensure_ascii=False)
                old = conn.execute("SELECT document FROM evidence WHERE id=?", (identifier,)).fetchone()
                keep_vector = old and old['document'] == serialized
                conn.execute("""INSERT INTO evidence(id, source_url, claim_key, document) VALUES(?,?,?,?)
                    ON CONFLICT(id) DO UPDATE SET document=excluded.document""",
                    (identifier, url, claim_key(record.claim_text), serialized))
                if not keep_vector:
                    conn.execute("UPDATE evidence SET embedding=NULL, embedding_model=NULL WHERE id=?", (identifier,))
                conn.execute("DELETE FROM evidence_fts WHERE id=?", (identifier,))
                text = ' '.join([record.claim_text, *record.aliases, record.title, record.snippet])
                conn.execute("INSERT INTO evidence_fts(id,content) VALUES(?,?)", (identifier, text))
        return len(records)

    def records(self) -> list[dict]:
        self.initialize()
        with self.connection() as conn:
            return [dict(row) for row in conn.execute('SELECT * FROM evidence ORDER BY id')]

    def set_vector(self, identifier: str, model: str, vector: list[float]):
        if not vector or not all(math.isfinite(x) for x in vector):
            raise ValueError('Embedding must contain finite values')
        with self.connection() as conn:
            conn.execute('UPDATE evidence SET embedding=?, embedding_model=? WHERE id=?',
                         (json.dumps(vector), model, identifier))

    def search(self, claim: str, vector: list[float] | None = None, model: str = '', limit: int = 8) -> list[dict]:
        self.initialize()
        tokenize = lambda text: re.findall(r'\d+(?:[,.]\d+)*(?:%)?|[^\W\d_]+', text.casefold())
        tokens = list(dict.fromkeys(tokenize(claim)))[:40]
        candidates = {}
        with self.connection() as conn:
            if tokens:
                query = ' OR '.join('"' + token.replace('"', '') + '"' for token in tokens)
                rows = conn.execute('''SELECT e.*, bm25(evidence_fts) AS rank FROM evidence_fts
                    JOIN evidence e ON e.id=evidence_fts.id WHERE evidence_fts MATCH ? ORDER BY rank LIMIT 30''', (query,))
                stop = {'the','a','an','of','and','to','in','is','are','has','have','ang','ng','sa','mga','ay','na','si','at'}
                query_terms = set(tokens) - stop
                for row in rows:
                    doc = json.loads(row['document'])
                    doc_terms = set(tokenize(' '.join([doc['claim_text'], *doc['aliases'], doc['title']]))) - stop
                    overlap = len(query_terms & doc_terms) / max(1, len(query_terms))
                    if overlap >= 0.3 and len(query_terms & doc_terms) >= min(2, len(query_terms)):
                        candidates[row['id']] = (dict(row), overlap, 'keyword')
            for row in conn.execute('SELECT * FROM evidence'):
                doc = json.loads(row['document'])
                exact = claim_key(claim) in {claim_key(doc['claim_text']), *(claim_key(x) for x in doc['aliases'])}
                if exact:
                    candidates[row['id']] = (dict(row), 1.0, 'exact')
                elif vector and row['embedding_model'] == model and row['embedding']:
                    stored = json.loads(row['embedding'])
                    if len(stored) != len(vector):
                        continue
                    denominator = math.sqrt(sum(x*x for x in stored) * sum(x*x for x in vector))
                    score = sum(a*b for a,b in zip(stored,vector)) / denominator if denominator else 0
                    if score >= 0.6 and score > candidates.get(row['id'], ({}, 0, ''))[1]:
                        candidates[row['id']] = (dict(row), score, 'vector')
        results = []
        for row, score, method in sorted(candidates.values(), key=lambda item: item[1], reverse=True)[:limit]:
            doc = json.loads(row['document'])
            results.append({**doc, 'id': row['id'], 'score': score, 'match_method': method,
                            'source_type': 'local_archive', 'relevance': 'contextual'})
        return results


def load_records(path: str | Path) -> list[EvidenceRecord]:
    return [EvidenceRecord.model_validate(item) for item in json.loads(Path(path).read_text(encoding='utf-8'))]
