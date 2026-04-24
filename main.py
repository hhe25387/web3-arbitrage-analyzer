"""Entry point for the Delay-Aware Cross-Exchange Arbitrage Analyzer."""

import config
from arbitrage import find_best_opportunity
from models import ArbitrageOpportunity, ExchangePrice, SimulationResult
from plotter import create_plots
from price_fetcher import get_prices
from report import build_report, print_report
from simulator import simulate_execution


def analyze_market(
    symbol: str = config.SYMBOL,
    mode: str = config.DATA_MODE,
    trade_size_usdt: float | None = None,
) -> tuple[list[ExchangePrice], ArbitrageOpportunity | None, SimulationResult | None]:
    """Run the core analysis workflow and return structured results."""

    prices = get_prices(symbol=symbol, mode=mode)
    opportunity = find_best_opportunity(
        prices=prices,
        trade_size_usdt=trade_size_usdt if trade_size_usdt is not None else config.TRADE_SIZE_USDT,
    )
    simulation = simulate_execution(opportunity, mode=mode) if opportunity else None
    return prices, opportunity, simulation


def run_analysis(symbol: str = config.SYMBOL, mode: str = config.DATA_MODE) -> None:
    """Run the full arbitrage analysis workflow and print the final report."""

    prices, opportunity, simulation = analyze_market(symbol=symbol, mode=mode)

    report_text = build_report(
        prices=prices,
        opportunity=opportunity,
        simulation=simulation,
        symbol=symbol,
        mode=mode,
    )
    print_report(report_text)

    if config.SAVE_PLOTS:
        create_plots(
            prices=prices,
            opportunity=opportunity,
            simulation=simulation,
            output_path=config.PLOT_FILE_NAME,
        )


if __name__ == "__main__":
    run_analysis()
