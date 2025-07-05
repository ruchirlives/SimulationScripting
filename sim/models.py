"""Core models for the simulation engine."""

from __future__ import annotations

import pandas as pd
import simpy

from .constants import NIRATE, NITHRESHOLD, EMPLOYERPENSIONRATE, PENSIONFTETHRESHOLD
from .utils import get_current_month, printtimestamp


class Worker:
    """Represents a worker in the simulation."""

    def __init__(self, **kwargs):
        self.position = kwargs.get("position", "undesignated")
        self.name = kwargs.get("name", "staff member")
        self.age = kwargs.get("age", 49)
        self.department = kwargs.get("department", "unspecified")
        self.mobilephone = kwargs.get("mobilephone", "not assigned")
        self.linemanagerrate = kwargs.get("linemanagerrate", 0)
        self.employerpensionrate = kwargs.get("employerpensionrate", EMPLOYERPENSIONRATE)
        self.fte_salary = kwargs.get("salary", 0)
        self.fte = kwargs.get("fte", 1)
        self.salary = self.fte * self.fte_salary

    def info(self):
        """Print worker information."""
        for attr, value in self.__dict__.items():
            print(f"{attr} : {value}")

    def getbreakdown(self, month: int):
        """Get cost breakdown for a specific month."""
        salary = self.getMonthSalary(month)
        data = [
            {"step": month, "item": "salary", "budget": salary, "type": "1. Staffing", "description": "Monthly salary"},
            {"step": month, "item": "ni", "budget": self.getNI(salary), "type": "1. Staffing", "description": "National Insurance"},
            {"step": month, "item": "pension", "budget": self.getPension(salary, self.fte), "type": "1. Staffing", "description": "Pension contribution"},
        ]
        return data

    def getSalaryCost(self) -> float:
        """Get total annual salary cost including NI and pension."""
        monthlysalary = self.salary / 12
        monthlycost = monthlysalary + self.getNI(monthlysalary) + self.getPension(monthlysalary, self.fte)
        return monthlycost * 12

    def getMonthSalaryCost(self, month: int) -> float:
        """Get monthly salary cost."""
        return self.getSalaryCost() / 12

    def getMonthSalary(self, month: int) -> float:
        """Get monthly salary."""
        return self.salary / 12

    def getNI(self, monthlySalary: float) -> float:
        """Calculate National Insurance contribution."""
        monthlyThreshold = NITHRESHOLD / 7 * 365 / 12
        if self.salary > monthlyThreshold:
            ni = max(0, (monthlySalary - monthlyThreshold)) * NIRATE
        else:
            ni = 0
        return ni

    def getPension(self, salary: float, fte: float) -> float:
        """Calculate pension contribution."""
        if fte > PENSIONFTETHRESHOLD:
            pension = salary * self.employerpensionrate
        else:
            pension = 0
        return pension


class ConsolidatedAccount:
    """Manages financial transactions for the portfolio."""

    def __init__(self, env: simpy.Environment):
        self.env = env
        self.total_capital = 0
        self.total_payments = 0
        self.total_income = 0
        self.balance = 0
        self.register = []

    def update(self, transaction: dict):
        """Update account with a new transaction."""
        transaction["amount"] = float(transaction["amount"])
        if transaction["type"] == "expenditure":
            self.total_payments += transaction["amount"]
        if transaction["type"] == "income":
            self.total_income += transaction["amount"]
            transaction["amount"] = -transaction["amount"]
        self.balance = self.total_income - self.total_payments
        transaction["date"] = self.env.now
        transaction["balance"] = self.balance
        self.register.append(transaction)

    def report(self):
        """Print account summary."""
        print(
            f"Consolidated Account Report: Payments to date: {self.total_payments:.2f}, "
            f"Income to date: {self.total_income:.2f}, Balance: {self.balance:.2f}"
        )
