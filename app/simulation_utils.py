"""Utility functions for running portfolio simulations."""

from __future__ import annotations

from typing import Any
import simpy
import pandas as pd

from sim import Portfolio, parseYAML


def run_simulation(events: Any | None = None, *, steps: int = 12) -> dict:
    """Run a simple portfolio simulation.

    Parameters
    ----------
    events : str | list[dict] | None
        Either a YAML string or a list of event dictionaries describing the
        projects to create.
    steps : int, optional
        Number of simulation steps to run, by default 12.

    Returns
    -------
    dict
        Simulation results containing projects, transactions and budget records.
    """
    if isinstance(events, str):
        try:
            events = parseYAML(events)
        except Exception:
            events = []
    events = events or []

    env = simpy.Environment()
    portfolio = Portfolio(env)

    if events:
        portfolio.set_portfolio(events)

    portfolio.run(until=steps)

    return {
        "projects": portfolio.list_projects().to_dict(orient="records"),
        "transactions": portfolio.list_transactions().to_dict(orient="records"),
        "budget": portfolio.getbudget().to_dict(orient="records"),
    }
