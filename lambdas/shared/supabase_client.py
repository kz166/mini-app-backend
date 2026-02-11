"""
Supabase PostgREST client for Lambda ETL functions.

Uses the REST API directly (no Python SDK dependency) for upserts with
ON CONFLICT merge-duplicates resolution.
"""

import json
import logging
import os
import urllib.error
import urllib.request

logger = logging.getLogger(__name__)

SUPABASE_URL = os.environ.get("SUPABASE_URL", "")
SUPABASE_SERVICE_KEY = os.environ.get("SUPABASE_SERVICE_KEY", "")


def _get_headers():
    return {
        "apikey": SUPABASE_SERVICE_KEY,
        "Authorization": f"Bearer {SUPABASE_SERVICE_KEY}",
        "Content-Type": "application/json",
        "Prefer": "resolution=merge-duplicates,return=representation,count=exact",
    }


def upsert(table: str, rows: list[dict], on_conflict: str, batch_size: int = 500) -> dict:
    """
    Upsert rows into a Supabase table via PostgREST.

    Args:
        table: Table name (e.g., "mortgage_rates")
        rows: List of row dicts to upsert
        on_conflict: Comma-separated conflict columns (e.g., "town_id,date,home_type")
        batch_size: Max rows per request (PostgREST default limit)

    Returns:
        dict with "inserted" and "total" counts
    """
    if not rows:
        logger.info(f"No rows to upsert into {table}")
        return {"inserted": 0, "total": 0}

    url = f"{SUPABASE_URL}/rest/v1/{table}?on_conflict={on_conflict}"
    headers = _get_headers()
    total_upserted = 0

    for i in range(0, len(rows), batch_size):
        batch = rows[i : i + batch_size]
        data = json.dumps(batch).encode("utf-8")

        req = urllib.request.Request(url, data=data, headers=headers, method="POST")

        try:
            with urllib.request.urlopen(req) as resp:
                # Parse content-range header for count: "*/123" or "0-99/123"
                content_range = resp.getheader("content-range", "")
                if "/" in content_range:
                    total_upserted += int(content_range.split("/")[-1])
                else:
                    total_upserted += len(batch)

                logger.info(
                    f"Upserted batch {i // batch_size + 1} into {table}: "
                    f"{len(batch)} rows"
                )
        except urllib.error.HTTPError as e:
            body = e.read().decode("utf-8")
            logger.error(f"Supabase upsert error ({e.code}): {body}")
            raise RuntimeError(f"Supabase upsert failed for {table}: {e.code} {body}") from e

    return {"inserted": len(rows), "total": total_upserted}


def query(table: str, select: str = "*", filters: str = "") -> list[dict]:
    """
    Query a Supabase table via PostgREST.

    Args:
        table: Table name
        select: Column selection (PostgREST select syntax)
        filters: Query string filters (e.g., "town_id=eq.fort_lee&year=eq.2023")

    Returns:
        List of row dicts
    """
    url = f"{SUPABASE_URL}/rest/v1/{table}?select={select}"
    if filters:
        url += f"&{filters}"

    headers = {
        "apikey": SUPABASE_SERVICE_KEY,
        "Authorization": f"Bearer {SUPABASE_SERVICE_KEY}",
    }

    req = urllib.request.Request(url, headers=headers, method="GET")

    try:
        with urllib.request.urlopen(req) as resp:
            return json.loads(resp.read().decode("utf-8"))
    except urllib.error.HTTPError as e:
        body = e.read().decode("utf-8")
        logger.error(f"Supabase query error ({e.code}): {body}")
        raise RuntimeError(f"Supabase query failed for {table}: {e.code} {body}") from e
