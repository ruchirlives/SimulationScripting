"""Policy classes for project management."""

from __future__ import annotations

import simpy

from .constants import FCRDATA
from .utils import printtimestamp


class Policy:
    """Base class for all policies."""

    def __init__(self, env: simpy.Environment, prj, **kwargs):
        self.env = env
        self.prj = prj

    def calculate(self, step: int):
        """Calculate policy effects for a step."""
        pass


class FullCostRecovery(Policy):
    """
    This policy calculates costs for staff based on their FTE and applies full cost recovery (FCR) rates.
    User args include:
    - fcrdata: List of FCR items with their costs and frequencies
    - linemanagerrate: Rate for line management
    - fte: Full-time equivalent for the person
    - step: Step at which the FCR is calculated
    The FCR data should include:
    - item: Name of the FCR item
    - daysperfte: Number of days per FTE for the item
    - dayrate: Daily rate for the item
    - frequency: Frequency of the cost (oneoff, monthly, annual)
    - description: Description of the item
    """

    def __init__(self, env: simpy.Environment, prj, **kwargs):
        super().__init__(env, prj, **kwargs)
        self.fcr = self.getfcrdata()
        self.register = []

    def getfcrdata(self):
        """Get FCR data."""
        fcr = []
        for item in FCRDATA:
            fcr.append(item)
        return fcr

    def getfcr(self, person, step: int):
        """Get FCR costs for a person and step."""
        register = []
        linemanagerrate = person.linemanagerrate
        for item in self.fcr:
            itemname = item["item"]
            daysperfte = item["daysperfte"]
            dayrate = linemanagerrate if itemname == "Line Management" else item["dayrate"]
            frequency = item["frequency"]
            try:
                cost = person.fte * daysperfte * dayrate
            except TypeError:
                pass
            if frequency == "oneoff":
                cost = cost if step == 0 else 0
            if frequency == "monthly":  # monthly costs are applied every month, so using the cost directly
                pass
            if frequency == "annual":
                cost = cost if step % 12 == 0 else 0
            register.append(
                {
                    "step": step,
                    "item": itemname,
                    "budget": cost,
                    "type": "3. FullCostRecovery",
                    "description": f"FCR: {itemname}",
                }
            )
        return register

    def calcfcr(self, person, step: int):
        """Calculate FCR for a person and step."""
        register = self.getfcr(person, step)
        self.register.extend(register)
        return sum(item["budget"] for item in register if "budget" in item)

    def calculate(self, step: int):
        """Calculate FCR for all staff in the project."""
        totalcost = 0
        for person in self.prj.staff:
            totalcost += self.calcfcr(person, step)
        self.prj.costs_thismonth += totalcost

    def getbudget(self):
        """Get FCR budget entries."""
        return self.register


class Grant(Policy):
    """
    Grant funding policy.
    This policy applies a grant amount at a specified step.
    User args include:
    - amount: Amount of the grant
    - fund: Name of the grant fund
    - step: Step at which the grant is applied
    """

    def __init__(self, env: simpy.Environment, prj, **kwargs):
        super().__init__(env, prj, **kwargs)
        self.amount = kwargs.get("amount", 0)
        self.fund = kwargs.get("fund", "unspecified")
        self.startstep = kwargs.get("step", 0)
        self.register = []

    def calculate(self, step: int):
        """Apply grant funding at the specified step."""
        prj = self.prj
        amount = self.amount
        if step == self.startstep:
            prj.income_thismonth += amount
            self.register.append({"item": f"{self.fund} grant", "step": step, "budget": -amount, "type": "4. Funding"})

    def getbudget(self):
        """Get grant budget entries."""
        return self.register


class Subsidy(Policy):
    """Government subsidy policy."""

    def calculate(self, step: int):
        """Apply government subsidy."""
        payment = 100000
        prj = self.prj
        prj.income_thismonth += payment
        prj.consolidated_account.update(
            {"type": "income", "title": "government subsidy", "project": prj.name, "amount": payment}
        )


class Rename(Policy):
    """Policy that renames the project."""

    def calculate(self, step: int):
        """Rename the project."""
        self.prj.name = f"Fancy project in step {step}"


class Finance(Policy):
    """
    Finance policy for project funding.
    This policy handles capital received, repayments, and interest calculations.
    User args include:
    - term: Number of steps for repayment
    - capital: Initial capital amount
    - rate: Interest rate applied to the capital
    """

    def __init__(self, env: simpy.Environment, prj, **kwargs):
        super().__init__(env, prj, **kwargs)
        self.term = kwargs.get("term", prj.term)
        self.account = self.capital = kwargs.get("capital", 0)
        self.rate = kwargs.get("rate", 0)
        self.consolidated_account = prj.consolidated_account
        self.totpay = 0
        print(f"New capital received {self.capital}")
        self.consolidated_account.update(
            {"type": "income", "title": "finance capitalisation", "project": "headoffice", "amount": self.capital}
        )

    def calculate(self, step: int):
        """Calculate finance payments."""
        repayment = self.capital / self.term
        interest = self.rate * self.account
        self.account -= repayment
        payment = repayment + interest
        self.totpay += payment
        self.consolidated_account.update(
            {"type": "expenditure", "title": "finance servicing", "project": "headoffice", "amount": payment}
        )
        if step == self.term - 1:
            self.finalize()

    def finalize(self):
        """Finalize the finance policy."""
        printtimestamp(self.env)
        print(f"Finance: Final account {self.account:.2f}, total paid {self.totpay:.2f}")


class CarbonFinancing(Policy):
    """
    Carbon financing policy.
        User args include:
        - investment: Total investment amount
        - tree_planting_cost_per_unit: Cost per tree planted
        - carbon_credit_per_unit: Income per carbon credit
    """
    def __init__(self, env: simpy.Environment, prj, **kwargs):
        """
        Initialize CarbonFinancing policy.
        """
        super().__init__(env, prj, **kwargs)
        self.prj = prj
        self.budget = prj.budget
        self.investment = kwargs.get("investment")
        self.tree_planting_cost_per_unit = kwargs.get("tree_planting_cost_per_unit")
        self.carbon_credit_per_unit = kwargs.get("carbon_credit_per_unit")
        self.trees_planted = self.calculate_trees_planted()
        self.carbon_credits_generated = self.calculate_carbon_credits()
        self.prj.consolidated_account.update(
            {
                "type": "expenditure",
                "title": "capital cost tree planting",
                "project": self.prj.name,
                "amount": self.investment - self.budget,
            }
        )
        print(
            f"Trees planted: {self.trees_planted:.0f} will generate "
            f"{self.calculate_carbon_credits():.0f} carbon credits over 40 years "
            f"worth £{self.calculate_carbon_income():.2f}"
        )

    def calculate_trees_planted(self) -> float:
        """Calculate number of trees planted."""
        return (self.investment - self.budget) / self.tree_planting_cost_per_unit

    def calculate_carbon_credits(self) -> float:
        """Calculate carbon credits generated."""
        unitpertreelifetime = 1.1
        return self.trees_planted * unitpertreelifetime

    def calculate_carbon_income(self) -> float:
        """Calculate income from carbon credits."""
        return self.calculate_carbon_credits() * self.carbon_credit_per_unit

    def report(self):
        """Generate carbon financing report."""
        return {
            "investment": self.investment,
            "trees_planted": self.trees_planted,
            "carbon_credits_generated": self.carbon_credits_generated,
        }

    def calculate(self, step: int):
        """Calculate carbon financing effects."""
        if step == 0:
            carbonincome = self.investment
        else:
            carbonincome = 0
        self.prj.income_thismonth += carbonincome


def get_policy_class(policy_name: str):
    """
    Get policy class by name.
    Options include:
    - FullCostRecovery
    - Grant
    - Subsidy
    - Rename
    - Finance
    - CarbonFinancing

    """
    policy_classes = {
        "FullCostRecovery": FullCostRecovery,
        "Grant": Grant,
        "Subsidy": Subsidy,
        "Rename": Rename,
        "Finance": Finance,
        "CarbonFinancing": CarbonFinancing,
    }
    return policy_classes.get(policy_name)
