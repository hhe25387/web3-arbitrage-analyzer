"""Streamlit frontend for the Delay-Aware Cross-Exchange Arbitrage Analyzer."""

from contextlib import contextmanager
from pathlib import Path
from typing import Iterator

import streamlit as st

import config
from main import analyze_market
from models import ArbitrageOpportunity, ExchangePrice, SimulationResult
from utils import format_money, format_percent, round_price


@contextmanager
def temporary_settings(
    trade_size_usdt: float,
    delay_seconds: int,
    slippage_percent: float,
) -> Iterator[None]:
    """Temporarily override runtime settings for the Streamlit session."""

    original_trade_size = config.TRADE_SIZE_USDT
    original_delay = config.EXECUTION_DELAY_SECONDS
    original_slippage = config.SLIPPAGE_RATE

    config.TRADE_SIZE_USDT = trade_size_usdt
    config.EXECUTION_DELAY_SECONDS = delay_seconds
    config.SLIPPAGE_RATE = slippage_percent / 100

    try:
        yield
    finally:
        config.TRADE_SIZE_USDT = original_trade_size
        config.EXECUTION_DELAY_SECONDS = original_delay
        config.SLIPPAGE_RATE = original_slippage


def build_market_rows(prices: list[ExchangePrice]) -> list[dict[str, str]]:
    """Convert exchange prices into table rows for Streamlit."""

    return [
        {
            "Exchange / Source": price.exchange,
            "Price": format_money(price.price),
            "Source Type": price.source_type,
            "Chain": price.chain or "-",
            "DEX": price.dex or "-",
            "Liquidity USD": format_money(price.liquidity_usd) if price.liquidity_usd > 0 else "-",
            "Timestamp": price.timestamp.strftime("%Y-%m-%d %H:%M:%S UTC"),
        }
        for price in sorted(prices, key=lambda item: item.price)
    ]


def show_theoretical_section(opportunity: ArbitrageOpportunity) -> None:
    """Render the theoretical arbitrage section."""

    st.subheader("Theoretical Arbitrage Before Costs")
    col1, col2 = st.columns(2)
    col1.metric("Best Buy Exchange", opportunity.buy_exchange)
    col2.metric("Best Sell Exchange", opportunity.sell_exchange)

    st.table(
        [
            {"Metric": "Buy price", "Value": format_money(opportunity.buy_price)},
            {"Metric": "Sell price", "Value": format_money(opportunity.sell_price)},
            {"Metric": "Gross spread", "Value": format_money(opportunity.gross_spread)},
            {"Metric": "Gross spread percent", "Value": format_percent(opportunity.gross_spread_percent)},
            {"Metric": "Trade size", "Value": format_money(opportunity.trade_size_usdt)},
            {
                "Metric": "Theoretical gross profit",
                "Value": format_money(opportunity.theoretical_gross_profit),
            },
        ]
    )


def show_execution_section(simulation: SimulationResult) -> None:
    """Render the delay and slippage stress test section."""

    st.subheader("Execution Stress Test After Delay and Slippage")
    st.table(
        [
            {"Metric": "Delayed buy price", "Value": format_money(round_price(simulation.delayed_buy_price))},
            {"Metric": "Delayed sell price", "Value": format_money(round_price(simulation.delayed_sell_price))},
            {"Metric": "Delay cost estimate", "Value": format_money(simulation.delay_cost)},
            {"Metric": "Slippage cost estimate", "Value": format_money(simulation.slippage_cost)},
        ]
    )


def show_cost_section(simulation: SimulationResult) -> None:
    """Render the cost breakdown section."""

    fee = simulation.fee_estimate
    st.subheader("Execution Cost Breakdown")
    st.table(
        [
            {"Metric": "Buy trading fee", "Value": format_money(fee.buy_trading_fee)},
            {"Metric": "Sell trading fee", "Value": format_money(fee.sell_trading_fee)},
            {"Metric": "Withdrawal fee", "Value": format_money(fee.withdrawal_fee)},
            {"Metric": "Transfer cost", "Value": format_money(fee.transfer_cost)},
            {"Metric": "Gas cost", "Value": f"{format_money(fee.gas_cost)} ({fee.gas_source})"},
            {"Metric": "Total fees", "Value": format_money(fee.total_fees)},
        ]
    )


def show_success_probability_section(simulation: SimulationResult) -> None:
    """Render the Monte Carlo success probability section."""

    summary = simulation.success_probability_summary or {}
    probability = float(summary.get("success_probability", 0.0))

    st.subheader("Monte Carlo Success Probability")
    col1, col2, col3 = st.columns(3)
    col1.metric("Success probability", f"{probability * 100:.2f}%")
    col2.metric("Average net profit", format_money(float(summary.get("average_net_profit", 0.0))))
    col3.metric("Simulations", int(summary.get("simulations", 0)))

    lower_left, lower_right = st.columns(2)
    lower_left.metric("Best case profit", format_money(float(summary.get("best_case_profit", 0.0))))
    lower_right.metric("Worst case profit", format_money(float(summary.get("worst_case_profit", 0.0))))

    if probability < 0.30:
        st.error("Low execution confidence")
    elif probability < 0.70:
        st.warning("Uncertain execution confidence")
    else:
        st.success("High execution confidence")

    st.info(
        "This probability is not financial advice. It is a simulation based on "
        "simplified volatility assumptions."
    )


def show_top_verdict_dashboard(
    opportunity: ArbitrageOpportunity,
    simulation: SimulationResult,
) -> None:
    """Render the top-level decision dashboard."""

    summary = simulation.success_probability_summary or {}
    probability = float(summary.get("success_probability", 0.0))
    total_fees = simulation.fee_estimate.total_fees
    recommendation, confidence, card_style = get_decision_summary(simulation, probability)

    st.markdown(
        f"""
        <div style="
            background:{card_style['background']};
            border:1px solid {card_style['border']};
            border-radius:10px;
            padding:18px 20px;
            margin:8px 0 18px 0;
        ">
            <div style="font-size:0.95rem; font-weight:700; color:{card_style['label']};">
                FINAL RECOMMENDATION
            </div>
            <div style="font-size:1.8rem; font-weight:800; color:{card_style['title']}; margin-top:6px;">
                {recommendation}
            </div>
            <div style="font-size:1rem; color:{card_style['text']}; margin-top:6px;">
                Net expected profit: {format_money(simulation.net_expected_profit)} |
                Success probability: {probability * 100:.2f}% |
                Execution confidence: {confidence}
            </div>
        </div>
        """,
        unsafe_allow_html=True,
    )

    st.markdown("**Why this result?**")
    for bullet in build_reason_bullets(opportunity, simulation, total_fees):
        st.write(f"- {bullet}")


def show_key_metrics(opportunity: ArbitrageOpportunity, simulation: SimulationResult) -> None:
    """Render the top key-metrics row."""

    fee = simulation.fee_estimate
    col1, col2, col3, col4 = st.columns(4)
    col1.metric("Gross spread %", format_percent(opportunity.gross_spread_percent))
    col2.metric("Theoretical gross profit", format_money(opportunity.theoretical_gross_profit))
    col3.metric("Total fees", format_money(fee.total_fees))
    col4.metric("Net expected profit", format_money(simulation.net_expected_profit))


def show_profit_chart(opportunity: ArbitrageOpportunity, simulation: SimulationResult) -> None:
    """Render a small chart comparing gross and net profit."""

    st.subheader("Gross Profit vs Net Profit Chart")
    chart_data = {
        "Profit (USD)": {
            "Theoretical Gross Profit": opportunity.theoretical_gross_profit,
            "Net Expected Profit": simulation.net_expected_profit,
        }
    }
    st.bar_chart(chart_data, use_container_width=True)


def show_market_snapshot(
    prices: list[ExchangePrice],
    opportunity: ArbitrageOpportunity | None,
) -> None:
    """Render the market snapshot with best buy and best sell summary."""

    st.subheader("Market Snapshot")
    if opportunity is not None:
        col1, col2 = st.columns(2)
        col1.info(f"Best Buy: {opportunity.buy_exchange} at {format_money(opportunity.buy_price)}")
        col2.info(f"Best Sell: {opportunity.sell_exchange} at {format_money(opportunity.sell_price)}")

    st.dataframe(build_market_rows(prices), use_container_width=True, hide_index=True)


def get_decision_summary(
    simulation: SimulationResult,
    probability: float,
) -> tuple[str, str, dict[str, str]]:
    """Return the final recommendation, confidence label, and card colors."""

    if simulation.net_expected_profit > 0 and probability >= 0.70:
        return (
            "EXECUTE",
            "HIGH",
            {
                "background": "#e8f7ee",
                "border": "#67b26f",
                "label": "#1f6b35",
                "title": "#14532d",
                "text": "#1f4d2d",
            },
        )

    if simulation.net_expected_profit > 0 or probability >= 0.30:
        return (
            "DO NOT EXECUTE",
            "MEDIUM",
            {
                "background": "#fff5e6",
                "border": "#f3b562",
                "label": "#9a5a00",
                "title": "#8a4b00",
                "text": "#7a4a12",
            },
        )

    return (
        "DO NOT EXECUTE",
        "LOW",
        {
            "background": "#fdecec",
            "border": "#e27d7d",
            "label": "#a01f1f",
            "title": "#8b1e1e",
            "text": "#6f1d1d",
        },
    )


def build_reason_bullets(
    opportunity: ArbitrageOpportunity,
    simulation: SimulationResult,
    total_fees: float,
) -> list[str]:
    """Create simple bullet points explaining the final decision."""

    bullets = [
        f"The theoretical gross profit is {format_money(opportunity.theoretical_gross_profit)}, while total execution fees are {format_money(total_fees)}.",
        "Delay and slippage reduce the effective buy/sell execution prices before the trade is completed.",
    ]

    if simulation.net_expected_profit <= 0:
        bullets.append("Gas, transfer costs, and trading fees push the final expected profit below zero.")
    else:
        bullets.append("Even after execution frictions, the expected profit remains positive in this simplified model.")

    return bullets


def show_optional_plot() -> None:
    """Display the saved matplotlib summary image if it exists."""

    plot_path = Path(config.PLOT_FILE_NAME)
    if plot_path.exists():
        st.subheader("Saved Summary Plot")
        st.image(str(plot_path), caption="arbitrage_summary.png", use_container_width=True)


def main() -> None:
    """Render the Streamlit application."""

    st.set_page_config(
        page_title="Delay-Aware Cross-Exchange Arbitrage Analyzer",
        layout="wide",
    )

    st.title("Delay-Aware Cross-Exchange Arbitrage Analyzer")
    st.write(
        "This tool compares theoretical crypto arbitrage with realistic execution after "
        "delay, slippage, fees, and gas costs."
    )
    st.write(
        "Most arbitrage tools only show theoretical spreads. This app checks whether "
        "the opportunity survives real execution frictions such as gas, slippage, latency, "
        "and trading fees."
    )
    st.info("Safety note: This tool does not perform real trading.")
    st.info(
        "This app compares centralized exchange prices with live decentralized exchange "
        "liquidity from DexScreener. It estimates whether a theoretical CEX/DEX arbitrage "
        "opportunity can survive real execution frictions such as gas, slippage, fees, and delay."
    )

    st.sidebar.header("Controls")
    mode = st.sidebar.selectbox("Data mode", options=["LIVE", "MOCK"], index=0)
    symbol = st.sidebar.selectbox("Symbol", options=["BTCUSDT"], index=0)
    trade_size = st.sidebar.number_input("Trade size in USD", min_value=100.0, value=float(config.TRADE_SIZE_USDT), step=100.0)
    delay_seconds = st.sidebar.slider("Delay seconds", min_value=0, max_value=120, value=int(config.EXECUTION_DELAY_SECONDS))
    slippage_percent = st.sidebar.slider(
        "Slippage percent per side",
        min_value=0.0,
        max_value=2.0,
        value=float(config.SLIPPAGE_RATE * 100),
        step=0.05,
    )

    st.caption("Live mode uses public read-only APIs. If live requests fail, the app falls back to mock data.")
    run_clicked = st.button("Run Analysis", type="primary")

    if not run_clicked:
        st.info("Choose settings in the sidebar and click Run Analysis.")
        return

    try:
        with temporary_settings(
            trade_size_usdt=trade_size,
            delay_seconds=delay_seconds,
            slippage_percent=slippage_percent,
        ):
            prices, opportunity, simulation = analyze_market(
                symbol=symbol,
                mode=mode.lower(),
                trade_size_usdt=trade_size,
            )
    except Exception as error:
        st.error(f"Analysis failed: {error}")
        return

    if opportunity is None or simulation is None:
        show_market_snapshot(prices, opportunity)
        st.warning("No positive theoretical spread was found before fees.")
        st.info("This tool does not place trades. It only analyzes and simulates potential arbitrage conditions.")
        show_optional_plot()
        return

    show_top_verdict_dashboard(opportunity, simulation)
    show_key_metrics(opportunity, simulation)
    show_profit_chart(opportunity, simulation)
    show_market_snapshot(prices, opportunity)
    show_theoretical_section(opportunity)
    show_execution_section(simulation)
    show_cost_section(simulation)
    show_success_probability_section(simulation)
    show_optional_plot()


if __name__ == "__main__":
    main()
