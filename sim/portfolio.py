"""Portfolio management for the simulation engine."""

from __future__ import annotations

import pandas as pd
import simpy

from .models import ConsolidatedAccount
from .utils import get_current_month, printtimestamp


class Portfolio:
    """Manages a portfolio of projects."""

    def __init__(self, env: simpy.Environment, name: str = "My Portfolio"):
        self.env = env
        self.name = name
        self.consolidated_account = ConsolidatedAccount(env)
        self.projects = []

    def counter(self):
        """Counter process for debugging."""
        for i in range(1, 31):
            month = get_current_month(start_month="apr", month=self.env.now)
            print(f"\nMonth: {i} {month}")
            yield self.env.timeout(1)

    def set_event(self, event: dict):
        """Set up an event in the simulation."""
        e = self.env.event()
        e.details = event
        yield self.env.timeout(event["time"])
        printtimestamp(self.env)
        message = event.get("message", event.get("name", "new project"))
        print(f"Event {message} succeeds")
        e.succeed()
        self.env.process(self.create_project(**event))

    def set_portfolio(self, events: list[dict]):
        """Set up multiple events for the portfolio."""
        for event in events:
            self.env.process(self.set_event(event))

    def getbudget(self) -> pd.DataFrame:
        """Get consolidated budget for all projects."""
        data = {"item": [], "step": [], "budget": []}
        consol_budget = pd.DataFrame(data)
        for prj in self.projects:
            budget = prj.getbudgetadjusted()
            consol_budget = pd.concat([consol_budget, budget], ignore_index=True)
        return consol_budget

    def list_projects(self) -> pd.DataFrame:
        """List all projects in the portfolio."""
        data = []
        for prj in self.projects:
            data.append({k: v for k, v in prj.__dict__.items() if isinstance(v, (str, int, float, bool))})
        df = pd.DataFrame(data)
        # round numeric columns to 2 decimal places but retain all columns
        numeric_cols = df.select_dtypes(include=["number"]).columns
        df[numeric_cols] = df[numeric_cols].round(2)

        return df

    def run(self, until: int):
        """Run the simulation until a specific time."""
        self.env.run(until=until)

    def list_transactions(self) -> pd.DataFrame:
        """List all transactions in the consolidated account."""
        transactions = self.consolidated_account.register
        df = pd.DataFrame(transactions)
        self.consolidated_account.report()
        return df

    def create_project(self, cls=None, **kwargs):
        """Create a new project in the portfolio."""
        if cls is None:
            from .project import Project

            cls = Project
        prj = cls(self, self.env, **kwargs)
        self.projects.append(prj)
        staff_names = ", ".join(person.name for person in prj.staff)
        print(f"Project {prj.name} created with budget {prj.budget:.2f} " f"and assigned staff {staff_names}")
        yield self.env.timeout(1)

    def finance(self, term: int, capital: float, rate: float = 0.05):
        """Finance the portfolio."""
        repayment = capital / term
        account = capital
        print(f"New capital received {capital}")
        self.consolidated_account.update(
            {"type": "income", "title": "finance capitalisation", "project": "headoffice", "amount": capital}
        )
        totpay = 0
        for i in range(term):
            interest = rate * account
            account = account - repayment
            payment = repayment + interest
            totpay += payment
            self.consolidated_account.update(
                {"type": "expenditure", "title": "finance servicing", "project": "headoffice", "amount": payment}
            )
            yield self.env.timeout(1)
        printtimestamp(self.env)
        print(f"Finance: Final account {account:.2f}, total paid {totpay:.2f}")
