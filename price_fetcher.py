"""Fetch exchange prices in mock mode or live mode."""

from typing import Any

import config
from models import ExchangePrice
from utils import current_utc_time, print_warning, safe_float
from web3_data import build_dex_exchange_price


def get_mock_prices(symbol: str) -> list[ExchangePrice]:
    """Return hardcoded but realistic exchange prices for a demo run."""

    normalized_symbol = symbol.upper().replace("/", "")

    if normalized_symbol == "ETHUSDT":
        base_prices = {
            "Coinbase": 3212.10,
            "Kraken": 3208.85,
            "CoinGecko ETH/USD": 3210.25,
        }
    else:
        base_prices = {
            "Coinbase": 64205.75,
            "Kraken": 64180.10,
            "CoinGecko BTC/USD": 64192.30,
        }

    prices = [
        ExchangePrice(
            exchange=name,
            symbol=normalized_symbol,
            price=price,
            timestamp=current_utc_time(),
            source_type="mock centralized exchange",
        )
        for name, price in base_prices.items()
    ]

    if config.INCLUDE_WEB3_SOURCE:
        reference_price = sum(base_prices.values()) / len(base_prices)
        prices.append(build_dex_exchange_price(normalized_symbol, reference_price, mode="mock"))

    return prices


def fetch_binance_price(symbol: str) -> ExchangePrice:
    """Deprecated placeholder kept for backwards compatibility."""

    raise RuntimeError("Binance is no longer used in live mode.")


def fetch_coinbase_price() -> ExchangePrice:
    """Fetch the latest BTC/USD spot price from Coinbase."""

    requests = _import_requests()
    response = requests.get(
        config.COINBASE_SPOT_URL,
        timeout=config.REQUEST_TIMEOUT,
        headers=_request_headers(),
    )
    response.raise_for_status()
    data: dict[str, Any] = response.json()
    amount = safe_float(data.get("data", {}).get("amount"))

    if amount <= 0:
        raise ValueError("Coinbase returned an invalid BTC/USD spot price.")

    return ExchangePrice(
        exchange="Coinbase",
        symbol="BTCUSDT",
        price=amount,
        timestamp=current_utc_time(),
        source_type="live centralized exchange",
    )


def fetch_kraken_price() -> ExchangePrice:
    """Fetch the latest XBT/USD ticker price from Kraken."""

    requests = _import_requests()
    response = requests.get(
        config.KRAKEN_TICKER_URL,
        timeout=config.REQUEST_TIMEOUT,
        headers=_request_headers(),
    )
    response.raise_for_status()
    data: dict[str, Any] = response.json()

    if data.get("error"):
        raise ValueError(f"Kraken returned an error: {data['error']}")

    result = data.get("result", {})
    ticker = result.get("XXBTZUSD") or next(iter(result.values()), {})
    last_trade_price = safe_float(ticker.get("c", [0])[0])

    if last_trade_price <= 0:
        raise ValueError("Kraken returned an invalid XBT/USD price.")

    return ExchangePrice(
        exchange="Kraken",
        symbol="BTCUSDT",
        price=last_trade_price,
        timestamp=current_utc_time(),
        source_type="live centralized exchange",
    )


def fetch_coingecko_price() -> ExchangePrice:
    """Fetch the latest BTC/USD market price from CoinGecko."""

    requests = _import_requests()
    response = requests.get(
        config.COINGECKO_URL,
        params={"ids": "bitcoin,ethereum", "vs_currencies": "usd"},
        timeout=config.REQUEST_TIMEOUT,
        headers=_request_headers(),
    )
    response.raise_for_status()
    data: dict[str, Any] = response.json()
    bitcoin_data = data.get("bitcoin", {})
    price = safe_float(bitcoin_data.get("usd"))

    if price <= 0:
        raise ValueError("CoinGecko returned an invalid bitcoin USD price.")

    return ExchangePrice(
        exchange="CoinGecko BTC/USD",
        symbol="BTCUSDT",
        price=price,
        timestamp=current_utc_time(),
        source_type="live market data",
    )


def get_live_prices(symbol: str) -> list[ExchangePrice]:
    """Fetch live prices from public APIs and return them as ExchangePrice objects.

    If one source fails, this function skips only that source. If every source
    fails, the caller can fall back to mock data.
    """

    normalized_symbol = symbol.upper().replace("/", "")
    live_prices: list[ExchangePrice] = []

    for source_name, fetch_function in (
        ("Coinbase", fetch_coinbase_price),
        ("Kraken", fetch_kraken_price),
        ("CoinGecko", fetch_coingecko_price),
    ):
        try:
            live_prices.append(fetch_function())
        except Exception as error:
            print_warning(f"{source_name} live price request failed: {error}")

    if not live_prices:
        raise RuntimeError("All live price sources failed.")

    if config.INCLUDE_WEB3_SOURCE:
        reference_price = sum(item.price for item in live_prices) / len(live_prices)
        live_prices.append(build_dex_exchange_price(normalized_symbol, reference_price, mode="live"))

    return live_prices


def get_prices(symbol: str, mode: str) -> list[ExchangePrice]:
    """Return live prices when requested, otherwise use mock data.

    If all live requests fail, this function prints a warning and falls back to
    mock data so the project remains safe and demo-friendly.
    """

    normalized_symbol = symbol.upper().replace("/", "")

    if mode.lower() == "mock":
        return get_mock_prices(normalized_symbol)

    try:
        return get_live_prices(normalized_symbol)
    except Exception as error:
        print_warning(f"Live price request failed: {error}")
        print_warning("Falling back to mock price data.")
        return get_mock_prices(normalized_symbol)


def fetch_prices(symbol: str, mode: str = config.DATA_MODE) -> list[ExchangePrice]:
    """Backward-compatible wrapper around get_prices."""

    return get_prices(symbol=symbol, mode=mode)


def _import_requests() -> Any:
    """Import requests inside live mode so mock mode works without dependencies."""

    try:
        import requests
    except ImportError as error:
        raise RuntimeError("The 'requests' package is required for live mode.") from error

    return requests


def _request_headers() -> dict[str, str]:
    """Return a small User-Agent header for public API calls."""

    return {"User-Agent": config.USER_AGENT}
