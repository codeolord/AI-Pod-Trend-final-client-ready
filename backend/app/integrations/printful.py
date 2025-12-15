from typing import Any, Dict, Optional

import httpx


class PrintfulClient:
    def __init__(self, api_key: str):
        self.api_key = api_key
        self.base_url = "https://api.printful.com"

    async def _request(self, method: str, endpoint: str, json: Optional[Dict] = None) -> Dict[str, Any]:
        headers = {"Authorization": f"Bearer {self.api_key}"}
        async with httpx.AsyncClient() as client:
            resp = await client.request(method, f"{self.base_url}{endpoint}", json=json, headers=headers, timeout=60)
            resp.raise_for_status()
            return resp.json()

    async def list_products(self) -> Dict[str, Any]:
        return await self._request("GET", "/products")

    async def create_product_with_mockup(
        self,
        store_product_name: str,
        printful_product_id: int,
        variant_id: int,
        file_url: str,
    ) -> Dict[str, Any]:
        payload = {
            "sync_product": {"name": store_product_name},
            "sync_variants": [
                {
                    "variant_id": variant_id,
                    "files": [{"url": file_url}],
                }
            ],
        }
        return await self._request("POST", "/store/products", json=payload)
