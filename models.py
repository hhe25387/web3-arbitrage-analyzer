"""Dataclasses used by the arbitrage analyzer."""

from dataclasses import dataclass
from datetime import datetime


@dataclass
class ExchangePrice:
    """A single market price from one exchange or onchain source."""

    exchange: str
    symbol: str
    price: float
    timestamp: datetime
    source_type: str = "mock data"
    is_web3: bool = False
    chain: str = ""
    dex: str = ""
    liquidity_usd: float = 0.0
    pair_address: str = ""
    url: str = ""


@dataclass
class ArbitrageOpportunity:
    """The best theoretical buy/sell arbitrage opportunity before fees."""

    symbol: str
    buy_exchange: str
    sell_exchange: str
    buy_price: float
    sell_price: float
    gross_spread: float
    gross_spread_percent: float
    trade_size_usdt: float
    theoretical_gross_profit: float


@dataclass
class FeeEstimate:
    """Estimated costs that reduce an arbitrage trade's profit."""

    buy_trading_fee: float
    sell_trading_fee: float
    withdrawal_fee: float
    transfer_cost: float
    gas_cost: float
    total_fees: float
    gas_source: str = "not used"


@dataclass
class SimulationResult:
    """Realistic execution estimate after delay, slippage, and fees."""

    delayed_buy_price: float
    delayed_sell_price: float
    slippage_cost: float
    delay_cost: float
    fee_estimate: FeeEstimate
    net_expected_profit: float
    verdict: str
    explanation: str
    success_probability_summary: dict[str, float | int] | None = None
