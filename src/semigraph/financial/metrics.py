from dataclasses import dataclass
from typing import Literal


@dataclass(frozen=True)
class MetricDefinition:
    name: str
    statement: Literal["income", "balance", "cash_flow"]
    aliases: tuple[str, ...]  # เรียงจาก preferred → fallback
    unit: str
    cash_outflow: bool = False


METRICS: tuple[MetricDefinition, ...] = (
    MetricDefinition(
        "revenue",
        "income",
        (
            "RevenueFromContractWithCustomerExcludingAssessedTax",
            "Revenues",
            "SalesRevenueNet",
            "RevenueFromContractWithCustomerIncludingAssessedTax"
        ),
        "USD",
    ),
    MetricDefinition(
        "cost_of_revenue",
        "income",
        ("CostOfRevenue", "CostOfGoodsAndServicesSold"),
        "USD",
    ),
    MetricDefinition("gross_profit", "income", ("GrossProfit",), "USD"),
    MetricDefinition(
        "research_and_development",
        "income",
        ("ResearchAndDevelopmentExpense",),
        "USD",
    ),
    MetricDefinition(
        "operating_income",
        "income",
        ("OperatingIncomeLoss",),
        "USD",
    ),
    MetricDefinition("net_income", "income", ("NetIncomeLoss","ProfitLoss"), "USD"),
    MetricDefinition(
        "diluted_eps",
        "income",
        ("EarningsPerShareDiluted",),
        "USD/share",
    ),
    MetricDefinition(
        "cash_and_equivalents",
        "balance",
        (
            "CashAndCashEquivalentsAtCarryingValue",
            "CashCashEquivalentsRestrictedCashAndRestrictedCashEquivalents",
        ),
        "USD",
    ),
    MetricDefinition("current_assets", "balance", ("AssetsCurrent",), "USD"),
    MetricDefinition("total_assets", "balance", ("Assets",), "USD"),
    MetricDefinition(
        "current_liabilities",
        "balance",
        ("LiabilitiesCurrent",),
        "USD",
    ),
    MetricDefinition("total_liabilities", "balance", ("Liabilities",), "USD"),
    MetricDefinition(
        "stockholders_equity",
        "balance",
        (
            "StockholdersEquity",
            "StockholdersEquityIncludingPortionAttributableToNoncontrollingInterest",
        ),
        "USD",
    ),
    MetricDefinition(
        "operating_cash_flow",
        "cash_flow",
        ("NetCashProvidedByUsedInOperatingActivities",),
        "USD",
    ),
    MetricDefinition(
        "capital_expenditure",
        "cash_flow",
        (
            "PaymentsToAcquirePropertyPlantAndEquipment",
            "PaymentsForAdditionsToPropertyPlantAndEquipment",
        ),
        "USD",
        cash_outflow=True,
    ),
)


def local_concept_name(concept: str) -> str:
    """Remove namespace only"""
    if ":" in concept:
        return concept.rsplit(":", 1)[-1]
    if concept.startswith("us-gaap_"):
        return concept.removeprefix("us-gaap_")
    return concept



ALIAS_TO_METRIC = {
    alias: definition
    for definition in METRICS
    for alias in definition.aliases
}
