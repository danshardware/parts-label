"""Part information lookup from distributor websites and APIs."""

import os
import requests
import logging
from typing import Optional, Tuple
from bs4 import BeautifulSoup
from dotenv import load_dotenv

from .part_number import detect_distributor, Distributor

# Load environment variables from .env file
load_dotenv()

logger = logging.getLogger(__name__)


class LCSCSearcher:
    """Search LCSC website for part information."""

    def __init__(self):
        self.session = requests.Session()
        self.session.headers.update({
            'User-Agent': 'Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36'
        })

    def search(self, part_number: str) -> Tuple[str, Optional[str]]:
        """
        Search LCSC for part information.

        Args:
            part_number: LCSC part number (e.g., C123456)

        Returns:
            Tuple of (part_name, datasheet_url)
        """
        try:
            # LCSC URL pattern: https://www.lcsc.com/product-detail/{part_number}.html
            url = f"https://www.lcsc.com/product-detail/{part_number}.html"
            logger.debug(f"Fetching LCSC page: {url}")

            response = self.session.get(url, timeout=10)
            response.raise_for_status()

            soup = BeautifulSoup(response.text, 'lxml')

            # Extract part name from page title or product name element
            part_name = None

            # Try to find the part name in various locations
            # Option 1: Product title
            title_elem = soup.find('h1', class_='product-name')
            if title_elem:
                part_name = title_elem.get_text(strip=True)

            # Option 2: Page title
            if not part_name:
                title_tag = soup.find('title')
                if title_tag:
                    # Extract meaningful part from title
                    title_text = title_tag.get_text(strip=True)
                    # Stop at first pipe symbol
                    if '|' in title_text:
                        part_name = title_text.split('|')[0].strip()
                    else:
                        # Remove " - LCSC" suffix if present
                        part_name = title_text.split(' - ')[0].strip()

            # Extract datasheet URL
            datasheet_url = None

            # Look for datasheet link
            datasheet_link = soup.find('a', href=True, text=lambda t: t and 'datasheet' in t.lower())
            if not datasheet_link:
                # Try alternative selector
                datasheet_link = soup.find('a', class_='datasheet-link')
            if not datasheet_link:
                # Try finding PDF links
                pdf_links = soup.find_all('a', href=lambda h: h and h.endswith('.pdf'))
                if pdf_links:
                    datasheet_link = pdf_links[0]

            if datasheet_link:
                datasheet_url = datasheet_link['href']
                # Make absolute URL if relative
                if datasheet_url and not datasheet_url.startswith('http'):
                    datasheet_url = f"https://www.lcsc.com{datasheet_url}"

            if part_name:
                logger.info(f"Found LCSC part: {part_name}")
                if datasheet_url:
                    logger.debug(f"Datasheet: {datasheet_url}")
                return part_name, datasheet_url
            else:
                logger.warning(f"Could not extract part name from LCSC page")
                return part_number, None

        except requests.exceptions.RequestException as e:
            logger.warning(f"LCSC lookup failed: {e}")
            return part_number, None
        except Exception as e:
            logger.error(f"Error parsing LCSC page: {e}")
            return part_number, None


class MouserSearcher:
    """Search Mouser API for part information."""

    def __init__(self, api_key: Optional[str] = None, llm_client=None):
        """
        Initialize Mouser API client.

        Args:
            api_key: Mouser API key. If not provided, uses MOUSER_API_KEY env var.
            llm_client: Optional LLM client for smart part matching
        """
        self.api_key = api_key or os.environ.get('MOUSER_API_KEY', '')
        self.base_url = "https://api.mouser.com/api/v1"
        self.session = requests.Session()
        self.llm_client = llm_client

    def _clean_part_result(self, part: dict) -> dict:
        """
        Clean Mouser API result to only essential fields.

        Args:
            part: Raw Mouser API part result

        Returns:
            Cleaned part dictionary
        """
        return {
            'MouserPartNumber': part.get('MouserPartNumber'),
            'ManufacturerPartNumber': part.get('ManufacturerPartNumber'),
            'Manufacturer': part.get('Manufacturer'),
            'Description': part.get('Description'),
            'Category': part.get('Category'),
            'Availability': part.get('Availability'),
            'AvailabilityInStock': part.get('AvailabilityInStock'),
            'ProductDetailUrl': part.get('ProductDetailUrl', '').split('?')[0],  # Remove query params
            'DataSheetUrl': part.get('DataSheetUrl'),
            'InfoMessages': part.get('InfoMessages', []),
        }

    def _pick_best_match(self, search_term: str, parts: list) -> dict:
        """
        Pick the best matching part from multiple results.

        Args:
            search_term: Original search term
            parts: List of cleaned part results

        Returns:
            Best matching part
        """
        if len(parts) == 1:
            return parts[0]

        # Prefer exact manufacturer part number match
        for part in parts:
            if part['ManufacturerPartNumber'] == search_term:
                logger.debug(f"Exact match: {search_term}")
                return part

        # Prefer parts with stock
        in_stock = [p for p in parts if p.get('AvailabilityInStock') and p['AvailabilityInStock'] != '0']
        if in_stock:
            # Sort by stock quantity (most popular)
            in_stock.sort(key=lambda p: int(p['AvailabilityInStock']) if p['AvailabilityInStock'].isdigit() else 0, reverse=True)
            logger.debug(f"Selected most popular variant: {in_stock[0]['ManufacturerPartNumber']}")
            return in_stock[0]

        # Default to first result
        logger.debug(f"Defaulting to first result: {parts[0]['ManufacturerPartNumber']}")
        return parts[0]

    def search(self, part_number: str) -> Tuple[str, Optional[str]]:
        """
        Search Mouser API for part information.

        Args:
            part_number: Part number to search (Mouser P/N or Manufacturer P/N)

        Returns:
            Tuple of (description, product_url)
        """
        if not self.api_key:
            logger.warning("Mouser API key not configured")
            return part_number, None

        try:
            # Mouser API search endpoint
            url = f"{self.base_url}/search/keyword"

            params = {
                'apiKey': self.api_key
            }

            data = {
                'SearchByKeywordRequest': {
                    'keyword': part_number,
                    'records': 5,  # Get multiple results for better matching
                    'startingRecord': 0
                }
            }

            logger.debug(f"Searching Mouser API for: {part_number}")

            response = self.session.post(url, params=params, json=data, timeout=10)
            response.raise_for_status()

            result = response.json()

            # Parse response
            errors = result.get('Errors', [])
            if errors:
                logger.error(f"Mouser API errors: {errors}")
                return part_number, None

            parts = result.get('SearchResults', {}).get('Parts', [])

            if parts and len(parts) > 0:
                # Clean all results
                cleaned_parts = [self._clean_part_result(p) for p in parts]

                # Pick best match
                best_part = self._pick_best_match(part_number, cleaned_parts)

                # Build description
                mfr = best_part.get('Manufacturer', '')
                mfr_pn = best_part.get('ManufacturerPartNumber', part_number)
                desc = best_part.get('Description', '')
                category = best_part.get('Category', '')

                # Combine into useful description
                description = f"{mfr} {mfr_pn}: {desc}"
                if category and category not in desc:
                    description = f"{category} - {description}"

                # Get URL (prefer product page over empty datasheet)
                url = best_part.get('DataSheetUrl') or best_part.get('ProductDetailUrl')

                logger.info(f"Found Mouser part: {mfr_pn}")
                if url:
                    logger.debug(f"URL: {url}")

                return description, url
            else:
                logger.warning(f"No results from Mouser API for {part_number}")
                return part_number, None

        except requests.exceptions.RequestException as e:
            logger.warning(f"Mouser API request failed: {e}")
            return part_number, None
        except Exception as e:
            logger.error(f"Error parsing Mouser API response: {e}")
            return part_number, None


class PartLookupClient:
    """Main client for looking up part information from various sources."""

    def __init__(self, mouser_api_key: Optional[str] = None, llm_client=None):
        """
        Initialize part lookup client.

        Args:
            mouser_api_key: Optional Mouser API key
            llm_client: Optional LLM client for smart matching
        """
        self.lcsc_searcher = LCSCSearcher()
        self.mouser_searcher = MouserSearcher(api_key=mouser_api_key, llm_client=llm_client)
        self.llm_client = llm_client

    def get_part_info(self, part_number: str, try_mouser_fuzzy: bool = True) -> Tuple[str, Optional[str]]:
        """
        Look up part information based on detected distributor.

        Args:
            part_number: Part number to search
            try_mouser_fuzzy: If True, try Mouser search for unknown distributors

        Returns:
            Tuple of (description, datasheet_url)
        """
        distributor = detect_distributor(part_number)

        logger.debug(f"Looking up {part_number} from {distributor.value}")

        if distributor == Distributor.LCSC:
            return self.lcsc_searcher.search(part_number)
        elif distributor == Distributor.MOUSER:
            return self.mouser_searcher.search(part_number)
        elif distributor == Distributor.DIGI_KEY:
            # Digi-Key OAuth is too complex for CLI, try Mouser as fallback
            if try_mouser_fuzzy and self.mouser_searcher.api_key:
                logger.info(f"Digi-Key part detected, trying Mouser search")
                result = self.mouser_searcher.search(part_number)
                if result[0] != part_number:  # Got useful data
                    return result
            logger.info(f"Digi-Key part detected, using part number as name")
            return part_number, None
        else:
            # Unknown distributor, try Mouser as fallback
            if try_mouser_fuzzy and self.mouser_searcher.api_key:
                logger.info(f"Unknown distributor, trying Mouser search")
                result = self.mouser_searcher.search(part_number)
                if result[0] != part_number:  # Got useful data
                    return result
            logger.info(f"Unknown distributor, using part number as name")
            return part_number, None
