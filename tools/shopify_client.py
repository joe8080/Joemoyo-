"""
Shopify Admin REST API client.
Requires SHOPIFY_SHOP_NAME and SHOPIFY_ACCESS_TOKEN in .env.
"""

import json
from datetime import datetime, timedelta

import requests

from config.settings import settings


class ShopifyClient:
    """Wrapper for the Shopify Admin REST API."""

    API_VERSION = "2024-01"

    def __init__(self):
        if not settings.shopify_shop_name or not settings.shopify_access_token:
            raise EnvironmentError(
                "Shopify credentials not configured. "
                "Add SHOPIFY_SHOP_NAME and SHOPIFY_ACCESS_TOKEN to your .env file. "
                "Create an access token in Shopify: Settings > Apps > Develop apps."
            )
        self.base_url = f"https://{settings.shopify_shop_name}/admin/api/{self.API_VERSION}"
        self.headers = {
            "X-Shopify-Access-Token": settings.shopify_access_token,
            "Content-Type": "application/json",
        }

    def get_orders(self, days_back: int = 30) -> list[dict]:
        """Fetch orders from the last N days."""
        since = (datetime.now() - timedelta(days=days_back)).strftime("%Y-%m-%dT%H:%M:%S")
        response = requests.get(
            f"{self.base_url}/orders.json",
            headers=self.headers,
            params={"status": "any", "created_at_min": since, "limit": 250},
            timeout=15,
        )
        response.raise_for_status()
        return response.json().get("orders", [])

    def get_products(self) -> list[dict]:
        """Fetch all products."""
        response = requests.get(
            f"{self.base_url}/products.json",
            headers=self.headers,
            params={"limit": 250},
            timeout=15,
        )
        response.raise_for_status()
        return response.json().get("products", [])

    def compute_sales_summary(self, orders: list[dict]) -> dict:
        """Compute key metrics from a list of orders."""
        if not orders:
            return {"total_revenue": 0.0, "order_count": 0, "avg_order_value": 0.0, "currency": "USD"}
        total = sum(float(o.get("total_price", 0)) for o in orders)
        count = len(orders)
        return {
            "total_revenue": round(total, 2),
            "order_count": count,
            "avg_order_value": round(total / count, 2),
            "currency": orders[0].get("currency", "USD"),
        }

    def simplify_orders(self, orders: list[dict]) -> list[dict]:
        """Strip orders down to key fields to avoid token overflow."""
        return [
            {
                "order_id": o.get("order_number"),
                "total": o.get("total_price"),
                "items": len(o.get("line_items", [])),
                "date": o.get("created_at", "")[:10],
                "city": o.get("shipping_address", {}).get("city", "") if o.get("shipping_address") else "",
                "fulfillment": o.get("fulfillment_status", ""),
            }
            for o in orders
        ]

    def simplify_products(self, products: list[dict]) -> list[dict]:
        """Strip products down to key fields."""
        return [
            {
                "title": p.get("title"),
                "variants": len(p.get("variants", [])),
                "status": p.get("status"),
            }
            for p in products
        ]
