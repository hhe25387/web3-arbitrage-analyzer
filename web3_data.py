"""Web3 and onchain data helpers.

This module keeps the web3 part read-only and safe. In live mode, it can call
free public APIs such as Etherscan and DexScreener. If a request fails, the
project falls back to clearly labeled mock data so the demo still works.
"""

from typing import Any

import config
from models import ExchangePrice
from utils import current_utc_time, print_warning, safe_float


def estimate_gas_cost_usdt(
    gas_units: int,
    gas_price_gwei: float,
    eth_price_usdt: float,
) -> float:
    """Estimate an Ethereum transaction gas cost in USDT.

    Formula:
        gas_units * gas_price_gwei * 1e-9 ETH/gwei * ETH price in USDT
    """

    gas_cost_eth = gas_units * gas_price_gwei * 1e-9
    return gas_cost_eth * eth_price_usdt


def get_live_gas_fee_usd() -> tuple[float, str]:
    """Return a live Etherscan gas estimate or a mock fallback.

    The function uses the optional ETHERSCAN_API_KEY environment variable. If
    no key is present or the request fails, it returns a mock gas estimate.
    """

    if not config.ETHERSCAN_API_KEY:
        return get_mock_gas_fee_usd(), "mock gas estimate"

    try:
        requests = _import_requests()
        response = requests.get(
            config.ETHERSCAN_GAS_URL,
            params={
                "module": "gastracker",
                "action": "gasoracle",
                "apikey": config.ETHERSCAN_API_KEY,
            },
            timeout=config.REQUEST_TIMEOUT,
            headers=_request_headers(),
        )
        response.raise_for_status()
        data: dict[str, Any] = response.json()
        result = data.get("result", {})

        gas_price_gwei = safe_float(result.get("ProposeGasPrice"))
        if gas_price_gwei <= 0:
            gas_price_gwei = safe_float(result.get("SafeGasPrice"))
        if gas_price_gwei <= 0:
            raise ValueError("Etherscan gas oracle returned no usable gas price.")

        eth_price_usd = fetch_live_eth_price_usd()
        gas_fee_usd = estimate_gas_cost_usdt(
            gas_units=config.DEX_SWAP_GAS_UNITS,
            gas_price_gwei=gas_price_gwei,
            eth_price_usdt=eth_price_usd,
        )
        return gas_fee_usd, "live Etherscan gas estimate"
    except Exception as error:
        print_warning(f"Etherscan gas request failed: {error}")
        print_warning("Falling back to mock gas estimate.")
        return get_mock_gas_fee_usd(), "mock gas estimate"


def get_gas_cost_usdt(mode: str = config.DATA_MODE) -> tuple[float, str]:
    """Return a gas-cost estimate used by the fee calculator."""

    if mode.lower() == "live":
        return get_live_gas_fee_usd()

    return get_mock_gas_fee_usd(), "mock gas estimate"


def get_mock_gas_fee_usd() -> float:
    """Return the beginner-friendly mock gas estimate used in mock mode."""

    return estimate_gas_cost_usdt(
        gas_units=config.DEX_SWAP_GAS_UNITS,
        gas_price_gwei=config.MOCK_GAS_PRICE_GWEI,
        eth_price_usdt=config.MOCK_ETH_PRICE_USDT,
    )


def fetch_live_eth_price_usd() -> float:
    """Fetch ETH/USD from CoinGecko or fall back to the configured mock value."""

    try:
        requests = _import_requests()
        response = requests.get(
            config.COINGECKO_URL,
            params={"ids": "ethereum", "vs_currencies": "usd"},
            timeout=config.REQUEST_TIMEOUT,
            headers=_request_headers(),
        )
        response.raise_for_status()
        data: dict[str, Any] = response.json()
        eth_price = safe_float(data.get("ethereum", {}).get("usd"))
        if eth_price > 0:
            return eth_price
    except Exception as error:
        print_warning(f"Could not fetch live ETH price for gas conversion: {error}")

    return config.MOCK_ETH_PRICE_USDT


def get_mock_dex_quote(symbol: str, reference_price: float) -> ExchangePrice:
    """Return a deterministic DEX quote near the centralized exchange price.

    TODO: Replace this with a real Uniswap, Curve, or oracle quote using an RPC
    provider. A real implementation would ask the DEX how many output tokens are
    received for a sample input amount, then convert the result into USDT price.
    """

    # The DEX quote is intentionally a little different from CEX prices so the
    # report can show why web3 opportunities need gas-aware analysis.
    dex_price = reference_price * 1.0018
    return ExchangePrice(
        exchange="Uniswap via DexScreener",
        symbol=symbol,
        price=round(dex_price, 2),
        timestamp=current_utc_time(),
        source_type="fallback mock Web3 data",
        is_web3=True,
        chain="ethereum",
        dex="uniswap-v3",
    )


def fetch_dexscreener_price(symbol: str) -> dict[str, str | float]:
    """Fetch live DEX price data from DexScreener.

    The search query is intentionally simple and beginner-readable. For this
    hackathon version, BTC uses the free DexScreener search endpoint and then
    picks the most relevant pair by scoring Ethereum and Uniswap pairs higher,
    while still considering liquidity.
    """

    requests = _import_requests()
    search_query = _dexscreener_query(symbol)
    response = requests.get(
        config.DEXSCREENER_SEARCH_URL,
        params={"q": search_query},
        timeout=config.REQUEST_TIMEOUT,
        headers=_request_headers(),
    )
    response.raise_for_status()
    data: dict[str, Any] = response.json()
    pairs: list[dict[str, Any]] = data.get("pairs", [])

    if not pairs:
        raise ValueError("DexScreener returned no DEX pairs.")

    best_pair = max(pairs, key=_dexscreener_pair_score)
    price_usd = safe_float(best_pair.get("priceUsd"))

    if price_usd <= 0:
        raise ValueError("DexScreener pair is missing a usable priceUsd value.")

    liquidity_usd = safe_float(best_pair.get("liquidity", {}).get("usd"))
    chain_id = str(best_pair.get("chainId", ""))
    dex_id = str(best_pair.get("dexId", ""))
    pair_address = str(best_pair.get("pairAddress", ""))
    url = str(best_pair.get("url", ""))

    return {
        "exchange": "Uniswap via DexScreener",
        "price": price_usd,
        "source_type": "live Web3 DEX data",
        "chain": chain_id,
        "dex": dex_id,
        "liquidity_usd": liquidity_usd,
        "pair_address": pair_address,
        "url": url,
    }


def build_dex_exchange_price(symbol: str, reference_price: float, mode: str) -> ExchangePrice:
    """Return a live DexScreener price when possible, otherwise a mock fallback."""

    normalized_symbol = symbol.upper().replace("/", "")

    if mode.lower() != "live":
        mock_quote = get_mock_dex_quote(normalized_symbol, reference_price)
        mock_quote.source_type = "mock Web3 DEX data"
        return mock_quote

    try:
        dex_data = fetch_dexscreener_price(normalized_symbol)
        return ExchangePrice(
            exchange=str(dex_data["exchange"]),
            symbol=normalized_symbol,
            price=float(dex_data["price"]),
            timestamp=current_utc_time(),
            source_type=str(dex_data["source_type"]),
            is_web3=True,
            chain=str(dex_data["chain"]),
            dex=str(dex_data["dex"]),
            liquidity_usd=float(dex_data["liquidity_usd"]),
            pair_address=str(dex_data["pair_address"]),
            url=str(dex_data["url"]),
        )
    except Exception as error:
        print_warning(f"DexScreener DEX request failed: {error}")
        return get_mock_dex_quote(normalized_symbol, reference_price)


def _dexscreener_query(symbol: str) -> str:
    """Convert the project symbol into a simple DexScreener search query."""

    normalized_symbol = symbol.upper().replace("/", "")
    if normalized_symbol == "BTCUSDT":
        return "BTC/USDC"
    if normalized_symbol == "ETHUSDT":
        return "ETH/USDC"
    return normalized_symbol


def _dexscreener_pair_score(pair: dict[str, Any]) -> tuple[int, int, float]:
    """Score DexScreener pairs so Ethereum Uniswap pools are preferred."""

    chain_id = str(pair.get("chainId", "")).lower()
    dex_id = str(pair.get("dexId", "")).lower()
    liquidity_usd = safe_float(pair.get("liquidity", {}).get("usd"))
    prefers_ethereum = 1 if chain_id == "ethereum" else 0
    prefers_uniswap = 1 if "uniswap" in dex_id else 0
    return (prefers_ethereum, prefers_uniswap, liquidity_usd)


def _import_requests() -> Any:
    """Import requests only when live web3 data is needed."""

    try:
        import requests
    except ImportError as error:
        raise RuntimeError("The 'requests' package is required for live web3 mode.") from error

    return requests


def _request_headers() -> dict[str, str]:
    """Return a small User-Agent header for public API calls."""

    return {"User-Agent": config.USER_AGENT}
