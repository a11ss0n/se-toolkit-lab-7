"""LMS API client service."""

from dataclasses import dataclass
from typing import Any

import httpx


@dataclass
class ApiError:
    """Represents an API error with user-friendly message."""

    message: str
    details: str


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
            headers = {}
            if self.api_key:
                headers["Authorization"] = f"Bearer {self.api_key}"
            self._client = httpx.AsyncClient(
                base_url=self.base_url,
                headers=headers,
                timeout=30.0,
            )
        return self._client

    async def close(self) -> None:
        """Close the HTTP client."""
        if self._client and not self._client.is_closed:
            await self._client.aclose()

    def _format_error(self, error: Exception, url: str) -> ApiError:
        """Format an exception into a user-friendly error message.

        Args:
            error: The exception that occurred
            url: The URL that was being accessed

        Returns:
            ApiError with user-friendly message and details
        """
        if isinstance(error, httpx.ConnectError):
            # Connection refused, DNS failure, etc.
            error_str = str(error)
            if "Connection refused" in error_str or "refused" in error_str.lower():
                return ApiError(
                    message=f"Backend error: connection refused ({url}). Check that the services are running.",
                    details=error_str,
                )
            if "Name or service not known" in error_str or "nodename nor servname" in error_str:
                return ApiError(
                    message=f"Backend error: cannot resolve hostname ({url}). Check the URL configuration.",
                    details=error_str,
                )
            return ApiError(
                message=f"Backend error: connection failed ({url}). {error}",
                details=error_str,
            )

        if isinstance(error, httpx.TimeoutException):
            return ApiError(
                message=f"Backend error: request timed out ({url}). The service may be overloaded.",
                details=str(error),
            )

        if isinstance(error, httpx.HTTPStatusError):
            status = error.response.status_code
            if status == 401:
                return ApiError(
                    message="Backend error: HTTP 401 Unauthorized. Check the API key configuration.",
                    details=str(error),
                )
            if status == 403:
                return ApiError(
                    message="Backend error: HTTP 403 Forbidden. The API key may not have sufficient permissions.",
                    details=str(error),
                )
            if status == 404:
                return ApiError(
                    message=f"Backend error: HTTP 404 Not Found. The endpoint {url} does not exist.",
                    details=str(error),
                )
            if status == 502:
                return ApiError(
                    message="Backend error: HTTP 502 Bad Gateway. The backend service may be down.",
                    details=str(error),
                )
            if status == 503:
                return ApiError(
                    message="Backend error: HTTP 503 Service Unavailable. The backend is temporarily unavailable.",
                    details=str(error),
                )
            if status >= 500:
                return ApiError(
                    message=f"Backend error: HTTP {status} Server Error. The backend encountered an internal error.",
                    details=str(error),
                )
            return ApiError(
                message=f"Backend error: HTTP {status}. {error}",
                details=str(error),
            )

        # Generic error
        return ApiError(
            message=f"Backend error: {type(error).__name__}. {error}",
            details=str(error),
        )

    async def health_check(self) -> tuple[bool, str | None, ApiError | None]:
        """Check if the LMS backend is healthy.

        Returns:
            Tuple of (is_healthy, status_message, error)
            - is_healthy: True if backend is healthy
            - status_message: Human-readable status message (if healthy)
            - error: ApiError if unhealthy, None otherwise
        """
        try:
            client = await self._get_client()
            response = await client.get("/items/")
            response.raise_for_status()
            items = response.json()
            count = len(items) if isinstance(items, list) else "unknown"
            return True, f"Backend health status: OK. {count} items available.", None
        except httpx.RequestError as e:
            api_error = self._format_error(e, f"{self.base_url}/items/")
            return False, None, api_error
        except httpx.HTTPStatusError as e:
            api_error = self._format_error(e, f"{self.base_url}/items/")
            return False, None, api_error
        except Exception as e:
            api_error = ApiError(
                message=f"Backend error: unexpected error. {e}",
                details=str(e),
            )
            return False, None, api_error

    async def get_items(self, item_type: str | None = None) -> tuple[list[dict], ApiError | None]:
        """Get items from LMS.

        Args:
            item_type: Optional filter by item type (e.g., "lab")

        Returns:
            Tuple of (items, error)
            - items: List of items (empty list on error)
            - error: ApiError if request failed, None otherwise
        """
        try:
            client = await self._get_client()
            params = {}
            if item_type:
                params["type"] = item_type
            response = await client.get("/items/", params=params)
            response.raise_for_status()
            return response.json(), None
        except httpx.RequestError as e:
            api_error = self._format_error(e, f"{self.base_url}/items/")
            return [], api_error
        except httpx.HTTPStatusError as e:
            api_error = self._format_error(e, f"{self.base_url}/items/")
            return [], api_error
        except Exception as e:
            api_error = ApiError(
                message=f"Backend error: unexpected error. {e}",
                details=str(e),
            )
            return [], api_error

    async def get_item(self, item_id: int) -> tuple[dict | None, ApiError | None]:
        """Get a specific item by ID.

        Args:
            item_id: Item ID

        Returns:
            Tuple of (item, error)
            - item: Item data or None if not found
            - error: ApiError if request failed, None otherwise
        """
        try:
            client = await self._get_client()
            response = await client.get(f"/items/{item_id}")
            if response.status_code == 404:
                return None, None
            response.raise_for_status()
            return response.json(), None
        except httpx.RequestError as e:
            api_error = self._format_error(e, f"{self.base_url}/items/{item_id}")
            return None, api_error
        except httpx.HTTPStatusError as e:
            api_error = self._format_error(e, f"{self.base_url}/items/{item_id}")
            return None, api_error
        except Exception as e:
            api_error = ApiError(
                message=f"Backend error: unexpected error. {e}",
                details=str(e),
            )
            return None, api_error

    async def get_pass_rates(self, lab: str) -> tuple[list[dict], ApiError | None]:
        """Get pass rates for a specific lab.

        Args:
            lab: Lab identifier (e.g., "lab-04")

        Returns:
            Tuple of (pass_rates, error)
            - pass_rates: List of pass rate data per task
            - error: ApiError if request failed, None otherwise
        """
        try:
            client = await self._get_client()
            response = await client.get("/analytics/pass-rates", params={"lab": lab})
            response.raise_for_status()
            return response.json(), None
        except httpx.RequestError as e:
            api_error = self._format_error(e, f"{self.base_url}/analytics/pass-rates?lab={lab}")
            return [], api_error
        except httpx.HTTPStatusError as e:
            if e.response.status_code == 404:
                return [], None  # Lab not found - not an error, just empty
            api_error = self._format_error(e, f"{self.base_url}/analytics/pass-rates?lab={lab}")
            return [], api_error
        except Exception as e:
            api_error = ApiError(
                message=f"Backend error: unexpected error. {e}",
                details=str(e),
            )
            return [], api_error
