"""Utility functions for Astra database operations."""

import os
from astrapy.db import AstraDB

# Month names for date conversion
MONTHS = [
    "January",
    "February",
    "March",
    "April",
    "May",
    "June",
    "July",
    "August",
    "September",
    "October",
    "November",
    "December",
]


def init_astra_db(
    token: str | None = None,
    endpoint: str | None = None,
    *,
    namespace: str = "default_keyspace",
    collection: str | None = None
):
    """Initialise and return an :class:`AstraDB` client and optionally a collection."""
    token = token or os.getenv("ASTRA_DB_TOKEN")
    endpoint = endpoint or os.getenv("ASTRA_DB_ENDPOINT")
    if not token or not endpoint:
        raise ValueError("ASTRA_DB_TOKEN and ASTRA_DB_ENDPOINT must be provided")

    astradb = AstraDB(token=token, api_endpoint=endpoint, namespace=namespace)
    coll = astradb.collection(collection) if collection else None
    return astradb, coll


def getDate(date: str) -> dict:
    """Convert ``2022-10-21T13:56:32.503Z`` to ``{"month": "October", "year": "2022"}``."""
    date = date.split("T")[0]
    year, month, _ = date.split("-")
    month_name = MONTHS[int(month) - 1]
    return {"month": month_name, "year": year}


def get_financial_year(date: str) -> int:
    """Return the financial year for ``date`` assuming the year starts in April."""
    date = date.split("T")[0]
    year, month, _ = date.split("-")
    month_name = MONTHS[int(month) - 1]
    year = int(year)
    if month_name in ["January", "February", "March", "April"]:
        year -= 1
    return year


def update_financial_year(collection) -> int:
    """Add a ``FinancialYear`` field on all documents without one."""
    data = collection.find({"FinancialYear": {"$exists": False}})
    for document in data["data"]["documents"]:
        year = get_financial_year(document["createdDateTime"])
        fields = {"FinancialYear": year}
        collection.update_one({"_id": document["_id"]}, {"$set": fields})
    return len(data["data"]["documents"])


def batch_update_financial_year(collection):
    """Batch update financial year for all documents in collection."""
    length = 20
    while length == 20:
        length = update_financial_year(collection)


def update_record(data: dict) -> dict:
    """Return a placeholder update response."""
    # Placeholder update logic
    return {"status": "updated", "data": data}
