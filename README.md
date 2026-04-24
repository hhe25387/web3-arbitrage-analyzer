# Delay-Aware Cross-Exchange Arbitrage Analyzer

Delay-Aware Cross-Exchange Arbitrage Analyzer is a beginner-friendly Python and Streamlit project that shows why visible crypto arbitrage spreads often disappear once realistic execution costs are included.

## Problem Statement

Cross-exchange crypto arbitrage looks attractive when one market shows a lower
price and another shows a higher price. In practice, the spread can vanish
before execution finishes because of latency, slippage, trading fees, transfer
costs, and onchain gas.

## Why This Matters

Hackathon judges and users can quickly understand an important real-world idea:
theoretical arbitrage is not the same as executable arbitrage. A spread that
looks profitable on paper may fail once the trade is delayed, partially filled,
or routed through onchain infrastructure.

## Features

- Live market data from Coinbase, Kraken, and CoinGecko
- Live DEX/Web3 liquidity data from DexScreener
- Safe mock fallback when live APIs fail
- Cross-exchange price comparison
- Best buy / best sell arbitrage identification
- Delay simulation
- Slippage simulation
- Fee breakdown
- Web3 gas cost estimate with live-or-mock labeling
- Clean CLI report through `main.py`
- Interactive Streamlit frontend through `app.py`
- Read-only analysis only, with no wallet signing and no trading

## Tech Stack

- Python
- Streamlit
- Requests
- Matplotlib

## Installation

1. Create and activate a virtual environment if you want:

```bash
python3 -m venv .venv
source .venv/bin/activate
```

2. Install dependencies:

```bash
pip install -r requirements.txt
```

Optional:

- Set `ETHERSCAN_API_KEY` if you want live Etherscan gas estimates.

```bash
export ETHERSCAN_API_KEY=your_key_here
```

## How to Run the CLI Version

```bash
python3 main.py
```

This prints a hackathon-friendly terminal report with:

- market snapshot
- theoretical arbitrage
- execution stress test
- cost breakdown
- final verdict

## How to Run the Streamlit Version

```bash
streamlit run app.py
```

The Streamlit app provides:

- sidebar controls for mode, trade size, delay, and slippage
- market snapshot table
- theoretical arbitrage section
- execution stress test
- cost breakdown
- final verdict and explanation

## Live APIs

The live mode uses public read-only APIs:

- Coinbase spot price API  
  `https://api.coinbase.com/v2/prices/BTC-USD/spot`
- Kraken ticker API  
  `https://api.kraken.com/0/public/Ticker?pair=XBTUSD`
- CoinGecko simple price API  
  `https://api.coingecko.com/api/v3/simple/price?ids=bitcoin,ethereum&vs_currencies=usd`
- DexScreener DEX search API  
  `https://api.dexscreener.com/latest/dex/search?q=BTC/USDC`

For web3-related cost estimation, the project can also use:

- Etherscan gas oracle  
  `https://api.etherscan.io/api?module=gastracker&action=gasoracle`

No trading, wallet signing, or private-key handling is implemented.

## Mock Fallback

The project is designed to stay demo-ready even when public APIs fail.

- If one live market source fails, that source is skipped.
- If all live market sources fail, the program falls back to mock prices.
- If Etherscan gas data is unavailable or no API key is set, the program falls
  back to a mock gas estimate.

This makes the demo stable for presentations, judging sessions, and offline use.

## Web3 Component

The web3 component is in `web3_data.py`.

It currently includes:

- live decentralized exchange liquidity and price discovery through DexScreener
- Ethereum gas cost estimation
- optional live gas estimate from Etherscan
- ETH/USD conversion through CoinGecko with fallback
- fallback mock Web3 data if DexScreener is unavailable

This part is essential because the project does not only compare centralized
exchange prices. It also checks whether a real CEX/DEX opportunity survives
when decentralized liquidity, gas cost, transfer cost, and execution friction
are included. In other words, the Web3 component is not decorative; it changes
the actual arbitrage decision.

## Example Output

CLI output highlights:

- whether price data is live or mock
- whether gas estimate is live or mock
- best buy and sell venues
- gross spread vs realistic profit
- final verdict

Example verdict:

```text
[NOT REALISTICALLY EXECUTABLE]
Net expected profit: $-26.93
```

## Limitations

- The project analyzes only a small set of public price sources.
- It uses ticker prices, not full order book depth.
- DexScreener provides aggregated DEX market data, not a guaranteed onchain swap execution quote.
- Gas cost is an estimate, not a guaranteed transaction cost.
- It is an analysis and simulation tool only.
- No real trading is performed.

## Future Improvements

- Add direct read-only onchain swap quotes from a DEX router or RPC provider
- Add more symbols and exchange support
- Use order book depth for more realistic slippage
- Save analysis results to CSV or JSON
- Add historical comparisons and charts in the web app
