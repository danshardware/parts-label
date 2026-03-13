"""Octopart API client for fetching part information."""

import os
import requests
from typing import Optional, Tuple
import logging

logger = logging.getLogger(__name__)

# Octopart API endpoints
OCTOPART_API_BASE = "https://api.octopart.com/v3"
OCTOPART_SEARCH_ENDPOINT = f"{OCTOPART_API_BASE}/parts/search"


class OctopartClient:
    """Client for Octopart API (free tier)."""

    def __init__(self, api_key: Optional[str] = None):
        """
        Initialize Octopart client.

        Args:
            api_key: Optional Octopart API key. If not provided, uses free tier.
        """
        self.api_key = api_key or os.environ.get("OCTOPART_API_KEY", "")
        self.session = requests.Session()

    def search(self, query: str) -> Optional[dict]:
        """
        Search Octopart for a part.

        Args:
            query: Part number or search query

        Returns:
            Dictionary with part info (name, datasheet, manufacturer) or None
        """
        try:
            params = {
                "q": query,
                "start": 0,
                "limit": 1,
                "include": ["datasheets"],
            }

            if self.api_key:
                params["apikey"] = self.api_key

            response = self.session.get(
                OCTOPART_SEARCH_ENDPOINT,
                params=params,
                timeout=10,
            )
            response.raise_for_status()

            data = response.json()

            if data.get("results") and len(data["results"]) > 0:
                part = data["results"][0]
                return self._extract_part_info(part)

            return None

        except requests.exceptions.RequestException as e:
            logger.warning(f"Octopart API error: {e}")
            return None

    def _extract_part_info(self, part: dict) -> dict:
        """
        Extract relevant info from Octopart part data.

        Args:
            part: Part data from Octopart API

        Returns:
            Dictionary with name, datasheet_url, manufacturer
        """
        # Try to get part name from various fields
        name = (
            part.get("mpn")
            or part.get("display_mpn")
            or part.get("brand", {}).get("name", "")
        )

        # Extract datasheet URL
        datasheet_url = None
        datasheets = part.get("datasheets", [])
        if datasheets and len(datasheets) > 0:
            datasheet_url = datasheets[0].get("url")

        # Get manufacturer
        manufacturer = part.get("brand", {}).get("name", "Unknown")

        return {
            "name": name,
            "datasheet_url": datasheet_url,
            "manufacturer": manufacturer,
            "mpn": part.get("mpn", ""),
        }

    def get_part_info(self, part_number: str) -> Tuple[str, Optional[str]]:
        """
        Get part name and datasheet URL.

        Args:
            part_number: Part number to search

        Returns:
            Tuple of (part_name, datasheet_url)
            If API fails, returns (part_number, None)
        """
        result = self.search(part_number)

        if result:
            return result["name"] or part_number, result.get("datasheet_url")

        # Fallback: return part number and no datasheet
        return part_number, None
