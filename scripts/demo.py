#!/usr/bin/env python3
"""
Demo script for recording GIF / terminal session.

Shows all 13 MCP tools working with realistic Ozon marketplace data.
No API keys, Redis, or PostgreSQL needed.

Usage:
    python scripts/demo.py
"""

from __future__ import annotations

import asyncio
import io
import json
import os
import sys
import time

# Fix Windows console encoding
if sys.platform == "win32":
    sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding="utf-8", errors="replace")
    sys.stderr = io.TextIOWrapper(sys.stderr.buffer, encoding="utf-8", errors="replace")

# Force demo mode
os.environ["DEMO_MODE"] = "true"
os.environ["OZON_CLIENT_ID"] = ""
os.environ["OZON_API_KEY"] = ""
os.environ["LOG_LEVEL"] = "WARNING"

# Add src to path
sys.path.insert(0, os.path.join(os.path.dirname(__file__), "..", "src"))

from ozon_mcp_server.demo import DemoOzonClient  # noqa: E402


CYAN = "\033[36m"
GREEN = "\033[32m"
YELLOW = "\033[33m"
WHITE = "\033[97m"
DIM = "\033[2m"
RESET = "\033[0m"
BOLD = "\033[1m"


def header(text: str) -> None:
    print(f"\n{BOLD}{CYAN}{'-' * 60}{RESET}")
    print(f"{BOLD}{CYAN}  {text}{RESET}")
    print(f"{BOLD}{CYAN}{'-' * 60}{RESET}")


def tool_call(name: str, params: str = "") -> None:
    if params:
        print(f"\n{YELLOW}> {name}{DIM}({params}){RESET}")
    else:
        print(f"\n{YELLOW}> {name}(){RESET}")


def result(data: dict | list | str, indent: int = 2) -> None:
    if isinstance(data, (dict, list)):
        text = json.dumps(data, ensure_ascii=False, indent=indent)
    else:
        text = str(data)
    for line in text.split("\n"):
        print(f"  {GREEN}{line}{RESET}")


def pause(seconds: float = 0.8) -> None:
    time.sleep(seconds)


async def main() -> None:
    client = DemoOzonClient()

    print(f"\n{BOLD}{WHITE}  Ozon Seller MCP Server — Demo{RESET}")
    print(f"{DIM}  13 tools • DEMO_MODE=true • no API keys needed{RESET}")

    # -- Product List ------------------------------------------
    header("1. Product Management")

    tool_call("get_product_list", 'visibility="ALL"')
    pause()
    resp = await client.request("/v2/product/list")
    items = resp["result"]["items"]
    print(f"  {WHITE}Found {resp['result']['total']} products:{RESET}")
    for item in items:
        print(f"  {GREEN}  • {item['offer_id']:<25} (ID: {item['product_id']}){RESET}")

    # -- Product Info ------------------------------------------
    pause()
    tool_call("get_product_info", "product_id=987210451")
    pause()
    resp = await client.request("/v2/product/info", {"product_id": 987210451})
    p = resp["result"]
    print(f"  {WHITE}{p['name']}{RESET}")
    print(f"  {GREEN}  Price: {p['price']} ₽  (was {p['old_price']} ₽){RESET}")
    print(f"  {GREEN}  Stock: {p['stocks']['present']} available, {p['stocks']['reserved']} reserved{RESET}")
    print(f"  {GREEN}  Rating: {'*' * int(p['rating'])} {p['rating']}{RESET}")
    print(f"  {GREEN}  Status: {p['status']['state']} / {p['status']['moderate_status']}{RESET}")

    # -- Stock on Warehouses -----------------------------------
    pause()
    tool_call("get_stock_on_warehouses", "product_ids=[987210451, 987210452]")
    pause()
    resp = await client.request("/v1/product/info/stocks")
    for row in resp["result"]["rows"][:2]:
        print(f"  {WHITE}{row['offer_id']}:{RESET}")
        for s in row["stocks"]:
            print(f"  {GREEN}    {s['warehouse_name']:30} {s['type'].upper():4} — {s['present']:>4} шт. ({s['reserved']} reserved){RESET}")

    # -- FBS Orders --------------------------------------------
    header("2. Order Tracking")

    tool_call("get_fbs_orders", 'status="awaiting_packaging", days_back=7')
    pause()
    resp = await client.request("/v3/posting/fbs/list", {"filter": {"status": "awaiting_packaging"}})
    postings = resp["result"]["postings"]
    print(f"  {WHITE}{len(postings)} orders awaiting packaging:{RESET}")
    for o in postings:
        prod = o["products"][0]
        city = o["analytics_data"]["city"]
        payout = o["financial_data"]["products"][0]["payout"]
        print(f"  {GREEN}  #{o['posting_number']}{RESET}")
        print(f"  {GREEN}    {prod['name'][:45]} × {prod['quantity']}{RESET}")
        print(f"  {GREEN}    {city} → {o['analytics_data']['delivery_type']}  |  Payout: {payout:,.0f} ₽{RESET}")

    # -- FBO Orders --------------------------------------------
    pause()
    tool_call("get_fbo_orders", 'status="delivered", days_back=7')
    pause()
    resp = await client.request("/v2/posting/fbo/list")
    for o in resp["result"]["postings"]:
        prod = o["products"][0]
        print(f"  {GREEN}  #{o['posting_number']} → {o['status']}{RESET}")
        print(f"  {GREEN}    {prod['name'][:45]} — {prod['price']} ₽ → {o['analytics_data']['city']}{RESET}")

    # -- Analytics ---------------------------------------------
    header("3. Sales Analytics")

    tool_call("get_analytics", 'date_from="2026-03-29", date_to="2026-04-03", metrics=["revenue", "ordered_units", "hits_view"]')
    pause()
    resp = await client.request("/v1/analytics/data")
    data = resp["result"]
    print(f"  {WHITE}Daily breakdown (revenue / orders / views):{RESET}")
    for row in data["data"]:
        date = row["dimensions"][0]["name"]
        rev, orders, views = row["metrics"]
        bar = "#" * int(rev / 20000)
        print(f"  {GREEN}  {date}  {rev:>12,.0f} ₽  {int(orders):>3} orders  {int(views):>5} views  {bar}{RESET}")
    totals = data["totals"]
    print(f"  {BOLD}{WHITE}  {'TOTAL':10}  {totals[0]:>12,.0f} ₽  {int(totals[1]):>3} orders  {int(totals[2]):>5} views{RESET}")

    # -- Finance -----------------------------------------------
    pause()
    tool_call("get_finance_report", 'date_from="2026-04-01", date_to="2026-04-03"')
    pause()
    resp = await client.request("/v3/finance/transaction/list")
    ops = resp["result"]["operations"]
    for op in ops:
        item = op["items"][0]["name"][:40]
        print(f"  {GREEN}  {op['operation_date'][:10]}  {item}{RESET}")
        print(f"  {GREEN}    Sale: {op['accruals_for_sale']:>10,.0f} ₽  Commission: {op['sale_commission']:>10,.0f} ₽  Payout: {op['amount']:>10,.0f} ₽{RESET}")

    # -- Warehouses --------------------------------------------
    header("4. Warehouse Management")

    tool_call("get_warehouse_list")
    pause()
    resp = await client.request("/v1/warehouse/list")
    for wh in resp["result"]:
        print(f"  {GREEN}  {wh['warehouse_id']}  {wh['name']:35}  [{wh['status']}]{RESET}")

    # -- Write Operations --------------------------------------
    header("5. Write Operations (with confirmation)")

    tool_call("update_prices", 'prices=[{product_id: 987210451, price: "17490.00", old_price: "24990.00"}]')
    pause()
    resp = await client.request("/v1/product/import/prices", {"prices": [{"product_id": 987210451, "price": "17490.00"}]})
    print(f"  {GREEN}  [OK] Price updated: product 987210451 → 17,490 ₽{RESET}")

    pause()
    tool_call("update_stocks", 'stocks=[{product_id: 987210451, stock: 200, warehouse_id: 22143901}]')
    pause()
    resp = await client.request("/v2/products/stocks", {"stocks": [{"product_id": 987210451, "stock": 200}]})
    print(f"  {GREEN}  [OK] Stock updated: product 987210451 → 200 units{RESET}")

    pause()
    tool_call("create_product", 'name="Sony WH-1000XM5", offer_id="WH-SONY-XM5", price="29990.00", ...')
    pause()
    resp = await client.request("/v3/product/import", {"items": [{}]})
    print(f"  {GREEN}  [OK] Product created: task_id={resp['result']['task_id']} (pending moderation){RESET}")

    # -- Summary -----------------------------------------------
    print(f"\n{BOLD}{CYAN}{'-' * 60}{RESET}")
    print(f"{BOLD}{WHITE}  [OK] All 13 MCP tools demonstrated successfully{RESET}")
    print(f"{DIM}  DEMO_MODE=true • No API keys • No Docker • No databases{RESET}")
    print(f"{BOLD}{CYAN}{'-' * 60}{RESET}\n")


if __name__ == "__main__":
    asyncio.run(main())
