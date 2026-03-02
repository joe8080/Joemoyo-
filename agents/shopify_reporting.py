"""
ShopifyReportingAgent: Pulls live Shopify store data and generates reports.

Connects to the Shopify Admin API, fetches sales and product data,
and uses Claude to generate narrative insights and recommendations.

Requires SHOPIFY_SHOP_NAME and SHOPIFY_ACCESS_TOKEN in .env
"""

import json
from datetime import date

from agents.base_agent import BaseAgent
from prompts.shopify_prompts import SHOPIFY_SYSTEM_PROMPT


class ShopifyReportingAgent(BaseAgent):

    def __init__(self):
        # Lazy import so missing credentials only error when this agent is used
        from tools.shopify_client import ShopifyClient
        self.shopify = ShopifyClient()
        super().__init__()

    @property
    def system_prompt(self) -> str:
        return SHOPIFY_SYSTEM_PROMPT

    def _define_tools(self) -> list:
        return [
            {
                "name": "get_sales_data",
                "description": "Fetch recent sales orders from the Shopify store.",
                "input_schema": {
                    "type": "object",
                    "properties": {
                        "days_back": {
                            "type": "integer",
                            "description": "Number of days of order history to fetch",
                        },
                    },
                    "required": ["days_back"],
                },
            },
            {
                "name": "get_product_catalog",
                "description": "Fetch the current product catalog and inventory status.",
                "input_schema": {
                    "type": "object",
                    "properties": {},
                    "required": [],
                },
            },
            {
                "name": "compute_metrics",
                "description": "Compute summary sales metrics (revenue, order count, AOV).",
                "input_schema": {
                    "type": "object",
                    "properties": {
                        "days_back": {"type": "integer"},
                    },
                    "required": ["days_back"],
                },
            },
        ]

    def _execute_tool(self, tool_name: str, tool_input: dict) -> str:
        if tool_name == "get_sales_data":
            orders = self.shopify.get_orders(days_back=tool_input["days_back"])
            simplified = self.shopify.simplify_orders(orders)
            return json.dumps(simplified, indent=2)

        if tool_name == "get_product_catalog":
            products = self.shopify.get_products()
            simplified = self.shopify.simplify_products(products)
            return json.dumps(simplified, indent=2)

        if tool_name == "compute_metrics":
            orders = self.shopify.get_orders(days_back=tool_input["days_back"])
            summary = self.shopify.compute_sales_summary(orders)
            return json.dumps(summary, indent=2)

        return f"Unknown tool: {tool_name}"

    def generate_weekly_report(self) -> str:
        """Generate a weekly Shopify performance report."""
        prompt = """
Generate a comprehensive weekly Shopify performance report.

Steps:
1. Fetch the last 7 days of sales data
2. Compute key metrics for the last 7 days
3. Fetch 30-day data for month-over-month context
4. Compute 30-day metrics for comparison
5. Fetch the product catalog
6. Analyze the data and write the report

Report sections:
- EXECUTIVE SUMMARY (3 bullets max — what the owner needs to know today)
- REVENUE ANALYSIS (7-day totals, comparison to prior 7 days if inferrable)
- ORDER BREAKDOWN (count, AOV, top locations)
- PRODUCT PERFORMANCE (which products are moving, which are stalling)
- FULFILLMENT HEALTH (any unfulfilled or flagged orders)
- TOP 3 RECOMMENDATIONS (specific, actionable, prioritized)

Format as clean markdown. Keep it scannable.
"""
        result = self.run(prompt)
        filename = f"shopify_weekly_{date.today().isoformat()}.md"
        self.save_output(result, "reports", filename)
        return result

    def generate_monthly_report(self) -> str:
        """Generate a monthly Shopify performance report."""
        prompt = """
Generate a comprehensive monthly Shopify performance report.

Steps:
1. Fetch 30 days of sales data and compute metrics
2. Fetch 60 days of data for prior-month comparison
3. Fetch the product catalog
4. Analyze trends over the full 30-day period

Report sections:
- EXECUTIVE SUMMARY
- MONTHLY REVENUE & GROWTH
- TOP PERFORMING PRODUCTS
- CUSTOMER GEOGRAPHY
- FULFILLMENT & OPERATIONS
- NEXT MONTH STRATEGY (promotions, inventory, marketing focus)

Format as clean markdown suitable for a monthly business review.
"""
        result = self.run(prompt)
        filename = f"shopify_monthly_{date.today().isoformat()}.md"
        self.save_output(result, "reports", filename)
        return result
