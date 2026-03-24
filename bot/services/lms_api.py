"""LMS API client service."""

import httpx


class LMSAPIClient:
    """Client for LMS Backend API.

    This service encapsulates all HTTP communication with the LMS backend.
    """

    def __init__(self, base_url: str, api_key: str):
        """Initialize LMS API client.

        Args:
            base_url: Base URL of the LMS API
            api_key: API key for authentication
        """
        self.base_url = base_url.rstrip("/")
        self.api_key = api_key
        self._client: httpx.AsyncClient | None = None

    async def _get_client(self) -> httpx.AsyncClient:
        """Get or create HTTP client with proper headers."""
        if self._client is None or self._client.is_closed:
            self._client = httpx.AsyncClient(
                base_url=self.base_url,
                headers={"X-API-Key": self.api_key} if self.api_key else {},
                timeout=30.0,
            )
        return self._client

    async def close(self) -> None:
        """Close the HTTP client."""
        if self._client and not self._client.is_closed:
            await self._client.aclose()

    async def health_check(self) -> bool:
        """Check if the LMS backend is healthy.

        Returns:
            True if backend is healthy, False otherwise
        """
        try:
            client = await self._get_client()
            # TODO: Replace with actual health endpoint
            response = await client.get("/items/")
            return response.status_code < 500
        except httpx.RequestError:
            return False

    async def get_items(self, item_type: str | None = None) -> list[dict]:
        """Get items from LMS.

        Args:
            item_type: Optional filter by item type (e.g., "lab")

        Returns:
            List of items
        """
        try:
            client = await self._get_client()
            params = {}
            if item_type:
                params["type"] = item_type
            response = await client.get("/items/", params=params)
            response.raise_for_status()
            return response.json()
        except httpx.RequestError:
            return []

    async def get_item(self, item_id: int) -> dict | None:
        """Get a specific item by ID.

        Args:
            item_id: Item ID

        Returns:
            Item data or None if not found
        """
        try:
            client = await self._get_client()
            response = await client.get(f"/items/{item_id}")
            if response.status_code == 404:
                return None
            response.raise_for_status()
            return response.json()
        except httpx.RequestError:
            return None
