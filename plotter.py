"""Optional matplotlib visualizations for the arbitrage analyzer."""

from pathlib import Path

from models import ArbitrageOpportunity, ExchangePrice, SimulationResult
from utils import print_warning


def create_plots(
    prices: list[ExchangePrice],
    opportunity: ArbitrageOpportunity | None,
    simulation: SimulationResult | None,
    output_path: str,
) -> None:
    """Create a simple PNG summary chart if matplotlib is available."""

    if opportunity is None or simulation is None:
        return

    try:
        import matplotlib.pyplot as plt
    except ImportError:
        print_warning("matplotlib is not installed, so plots were skipped.")
        return

    exchange_names = [item.exchange for item in prices]
    exchange_prices = [item.price for item in prices]

    figure, axes = plt.subplots(1, 2, figsize=(12, 5))

    axes[0].bar(exchange_names, exchange_prices, color="#4C78A8")
    axes[0].set_title("Exchange Price Comparison")
    axes[0].set_ylabel("Price (USDT)")
    axes[0].tick_params(axis="x", rotation=25)

    profit_labels = ["Theoretical gross", "Net expected"]
    profit_values = [
        opportunity.theoretical_gross_profit,
        simulation.net_expected_profit,
    ]
    colors = ["#59A14F", "#E15759" if simulation.net_expected_profit < 0 else "#59A14F"]
    axes[1].bar(profit_labels, profit_values, color=colors)
    axes[1].axhline(0, color="black", linewidth=0.8)
    axes[1].set_title("Gross Profit vs Net Profit")
    axes[1].set_ylabel("Profit (USDT)")

    figure.tight_layout()
    Path(output_path).parent.mkdir(parents=True, exist_ok=True)
    figure.savefig(output_path, dpi=140)
    plt.close(figure)
