"""Portfolio management for the simulation engine."""

from __future__ import annotations

import pandas as pd

from .models import ConsolidatedAccount
from .utils import get_current_month, printtimestamp


class Portfolio:
    """Manages a portfolio of projects."""

    def __init__(self, name: str = "My Portfolio"):
        self.name = name
        self.now = 0
        self.consolidated_account = ConsolidatedAccount(self)
        self.projects: list = []
        self._pending_events: list[dict] = []

    def counter(self):
        """Counter process for debugging."""
        for i in range(1, 31):
            month = get_current_month(start_month="apr", month=i)
            print(f"\nMonth: {i} {month}")

    def set_event(self, event: dict):
        """Schedule an event for a future step."""
        self._pending_events.append(event)
        self._pending_events.sort(key=lambda e: e.get("time", 0))

    def set_portfolio(self, events: list[dict]):
        """Set up multiple events for the portfolio."""
        for event in events:
            self.set_event(event)

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

    def run(self, steps: int):
        """Run the simulation for a number of steps."""
        for step in range(steps):
            self.now = step
            # create projects whose start time matches current step
            events_to_start = [e for e in self._pending_events if e.get("time", 0) == step]
            for event in events_to_start:
                printtimestamp(self)
                message = event.get("message", event.get("name", "new project"))
                print(f"Event {message} succeeds")
                self.create_project(**event)
            self._pending_events = [e for e in self._pending_events if e not in events_to_start]

            # update active projects
            for prj in list(self.projects):
                prj.step()

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
        prj = cls(self, **kwargs)
        self.projects.append(prj)
        staff_names = ", ".join(person.name for person in prj.staff)
        print(
            f"Project {prj.name} created with budget {prj.budget:.2f} and assigned staff {staff_names}"
        )
        return prj

    def finance(self, term: int, capital: float, rate: float = 0.05):
        """Finance the portfolio."""
        repayment = capital / term
        account = capital
        print(f"New capital received {capital}")
        self.consolidated_account.update(
            {"type": "income", "title": "finance capitalisation", "project": "headoffice", "amount": capital}
        )
        totpay = 0
        for _ in range(term):
            interest = rate * account
            account -= repayment
            payment = repayment + interest
            totpay += payment
            self.consolidated_account.update(
                {"type": "expenditure", "title": "finance servicing", "project": "headoffice", "amount": payment}
            )
        printtimestamp(self)
        print(f"Finance: Final account {account:.2f}, total paid {totpay:.2f}")
