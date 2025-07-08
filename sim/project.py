"""Project management classes for the simulation engine."""

from __future__ import annotations

import pandas as pd

from .constants import SUPPORTDATA
from .models import Worker
from .utils import printtimestamp


class Project:
    """Represents a project in the simulation."""

    def __init__(self, portfolio, **kwargs):
        self.kwargs = kwargs
        self.name = kwargs.get("name", "New Project")
        self.term = kwargs.get("term", 0)
        self.directcosts = kwargs.get("directcosts", [])
        self.supports = kwargs.get("supports", [])
        self.portfolio = portfolio
        self.startstep = kwargs.get("time", portfolio.now)
        self.consolidated_account = portfolio.consolidated_account
        self.budget = kwargs.get("budget", 0)
        self.policies = []

        # Initialize policies
        policies = kwargs.get("policies")
        if policies:
            # Import policies here to avoid circular imports
            from .policies import get_policy_class

            for policy in policies:
                cls = get_policy_class(policy["policy"])
                if cls:
                    self.policies.append(cls(self.portfolio, self, **policy))

        # Initialize staff
        self.staff = []
        staffing = kwargs.get("staffing", [])
        for person in staffing:
            self.addstaff(Worker(**person))

        self.costs_thismonth = 0
        self.income_thismonth = 0
        self.cost = 0
        self.income = 0
        self.current_step = 0

    def calculate(self, step: int):
        """Calculate costs and income for a step."""
        dcosts = self.getdirectcosts(step)
        directcost = sum(d["budget"] for d in dcosts if "budget" in d)
        scosts = self.getsupports(step)
        supportcost = sum(d["budget"] for d in scosts if "budget" in d)
        self.costs_thismonth += self.getsalarycosts(step) + directcost + supportcost
        self.income_thismonth += 0

    def getsupports(self, step: int):
        """Get support costs for a step."""
        costs = []
        for support in self.supports:
            item = support.get("item", "unspecified")
            applystep = support.get("step", 0)
            description = support.get("description", "")
            freq = support.get("frequency", "oneoff")
            matching = [d for d in SUPPORTDATA if d.get("item") == item]
            eligiblestep = (
                freq == "monthly"
                or (freq == "oneoff" and applystep == step)
                or (freq == "annual" and (step - applystep) % 12 == 0)
            )
            if eligiblestep and matching:
                lookup = matching[0]
                cost = support["units"] * lookup["dayrate"] * lookup["daysperunit"]
            else:
                cost = 0
            costs.append({"step": step, "item": item, "budget": cost, "description": description})
        return costs

    def getdirectcosts(self, step: int):
        """Get direct costs for a step."""
        costs = []
        for directcost in self.directcosts:
            freq = directcost.get("frequency", "oneoff")
            applystep = directcost.get("step", 0)
            item = directcost.get("item", "unspecified")
            cost = directcost.get("cost", 0)
            description = directcost.get("description", "")
            type_desc = directcost.get("type", "2. Standard")
            if (
                freq == "monthly"
                or (freq == "oneoff" and applystep == step)
                or (freq == "annual" and (step - applystep) % 12 == 0)
            ):
                pass
            else:
                cost = 0
            costs.append({"step": step, "item": item, "budget": cost, "description": description, "type": type_desc})
        return costs

    def getstaffcosts(self, step: int | None = None):
        """Get staff costs for a step or all steps."""
        from .policies import FullCostRecovery

        fcr_policy = next((p for p in self.policies if isinstance(p, FullCostRecovery)), None)

        def getstep(step: int):
            stepregister = []
            for person in self.staff:
                breakdown = person.getbreakdown(step)
                for entry in breakdown:
                    entry["name"] = person.name
                stepregister.extend(breakdown)
                if fcr_policy is not None:
                    fcr_entries = fcr_policy.getfcr(person, step)
                    for entry in fcr_entries:
                        entry["name"] = person.name
                    stepregister.extend(fcr_entries)
            return stepregister

        register = []
        if step is not None:
            register.extend(getstep(step))
        else:
            for s in range(self.term):
                register.extend(getstep(s))
        return pd.DataFrame(register)

    def getbudget(self) -> pd.DataFrame:
        """Get budget for the entire project."""
        budget = []
        for i in range(self.term):
            directcosts = self.getdirectcosts(i)
            supportcosts = self.getsupports(i)
            budget.extend(directcosts)
            budget.extend(supportcosts)
            for st in self.staff:
                budget.extend(st.getbreakdown(i))
        for policy in self.policies:
            if hasattr(policy, "getbudget") and callable(policy.getbudget):
                budget.extend(policy.getbudget())
        df = pd.DataFrame(budget)
        return df

    def getbudgetadjusted(self) -> pd.DataFrame:
        """Get budget adjusted for project start step."""
        df = self.getbudget()
        if "step" in df.columns:
            df["step"] = df["step"] + self.startstep
        return df

    def getsalarycosts(self, step: int) -> float:
        """Get salary costs for a step."""
        cost = 0
        for worker in self.staff:
            cost += worker.getMonthSalaryCost(step)
        return cost

    def addstaff(self, staff: Worker):
        """Add a staff member to the project."""
        self.staff.append(staff)

    def sweep_policies(self, step: int):
        """Apply all policies for a step."""
        for policy in self.policies:
            policy.calculate(step)

    def step(self) -> bool:
        """Advance the project by one step."""
        if self.current_step >= self.term:
            return False
        i = self.current_step
        self.income_thismonth = self.costs_thismonth = 0
        self.calculate(i)
        self.sweep_policies(i)
        self.income += self.income_thismonth
        self.cost += self.costs_thismonth
        cons = self.portfolio.consolidated_account
        cons.update(
            {"type": "expenditure", "title": "project costs", "project": self.name, "amount": self.costs_thismonth}
        )
        cons.update(
            {"type": "income", "title": "project income", "project": self.name, "amount": self.income_thismonth}
        )
        self.current_step += 1
        if self.current_step == self.term:
            printtimestamp(self.portfolio)
            print(
                f"Project {self.name} cost {self.cost:.2f} and generated {self.income:.2f} "
                f"with budget {self.budget:.2f}"
            )
        return True
