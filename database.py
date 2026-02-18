"""
Handler Database - Azure Table Storage
Menyimpan URL artikel yang sudah dikirim agar tidak duplikat.
Menggantikan SQLite karena Azure Functions filesystem bersifat ephemeral.
"""

import hashlib
import logging
from datetime import datetime, timezone, timedelta
from azure.data.tables import TableServiceClient, TableClient
from azure.core.exceptions import ResourceExistsError, ResourceNotFoundError
from config import AZURE_STORAGE_CONNECTION_STRING, TABLE_NAME

logger = logging.getLogger(__name__)

# ─── Helper ──────────────────────────────────────────────────────────────────

def _url_to_row_key(url: str) -> str:
    """
    Azure Table Storage RowKey tidak boleh mengandung karakter khusus.
    Gunakan MD5 hash dari URL agar aman dan unik.
    """
    return hashlib.md5(url.encode()).hexdigest()


def _get_table_client() -> TableClient:
    service = TableServiceClient.from_connection_string(
        AZURE_STORAGE_CONNECTION_STRING
    )
    return service.get_table_client(TABLE_NAME)


# ─── Public API ───────────────────────────────────────────────────────────────

def init_table() -> None:
    """Buat Azure Storage Table jika belum ada (idempotent)."""
    try:
        service = TableServiceClient.from_connection_string(
            AZURE_STORAGE_CONNECTION_STRING
        )
        service.create_table(TABLE_NAME)
        logger.info("Azure Table '%s' berhasil dibuat.", TABLE_NAME)
    except ResourceExistsError:
        logger.info("Azure Table '%s' sudah ada.", TABLE_NAME)
    except Exception as e:
        logger.error("Gagal inisialisasi Azure Table: %s", e)
        raise


def is_sent(url: str) -> bool:
    """Kembalikan True jika artikel sudah pernah dikirim."""
    client = _get_table_client()
    row_key = _url_to_row_key(url)
    try:
        client.get_entity(partition_key="article", row_key=row_key)
        return True
    except ResourceNotFoundError:
        return False
    except Exception as e:
        logger.warning("Gagal cek status artikel: %s", e)
        return False


def mark_sent(url: str) -> None:
    """Tandai artikel sebagai sudah dikirim."""
    client = _get_table_client()
    row_key = _url_to_row_key(url)
    entity = {
        "PartitionKey": "article",
        "RowKey":        row_key,
        "url":           url[:1024],   # simpan URL asli untuk debugging
        "sent_at":       datetime.now(timezone.utc).isoformat(),
    }
    try:
        client.upsert_entity(entity=entity)
    except Exception as e:
        logger.error("Gagal menyimpan artikel ke Table Storage: %s", e)


def cleanup_old_articles(days: int = 30) -> None:
    """
    Hapus artikel lama (> N hari) dari Azure Table Storage.
    Dipanggil otomatis setiap invocation, namun murah karena filter server-side.
    """
    client = _get_table_client()
    cutoff = datetime.now(timezone.utc) - timedelta(days=days)
    cutoff_str = cutoff.isoformat()

    try:
        # Query entitas yang lebih tua dari cutoff
        entities = client.query_entities(
            query_filter=f"PartitionKey eq 'article' and sent_at lt '{cutoff_str}'"
        )
        deleted = 0
        for entity in entities:
            client.delete_entity(
                partition_key=entity["PartitionKey"],
                row_key=entity["RowKey"],
            )
            deleted += 1
        if deleted:
            logger.info("Cleanup: %d artikel lama dihapus dari Table Storage.", deleted)
    except Exception as e:
        logger.warning("Cleanup gagal (non-fatal): %s", e)
