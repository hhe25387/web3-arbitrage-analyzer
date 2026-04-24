# 🚀 Web3 Arbitrage Reality Analyzer

A Web3-aware arbitrage analyzer that compares centralized exchange (CEX) prices with decentralized exchange (DEX) liquidity, and determines whether a theoretical arbitrage opportunity is actually executable in real-world conditions.

---

## 💡 Key Idea

Most arbitrage tools only show **theoretical price differences**.

👉 This project answers a more important question:

> **Can the arbitrage actually survive real execution?**

It models:
- ⏱ Delay (latency)
- 📉 Slippage
- ⛽ Gas fees (on-chain)
- 💸 Trading & transfer costs

---

## 🧠 Features

- 🔗 Live Web3 data from DexScreener (Uniswap / DEX liquidity)
- 🏦 CEX price comparison (Coinbase, Kraken, etc.)
- 📊 Theoretical arbitrage detection
- ⚙️ Execution stress testing (delay + slippage)
- 💰 Full cost breakdown (fees, gas, transfer)
- 🎲 Monte Carlo simulation for success probability
- 🚨 Final verdict: EXECUTE or DO NOT EXECUTE

---

## 📸 Demo

![App Screenshot](arbitrage_summary.png)

---

## 🧪 Example Insight

Even when a price difference exists:

- Theoretical profit: +$0.65  
- Total fees: ~$25  
- Final expected profit: **negative**

👉 **Conclusion: Not realistically executable**

---

## 🛠 Tech Stack

- Python
- Streamlit
- DexScreener API (Web3 / DEX data)
- Pandas
- Matplotlib

---

## ▶️ How to Run

```bash
pip install -r requirements.txt
streamlit run app.py
