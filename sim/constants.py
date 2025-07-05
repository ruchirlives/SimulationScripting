"""Constants used throughout the simulation engine."""

ALL_MONTHS = [
    "jan", "feb", "mar", "apr", "may", "jun",
    "jul", "aug", "sep", "oct", "nov", "dec",
]

NIRATE = 0.138
NITHRESHOLD = 175
EMPLOYERPENSIONRATE = 0.09
PENSIONFTETHRESHOLD = 0.2
REALLIVINGWAGE = 12

# Data stores for FCR and support lookup
FCRDATA: list[dict] = []
SUPPORTDATA: list[dict] = []
