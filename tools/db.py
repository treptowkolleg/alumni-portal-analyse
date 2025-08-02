import json
import numpy as np
from datetime import datetime
import sqlite3


def add_embedding_for_speaker(conn, speaker_id: int, new_embedding: np.ndarray, max_embeddings: int = 100):
    c = conn.cursor()

    c.execute("""
            SELECT id FROM speaker_profiles
            WHERE speaker_id = ?
        """, (speaker_id,))

    profile_id = c.fetchone()[0]

    # 1. Neues Embedding einfügen
    c.execute("""
        INSERT INTO speaker_embeddings (speaker_id, embedding, created_at)
        VALUES (?, ?, ?)
    """, (profile_id, json.dumps(new_embedding.tolist()), datetime.now().isoformat()))

    # 2. Zu viele alte Einträge löschen (FIFO)
    c.execute("""
        SELECT id FROM speaker_embeddings
        WHERE speaker_id = ?
        ORDER BY created_at
    """, (profile_id,))

    embedding_ids = [row[0] for row in c.fetchall()]
    if len(embedding_ids) > max_embeddings:
        to_delete = embedding_ids[:len(embedding_ids) - max_embeddings]
        c.executemany("DELETE FROM speaker_embeddings WHERE id = ?", [(i,) for i in to_delete])

    # 3. Mittelwert neu berechnen
    c.execute("SELECT embedding FROM speaker_embeddings WHERE speaker_id = ?", (profile_id,))
    all_embeddings = [json.loads(row[0]) for row in c.fetchall()]
    mean_embedding = np.mean(all_embeddings, axis=0)

    # 4. Mittelwert im Profil aktualisieren
    c.execute("""
        UPDATE speaker_profiles
        SET embedding_avg = ?, updated_at = ?
        WHERE id = ?
    """, (json.dumps(mean_embedding.tolist()), datetime.now().isoformat(), profile_id))

    conn.commit()


def create_new_speaker_profile(conn, new_embedding: np.ndarray) -> int:
    c = conn.cursor()
    now = datetime.now().isoformat()
    embedding_json = json.dumps(new_embedding.tolist())

    c.execute("""
                INSERT INTO speaker (name)
                VALUES (?)
            """, ("",))

    new_id = c.lastrowid

    c.execute("""
        INSERT INTO speaker_profiles (name, embedding_avg, created_at, updated_at, speaker_id)
        VALUES (?, ?, ?, ?, ?)
    """, (None, embedding_json, now, now, new_id))
    speaker_id = c.lastrowid

    # Danach erstes Embedding einfügen
    c.execute("""
        INSERT INTO speaker_embeddings (speaker_id, embedding, created_at)
        VALUES (?, ?, ?)
    """, (speaker_id, embedding_json, now))

    conn.commit()
    return new_id