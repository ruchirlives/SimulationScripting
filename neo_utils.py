import os
from neo4j import GraphDatabase
from neomodel import config, db
from neomodel.scripts.neomodel_inspect_database import inspect_database


def init_neo4j(uri: str | None = None, user: str | None = None, password: str | None = None):
    """Initialise neomodel using the provided connection details or environment variables.

    Environment variables used: ``NEO4J_URI``, ``NEO4J_USERNAME`` and ``NEO4J_PASSWORD``.
    """
    uri = uri or os.getenv("NEO4J_URI")
    user = user or os.getenv("NEO4J_USERNAME")
    password = password or os.getenv("NEO4J_PASSWORD")
    if not uri or not user or not password:
        raise ValueError("Neo4j connection details must be provided")

    driver = GraphDatabase.driver(uri, auth=(user, password))
    config.DATABASE_URL = f"bolt://{user}:{password}@{uri.replace('bolt://', '')}"
    db.set_connection(driver=driver)
    return driver


def get_models(output_file: str = "models.py"):
    """Use ``neomodel_inspect_database`` to dump models to ``output_file``."""
    script = inspect_database(config.DATABASE_URL)
    with open(output_file, "w") as f:
        f.write(script)
