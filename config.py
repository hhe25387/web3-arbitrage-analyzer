"""Configuration values for the arbitrage analyzer.

This file keeps assumptions in one place so beginners can change the project
without hunting through the business logic.
"""

import os

# Set to "mock" for deterministic demo data, or "live" for public API calls.
DATA_MODE: str = "live"

# Symbol used by the first live version.
SYMBOL: str = "BTCUSDT"

# Centralized exchanges used by the first live version.
EXCHANGES: list[str] = ["Coinbase", "Kraken", "CoinGecko BTC/USD"]

# A DEX/onchain quote source is represented separately because it has gas costs.
INCLUDE_WEB3_SOURCE: bool = True
WEB3_SOURCE_NAME: str = "Uniswap V3 (estimated)"

# API settings.
REQUEST_TIMEOUT: int = 10
USER_AGENT: str = "DelayAwareArbitrageAnalyzer/1.0"
COINBASE_SPOT_URL: str = "https://api.coinbase.com/v2/prices/BTC-USD/spot"
KRAKEN_TICKER_URL: str = "https://api.kraken.com/0/public/Ticker?pair=XBTUSD"
COINGECKO_URL: str = "https://api.coingecko.com/api/v3/simple/price"
DEXSCREENER_SEARCH_URL: str = "https://api.dexscreener.com/latest/dex/search"
ETHERSCAN_GAS_URL: str = "https://api.etherscan.io/api"
ETHERSCAN_API_KEY: str | None = os.getenv("ETHERSCAN_API_KEY")

# Trade sizing.
TRADE_SIZE_USDT: float = 1_000.0

# Fee assumptions. Values are deliberately simple for hackathon explainability.
TAKER_TRADING_FEE_RATE: float = 0.0010  # 0.10% charged when buying or selling.
WITHDRAWAL_FEE_USDT: float = 5.00
TRANSFER_COST_USDT: float = 2.00

# Web3 / onchain assumptions.
MOCK_GAS_PRICE_GWEI: float = 28.0
MOCK_ETH_PRICE_USDT: float = 3_200.0
DEX_SWAP_GAS_UNITS: int = 180_000

# Execution simulation assumptions.
EXECUTION_DELAY_SECONDS: int = 20
PRICE_DRIFT_PER_SECOND_RATE: float = 0.00002  # 0.002% per second.
SLIPPAGE_RATE: float = 0.0015  # 0.15% on both buy and sell execution prices.

# Plot output settings.
SAVE_PLOTS: bool = True
PLOT_FILE_NAME: str = "arbitrage_summary.png"

# Backward-compatible aliases so the rest of the beginner project stays simple.
RUN_MODE: str = DATA_MODE
DEFAULT_SYMBOL: str = SYMBOL
API_TIMEOUT_SECONDS: int = REQUEST_TIMEOUT
