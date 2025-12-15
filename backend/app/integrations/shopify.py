from typing import Any, Dict, List, Optional

import httpx


class ShopifyClient:
    def __init__(self, shop_domain: str, admin_access_token: str, api_version: str = "2023-10"):
        self.base_url = f"https://{shop_domain}/admin/api/{api_version}"
        self.token = admin_access_token

    async def _request(self, method: str, endpoint: str, json: Optional[Dict] = None) -> Dict[str, Any]:
        headers = {
            "X-Shopify-Access-Token": self.token,
            "Content-Type": "application/json",
        }
        async with httpx.AsyncClient() as client:
            resp = await client.request(method, f"{self.base_url}{endpoint}", json=json, headers=headers, timeout=60)
            resp.raise_for_status()
            return resp.json()

    async def create_draft_product(
        self,
        title: str,
        body_html: str,
        images: List[str],
        tags: List[str] | None = None,
    ) -> Dict[str, Any]:
        payload: Dict[str, Any] = {
            "product": {
                "title": title,
                "body_html": body_html,
                "images": [{"src": url} for url in images],
                "status": "draft",
            }
        }
        if tags:
            payload["product"]["tags"] = ", ".join(tags)
        return await self._request("POST", "/products.json", json=payload)
