"""Execution-delay and slippage simulation."""

import random

import config
from fees import estimate_fees
from models import ArbitrageOpportunity, SimulationResult


def simulate_execution(
    opportunity: ArbitrageOpportunity,
    mode: str = config.DATA_MODE,
) -> SimulationResult:
    """Simulate realistic arbitrage execution after delay, fees, and slippage.

    The simple stress model assumes the buy price moves up and the sell price
    moves down during execution delay. That is intentionally conservative and
    helps explain why visible spreads often disappear before settlement.
    """

    drift_rate = config.EXECUTION_DELAY_SECONDS * config.PRICE_DRIFT_PER_SECOND_RATE
    delayed_buy_price = opportunity.buy_price * (1 + drift_rate)
    delayed_sell_price = opportunity.sell_price * (1 - drift_rate)

    buy_after_slippage = delayed_buy_price * (1 + config.SLIPPAGE_RATE)
    sell_after_slippage = delayed_sell_price * (1 - config.SLIPPAGE_RATE)

    original_token_amount = opportunity.trade_size_usdt / opportunity.buy_price
    realistic_token_amount = opportunity.trade_size_usdt / buy_after_slippage
    realistic_sell_value = realistic_token_amount * sell_after_slippage
    realistic_gross_profit = realistic_sell_value - opportunity.trade_size_usdt

    fee_estimate = estimate_fees(opportunity, mode=mode)
    net_expected_profit = realistic_gross_profit - fee_estimate.total_fees

    delay_cost = opportunity.theoretical_gross_profit - (
        original_token_amount * (delayed_sell_price - delayed_buy_price)
    )
    slippage_cost = (
        realistic_token_amount * delayed_sell_price
        - realistic_sell_value
    ) + (
        opportunity.trade_size_usdt
        - realistic_token_amount * delayed_buy_price
    )

    verdict = (
        "Potentially profitable"
        if net_expected_profit > 0
        else "Not realistically executable"
    )
    explanation = _build_explanation(
        theoretical_profit=opportunity.theoretical_gross_profit,
        net_expected_profit=net_expected_profit,
        total_fees=fee_estimate.total_fees,
    )
    success_probability_summary = estimate_success_probability(
        opportunity=opportunity,
        trade_size=opportunity.trade_size_usdt,
        total_fees=fee_estimate.total_fees,
        delay_seconds=config.EXECUTION_DELAY_SECONDS,
        slippage_rate=config.SLIPPAGE_RATE,
    )

    return SimulationResult(
        delayed_buy_price=delayed_buy_price,
        delayed_sell_price=delayed_sell_price,
        slippage_cost=max(slippage_cost, 0.0),
        delay_cost=max(delay_cost, 0.0),
        fee_estimate=fee_estimate,
        net_expected_profit=net_expected_profit,
        verdict=verdict,
        explanation=explanation,
        success_probability_summary=success_probability_summary,
    )


def estimate_success_probability(
    opportunity: ArbitrageOpportunity,
    trade_size: float,
    total_fees: float,
    delay_seconds: int,
    slippage_rate: float,
    simulations: int = 500,
) -> dict[str, float | int]:
    """Estimate the chance that an opportunity stays profitable.

    This Monte Carlo simulation uses a simple volatility assumption based on
    delay. It randomly moves the buy and sell prices, applies slippage, and
    subtracts total fees to estimate how often the final trade remains positive.
    """

    volatility = min(0.0005 * delay_seconds, 0.02)
    profitable_runs = 0
    net_profits: list[float] = []

    for _ in range(simulations):
        buy_move = random.uniform(-volatility, volatility)
        sell_move = random.uniform(-volatility, volatility)

        simulated_buy_price = opportunity.buy_price * (1 + buy_move)
        simulated_sell_price = opportunity.sell_price * (1 + sell_move)

        buy_after_slippage = simulated_buy_price * (1 + slippage_rate)
        sell_after_slippage = simulated_sell_price * (1 - slippage_rate)

        token_amount = trade_size / buy_after_slippage
        sell_value = token_amount * sell_after_slippage
        net_profit = (sell_value - trade_size) - total_fees
        net_profits.append(net_profit)

        if net_profit > 0:
            profitable_runs += 1

    success_probability = profitable_runs / simulations if simulations > 0 else 0.0
    average_net_profit = sum(net_profits) / simulations if simulations > 0 else 0.0
    best_case_profit = max(net_profits) if net_profits else 0.0
    worst_case_profit = min(net_profits) if net_profits else 0.0

    return {
        "success_probability": success_probability,
        "average_net_profit": average_net_profit,
        "best_case_profit": best_case_profit,
        "worst_case_profit": worst_case_profit,
        "simulations": simulations,
    }


def _build_explanation(
    theoretical_profit: float,
    net_expected_profit: float,
    total_fees: float,
) -> str:
    """Create a short explanation for the final verdict."""

    if net_expected_profit > 0:
        return (
            "The opportunity remains positive after conservative delay, slippage, "
            "and fee assumptions. It may still fail if order books are thin or "
            "prices move faster than expected."
        )

    return (
        "The visible spread is smaller than the combined execution costs. "
        f"Theoretical profit was about {theoretical_profit:.2f} USDT, but fees "
        f"alone were about {total_fees:.2f} USDT before delay and slippage."
    )
