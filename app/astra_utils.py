"""Utility functions for Astra database operations.

This module uses the DataAPIClient API from astrapy.
Usage example:
    client, collection = init_astra_db(
        token="AstraCS:xxx",
        endpoint="https://<db-id>-<region>.apps.astra.datastax.com",
        collection="my_collection"
    )
    collection.insert_one({"hello": "world"})

Environment variables:
    ASTRA_DB_TOKEN: Your Astra DB token (AstraCS:...)
    ASTRA_DB_ENDPOINT: Your database API endpoint
    ASTRA_DB_DATABASE: Default database name (optional)
"""

import os
from astrapy import DataAPIClient

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
    database: str | None = None,
    collection: str | None = None
):
    """Initialise and return a :class:`DataAPIClient` and optionally a collection."""
    token = token or os.getenv("ASTRA_DB_TOKEN")
    endpoint = endpoint or os.getenv("ASTRA_DB_ENDPOINT")
    database = database or os.getenv("ASTRA_DB_DATABASE")
    if not token or not endpoint:
        raise ValueError("ASTRA_DB_TOKEN and ASTRA_DB_ENDPOINT must be provided")

    client = DataAPIClient(token=token)
    db = client.get_database_by_api_endpoint(endpoint)
    
    if collection:
        coll = db.get_collection(collection)
        return client, coll
    else:
        return client, db


def get_database(client: DataAPIClient, endpoint: str):
    """Get a database instance from the DataAPIClient."""
    return client.get_database_by_api_endpoint(endpoint)


def get_collection(client: DataAPIClient, endpoint: str, collection: str):
    """Get a collection instance from the DataAPIClient."""
    db = client.get_database_by_api_endpoint(endpoint)
    return db.get_collection(collection)


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
