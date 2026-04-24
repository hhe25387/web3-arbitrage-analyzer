"""Human-readable report generation."""

import config
from models import ArbitrageOpportunity, ExchangePrice, SimulationResult
from utils import format_money, format_percent, round_price


def build_report(
    prices: list[ExchangePrice],
    opportunity: ArbitrageOpportunity | None,
    simulation: SimulationResult | None,
    symbol: str | None = None,
    mode: str | None = None,
) -> str:
    """Build a clean text report for terminal output."""

    lines: list[str] = []
    divider = "=" * 78
    thin_divider = "-" * 78
    report_symbol = symbol or (prices[0].symbol if prices else config.DEFAULT_SYMBOL)
    report_mode = mode or config.DATA_MODE
    web3_mode = _web3_source_label(simulation, report_mode)

    lines.append(divider)
    lines.append("DELAY-AWARE CROSS-EXCHANGE ARBITRAGE ANALYZER")
    lines.append("Hackathon demo: theoretical spread vs realistic execution")
    lines.append(divider)
    lines.append(
        f"Symbol: {report_symbol} | Mode: {report_mode.upper()} | "
        f"Trade size: {format_money(config.TRADE_SIZE_USDT)}"
    )
    lines.append(
        f"Delay: {config.EXECUTION_DELAY_SECONDS}s | "
        f"Slippage: {config.SLIPPAGE_RATE * 100:.2f}% per side | "
        f"Gas/Web3: {web3_mode}"
    )
    lines.append(
        "Web3 component: gas cost is included because onchain execution can erase "
        "small arbitrage spreads."
    )
    lines.append("Safety note: no real trading is performed. This is only an analysis and simulation tool.")
    lines.append("")
    lines.append("1) Market Snapshot")
    lines.append(thin_divider)
    lines.append(f"{'Exchange / Source':<26} {'Price':>14}  {'Source type':<24} {'Timestamp'}")
    lines.append(thin_divider)

    for price in sorted(prices, key=lambda item: item.price):
        lines.append(
            f"{price.exchange:<26} {format_money(price.price):>14}  "
            f"{price.source_type:<24} {price.timestamp.strftime('%Y-%m-%d %H:%M:%S UTC')}"
        )

    if opportunity is None or simulation is None:
        lines.append("")
        lines.append("FINAL VERDICT")
        lines.append(thin_divider)
        lines.append("[NOT REALISTICALLY EXECUTABLE]")
        lines.append("No positive theoretical spread was found before fees.")
        return "\n".join(lines)

    fee = simulation.fee_estimate
    success_stats = simulation.success_probability_summary or {}
    lines.extend(
        [
            "",
            "2) Theoretical Arbitrage",
            thin_divider,
            f"Buy low on:              {opportunity.buy_exchange}",
            f"Sell high on:            {opportunity.sell_exchange}",
            f"Buy price:               {format_money(opportunity.buy_price)}",
            f"Sell price:              {format_money(opportunity.sell_price)}",
            f"Gross spread:            {format_money(opportunity.gross_spread)}",
            f"Gross spread percent:    {format_percent(opportunity.gross_spread_percent)}",
            f"Theoretical gross profit: {format_money(opportunity.theoretical_gross_profit)}",
            "",
            "3) Execution Stress Test",
            thin_divider,
            f"Delayed buy price:        {format_money(round_price(simulation.delayed_buy_price))}",
            f"Delayed sell price:       {format_money(round_price(simulation.delayed_sell_price))}",
            f"Delay cost estimate:      {format_money(simulation.delay_cost)}",
            f"Slippage cost estimate:   {format_money(simulation.slippage_cost)}",
            "",
            "4) Cost Breakdown",
            thin_divider,
            f"Buy trading fee:          {format_money(fee.buy_trading_fee)}",
            f"Sell trading fee:         {format_money(fee.sell_trading_fee)}",
            f"Withdrawal fee:           {format_money(fee.withdrawal_fee)}",
            f"Transfer cost:            {format_money(fee.transfer_cost)}",
            f"Gas cost:                 {format_money(fee.gas_cost)} ({fee.gas_source})",
            f"Total fees:               {format_money(fee.total_fees)}",
            "",
            "5) Success Probability",
            thin_divider,
            f"Success probability:      {success_stats.get('success_probability', 0.0) * 100:.2f}%",
            f"Average simulated net profit: {format_money(float(success_stats.get('average_net_profit', 0.0)))}",
            f"Best case profit:         {format_money(float(success_stats.get('best_case_profit', 0.0)))}",
            f"Worst case profit:        {format_money(float(success_stats.get('worst_case_profit', 0.0)))}",
            f"Monte Carlo runs:         {int(success_stats.get('simulations', 0))}",
            "This probability is not financial advice. It is a simulation based on simplified volatility assumptions.",
            "",
            "FINAL VERDICT",
            thin_divider,
            f"[{simulation.verdict.upper()}]",
            f"Net expected profit:      {format_money(simulation.net_expected_profit)}",
            "",
            "Why this matters:",
            simulation.explanation,
            divider,
        ]
    )

    return "\n".join(lines)


def print_report(report_text: str) -> None:
    """Print a generated report to the terminal."""

    print(report_text)


def _web3_source_label(
    simulation: SimulationResult | None,
    mode: str,
) -> str:
    """Describe whether web3 values are mock, live, or mixed."""

    if simulation is not None and simulation.fee_estimate.gas_source != "not used":
        return simulation.fee_estimate.gas_source

    if mode.lower() == "live":
        return "mock gas estimate"

    return "mock estimates"
