# ERC-4337 Bundler Monitor

A live research tool that monitors Ethereum ERC-4337 bundlers for fairness and censorship patterns.

## What it does

ERC-4337 introduced "smart wallets" to Ethereum — wallets that don't need seed phrases and can pay gas in any token. These wallets use special middlemen called **bundlers** to submit transactions. 

This tool investigates: **do bundlers treat all UserOperations fairly, or do they reorder, delay, or censor transactions for profit?**

## How it works

- Connects directly to Ethereum mainnet via Alchemy
- Monitors the ERC-4337 EntryPoint contract for `UserOperationEvent` logs in real time
- Extracts bundler addresses, sender addresses, block timestamps, and transaction hashes
- Stores data in a local SQLite database, building up over time
- Displays live analysis on a Streamlit dashboard

## Dashboard features

- Total UserOps
4. Run the collector: `python collect_userops.py`
5. Run the dashboard: `streamlit run dashboard.py`

## Research context

This project investigates a largely unstudied security surface in the ERC-4337 ecosystem. Unlike the standard Ethereum mempool, the bundler mempool has limited transparency tooling. This tool aims to provide independent, on-chain verified monitoring of bundler behavior.