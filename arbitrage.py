"""Find theoretical cross-exchange arbitrage opportunities."""

from models import ArbitrageOpportunity, ExchangePrice


def find_best_opportunity(
    prices: list[ExchangePrice],
    trade_size_usdt: float,
) -> ArbitrageOpportunity | None:
    """Find the best buy-low/sell-high opportunity before fees.

    Returns None if there are fewer than two prices or if the best spread is not
    positive.
    """

    if len(prices) < 2:
        return None

    best_buy = min(prices, key=lambda item: item.price)
    best_sell = max(prices, key=lambda item: item.price)
    gross_spread = best_sell.price - best_buy.price

    if gross_spread <= 0:
        return None

    gross_spread_percent = (gross_spread / best_buy.price) * 100
    token_amount = trade_size_usdt / best_buy.price
    theoretical_gross_profit = token_amount * gross_spread

    return ArbitrageOpportunity(
        symbol=best_buy.symbol,
        buy_exchange=best_buy.exchange,
        sell_exchange=best_sell.exchange,
        buy_price=best_buy.price,
        sell_price=best_sell.price,
        gross_spread=gross_spread,
        gross_spread_percent=gross_spread_percent,
        trade_size_usdt=trade_size_usdt,
        theoretical_gross_profit=theoretical_gross_profit,
    )
