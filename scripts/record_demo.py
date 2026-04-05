#!/usr/bin/env python3
"""
Generate asciinema .cast file from demo output, then convert to GIF.

Usage:
    python scripts/record_demo.py
"""

from __future__ import annotations

import io
import json
import os
import sys
import time

sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding="utf-8", errors="replace")

# Force demo mode
os.environ["DEMO_MODE"] = "true"
os.environ["OZON_CLIENT_ID"] = ""
os.environ["OZON_API_KEY"] = ""
os.environ["LOG_LEVEL"] = "ERROR"

sys.path.insert(0, os.path.join(os.path.dirname(__file__), "..", "src"))

import asyncio
from ozon_mcp_server.demo import DemoOzonClient  # noqa: E402


CYAN = "\033[36m"
GREEN = "\033[32m"
YELLOW = "\033[33m"
WHITE = "\033[97m"
DIM = "\033[2m"
BOLD = "\033[1m"
RESET = "\033[0m"


class CastRecorder:
    """Records terminal output in asciicast v2 format."""

    def __init__(self, width: int = 100, height: int = 35):
        self.width = width
        self.height = height
        self.events: list[tuple[float, str, str]] = []
        self.start_time = time.monotonic()

    def write(self, text: str, delay: float = 0.0) -> None:
        if delay > 0:
            time.sleep(delay)
        elapsed = time.monotonic() - self.start_time
        self.events.append((elapsed, "o", text))

    def writeln(self, text: str = "", delay: float = 0.0) -> None:
        self.write(text + "\r\n", delay)

    def pause(self, seconds: float = 0.6) -> None:
        time.sleep(seconds)

    def save(self, path: str) -> None:
        header = {
            "version": 2,
            "width": self.width,
            "height": self.height,
            "timestamp": int(time.time()),
            "env": {"SHELL": "/bin/bash", "TERM": "xterm-256color"},
            "title": "Ozon Seller MCP Server - Demo",
        }
        with open(path, "w", encoding="utf-8") as f:
            f.write(json.dumps(header) + "\n")
            for ts, etype, data in self.events:
                f.write(json.dumps([round(ts, 6), etype, data]) + "\n")


async def record() -> None:
    client = DemoOzonClient()
    rec = CastRecorder(width=105, height=40)

    # Title
    rec.writeln()
    rec.writeln(f"  {BOLD}{WHITE}Ozon Seller MCP Server{RESET} — Demo")
    rec.writeln(f"  {DIM}13 MCP tools | DEMO_MODE=true | No API keys needed{RESET}")
    rec.pause(1.0)

    # === 1. Product List ===
    rec.writeln()
    rec.writeln(f"  {BOLD}{CYAN}--- 1. Product Management ---{RESET}", delay=0.3)
    rec.writeln()
    rec.writeln(f"  {YELLOW}> get_product_list{DIM}(visibility=\"ALL\"){RESET}", delay=0.3)
    rec.pause(0.5)

    resp = await client.request("/v2/product/list")
    for item in resp["result"]["items"]:
        rec.writeln(f"    {GREEN}{item['offer_id']:<25} (ID: {item['product_id']}){RESET}", delay=0.08)
    rec.writeln(f"    {WHITE}{resp['result']['total']} products total{RESET}", delay=0.1)
    rec.pause(0.8)

    # === 2. Product Info ===
    rec.writeln()
    rec.writeln(f"  {YELLOW}> get_product_info{DIM}(product_id=987210451){RESET}", delay=0.3)
    rec.pause(0.5)

    resp = await client.request("/v2/product/info", {"product_id": 987210451})
    p = resp["result"]
    rec.writeln(f"    {WHITE}{p['name']}{RESET}", delay=0.1)
    rec.writeln(f"    {GREEN}Price: {p['price']} RUB  (was {p['old_price']} RUB){RESET}", delay=0.08)
    rec.writeln(f"    {GREEN}Stock: {p['stocks']['present']} available, {p['stocks']['reserved']} reserved{RESET}", delay=0.08)
    rec.writeln(f"    {GREEN}Rating: {p['rating']}  |  Status: {p['status']['state']}{RESET}", delay=0.08)
    rec.pause(0.8)

    # === 3. Stock on Warehouses ===
    rec.writeln()
    rec.writeln(f"  {YELLOW}> get_stock_on_warehouses{DIM}(product_ids=[987210451]){RESET}", delay=0.3)
    rec.pause(0.5)

    resp = await client.request("/v1/product/info/stocks")
    row = resp["result"]["rows"][0]
    for s in row["stocks"]:
        rec.writeln(f"    {GREEN}{s['warehouse_name']:30} {s['type'].upper():4} {s['present']:>4} pcs ({s['reserved']} reserved){RESET}", delay=0.08)
    rec.pause(0.8)

    # === 4. FBS Orders ===
    rec.writeln()
    rec.writeln(f"  {BOLD}{CYAN}--- 2. Order Tracking ---{RESET}", delay=0.3)
    rec.writeln()
    rec.writeln(f"  {YELLOW}> get_fbs_orders{DIM}(status=\"awaiting_packaging\"){RESET}", delay=0.3)
    rec.pause(0.5)

    resp = await client.request("/v3/posting/fbs/list", {"filter": {"status": "awaiting_packaging"}})
    for o in resp["result"]["postings"]:
        prod = o["products"][0]
        city = o["analytics_data"]["city"]
        payout = o["financial_data"]["products"][0]["payout"]
        rec.writeln(f"    {GREEN}#{o['posting_number']}{RESET}", delay=0.08)
        rec.writeln(f"    {GREEN}  {prod['name'][:50]} x{prod['quantity']}  ->  {city}{RESET}", delay=0.06)
        rec.writeln(f"    {GREEN}  Payout: {payout:,.0f} RUB{RESET}", delay=0.06)
    rec.pause(0.8)

    # === 5. Analytics ===
    rec.writeln()
    rec.writeln(f"  {BOLD}{CYAN}--- 3. Sales Analytics ---{RESET}", delay=0.3)
    rec.writeln()
    rec.writeln(f"  {YELLOW}> get_analytics{DIM}(date_from=\"2026-03-29\", date_to=\"2026-04-03\"){RESET}", delay=0.3)
    rec.pause(0.5)

    resp = await client.request("/v1/analytics/data")
    data = resp["result"]
    for row in data["data"]:
        date = row["dimensions"][0]["name"]
        rev, orders, views = row["metrics"]
        bar = "#" * int(rev / 25000)
        rec.writeln(f"    {GREEN}{date}  {rev:>12,.0f} RUB  {int(orders):>3} orders  {bar}{RESET}", delay=0.1)
    totals = data["totals"]
    rec.writeln(f"    {BOLD}{WHITE}TOTAL     {totals[0]:>12,.0f} RUB  {int(totals[1]):>3} orders{RESET}", delay=0.15)
    rec.pause(0.8)

    # === 6. Finance ===
    rec.writeln()
    rec.writeln(f"  {YELLOW}> get_finance_report{DIM}(date_from=\"2026-04-01\", date_to=\"2026-04-03\"){RESET}", delay=0.3)
    rec.pause(0.5)

    resp = await client.request("/v3/finance/transaction/list")
    for op in resp["result"]["operations"]:
        item = op["items"][0]["name"][:45]
        rec.writeln(f"    {GREEN}{op['operation_date'][:10]}  {item}{RESET}", delay=0.08)
        rec.writeln(f"    {GREEN}  Sale: {op['accruals_for_sale']:>10,.0f}  Commission: {op['sale_commission']:>10,.0f}  Payout: {op['amount']:>10,.0f}{RESET}", delay=0.06)
    rec.pause(0.8)

    # === 7. Warehouses ===
    rec.writeln()
    rec.writeln(f"  {BOLD}{CYAN}--- 4. Warehouses ---{RESET}", delay=0.3)
    rec.writeln()
    rec.writeln(f"  {YELLOW}> get_warehouse_list(){RESET}", delay=0.3)
    rec.pause(0.4)

    resp = await client.request("/v1/warehouse/list")
    for wh in resp["result"]:
        rec.writeln(f"    {GREEN}{wh['warehouse_id']}  {wh['name']:35}  [{wh['status']}]{RESET}", delay=0.1)
    rec.pause(0.8)

    # === 8. Write operations ===
    rec.writeln()
    rec.writeln(f"  {BOLD}{CYAN}--- 5. Write Operations ---{RESET}", delay=0.3)
    rec.writeln()
    rec.writeln(f"  {YELLOW}> update_prices{DIM}(product_id=987210451, price=\"17490.00\"){RESET}", delay=0.3)
    rec.pause(0.4)
    rec.writeln(f"    {GREEN}[OK] Price updated -> 17,490 RUB{RESET}", delay=0.1)

    rec.writeln()
    rec.writeln(f"  {YELLOW}> update_stocks{DIM}(product_id=987210451, stock=200){RESET}", delay=0.3)
    rec.pause(0.4)
    rec.writeln(f"    {GREEN}[OK] Stock updated -> 200 units{RESET}", delay=0.1)

    rec.writeln()
    rec.writeln(f"  {YELLOW}> create_product{DIM}(name=\"Sony WH-1000XM5\", price=\"29990.00\"){RESET}", delay=0.3)
    rec.pause(0.4)
    rec.writeln(f"    {GREEN}[OK] Product created, task_id=348901562{RESET}", delay=0.1)

    rec.pause(1.0)

    # === Summary ===
    rec.writeln()
    rec.writeln(f"  {BOLD}{CYAN}------------------------------------------------------------{RESET}", delay=0.1)
    rec.writeln(f"  {BOLD}{WHITE}  [OK] All 13 MCP tools demonstrated{RESET}", delay=0.2)
    rec.writeln(f"  {DIM}  DEMO_MODE=true | No API keys | No Docker | No databases{RESET}", delay=0.1)
    rec.writeln(f"  {BOLD}{CYAN}------------------------------------------------------------{RESET}", delay=0.1)
    rec.writeln()
    rec.pause(2.0)

    # Save
    cast_path = os.path.join(os.path.dirname(__file__), "..", "demo.cast")
    rec.save(cast_path)
    print(f"Saved: {os.path.abspath(cast_path)}")
    print(f"Events: {len(rec.events)}")
    print(f"Duration: {rec.events[-1][0]:.1f}s")
    print()
    print("To convert to GIF:")
    print(f"  agg {os.path.abspath(cast_path)} demo.gif --font-size 14 --speed 1.2")
    print()
    print("Or view in terminal:")
    print(f"  asciinema play {os.path.abspath(cast_path)}")
    print()
    print("Or upload to asciinema.org:")
    print(f"  asciinema upload {os.path.abspath(cast_path)}")


if __name__ == "__main__":
    asyncio.run(record())
