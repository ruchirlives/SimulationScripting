"""Simulation engine for portfolio and project management.

This package provides a comprehensive simulation framework for managing
portfolios of projects with staffing, policies, and financial tracking.
"""

from .constants import (
    ALL_MONTHS,
    NIRATE,
    NITHRESHOLD,
    EMPLOYERPENSIONRATE,
    PENSIONFTETHRESHOLD,
    REALLIVINGWAGE,
    FCRDATA,
    SUPPORTDATA,
)
from .models import Worker, ConsolidatedAccount
from .portfolio import Portfolio
from .project import Project
from .policies import Policy, FullCostRecovery, Grant, Subsidy, Rename, Finance, CarbonFinancing
from .utils import (
    get_current_month,
    printtimestamp,
    pivotbudget,
    parseYAML,
    yaml_to_react_flow_json,
    react_flow_to_yaml,
)

# For backward compatibility
worker = Worker
project = Project

__all__ = [
    # Core classes
    "Portfolio",
    "Project",
    "Worker",
    "ConsolidatedAccount",
    # Policies
    "Policy",
    "FullCostRecovery",
    "Grant",
    "Subsidy",
    "Rename",
    "Finance",
    "CarbonFinancing",
    # Utilities
    "get_current_month",
    "printtimestamp",
    "pivotbudget",
    "parseYAML",
    "yaml_to_react_flow_json",
    "react_flow_to_yaml",
    # Constants
    "ALL_MONTHS",
    "NIRATE",
    "NITHRESHOLD",
    "EMPLOYERPENSIONRATE",
    "PENSIONFTETHRESHOLD",
    "REALLIVINGWAGE",
    "FCRDATA",
    "SUPPORTDATA",
    # Backward compatibility
    "worker",
    "project",
]
