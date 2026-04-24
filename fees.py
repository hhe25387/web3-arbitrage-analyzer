"""Fee estimation for realistic arbitrage calculations."""

import config
from models import ArbitrageOpportunity, FeeEstimate
from web3_data import get_gas_cost_usdt


def estimate_fees(
    opportunity: ArbitrageOpportunity,
    mode: str = config.DATA_MODE,
) -> FeeEstimate:
    """Estimate all simple costs for an arbitrage execution.

    Assumptions:
    - The trader pays taker fees on both the buy and sell legs.
    - Withdrawal and transfer costs are flat USDT estimates.
    - Gas is included when either side touches a web3/onchain source.
    - In live mode, gas price is requested from Etherscan when an API key exists.
    """

    buy_trading_fee = opportunity.trade_size_usdt * config.TAKER_TRADING_FEE_RATE
    expected_sell_value = opportunity.trade_size_usdt + opportunity.theoretical_gross_profit
    sell_trading_fee = expected_sell_value * config.TAKER_TRADING_FEE_RATE
    gas_cost = 0.0
    gas_source = "not used"

    if "Uniswap" in opportunity.buy_exchange or "Uniswap" in opportunity.sell_exchange:
        gas_cost, gas_source = get_gas_cost_usdt(mode=mode)

    total_fees = (
        buy_trading_fee
        + sell_trading_fee
        + config.WITHDRAWAL_FEE_USDT
        + config.TRANSFER_COST_USDT
        + gas_cost
    )

    return FeeEstimate(
        buy_trading_fee=buy_trading_fee,
        sell_trading_fee=sell_trading_fee,
        withdrawal_fee=config.WITHDRAWAL_FEE_USDT,
        transfer_cost=config.TRANSFER_COST_USDT,
        gas_cost=gas_cost,
        total_fees=total_fees,
        gas_source=gas_source,
    )
