"""
SEC Company Ticker Exchange Service
Service for fetching and caching company ticker data from SEC.
"""

import asyncio
import json
import logging
from datetime import datetime, timedelta

import aiofiles
import aiohttp

from .settings import settings

logger = logging.getLogger(__name__)


class TickerExchangeService:
    """Service for managing SEC company ticker exchange data."""

    def __init__(self):
        self.sec_ticker_url = "https://www.sec.gov/files/company_tickers_exchange.json"
        self.cache_file = settings.sec_data_directory / "company_tickers_exchange.json"
        self.cache_duration = timedelta(hours=24)  # Cache for 24 hours
        self._ticker_data: dict | None = None
        self._cik_to_ticker: dict[str, str] | None = None
        self._last_updated: datetime | None = None

    async def fetch_and_cache_tickers(self, force_refresh: bool = False) -> bool:
        """
        Fetch company ticker data from SEC and cache it locally.
        
        Args:
            force_refresh: Force refresh even if cache is valid
            
        Returns:
            True if successful, False otherwise
        """
        try:
            # Check if cache is still valid
            if not force_refresh and self._is_cache_valid():
                logger.info("Ticker cache is still valid, skipping fetch")
                return True

            logger.info(f"Fetching company ticker data from: {self.sec_ticker_url}")

            # Ensure cache directory exists
            self.cache_file.parent.mkdir(parents=True, exist_ok=True)

            # Fetch data from SEC
            async with aiohttp.ClientSession() as session:
                async with session.get(
                    self.sec_ticker_url,
                    headers={
                        'User-Agent': 'SEC EDGAR Filings App contact@example.com',
                        'Accept': 'application/json'
                    },
                    timeout=aiohttp.ClientTimeout(total=60)
                ) as response:
                    if response.status != 200:
                        logger.error(f"Failed to fetch ticker data: HTTP {response.status}")
                        return False

                    ticker_data = await response.json()

            # Save to cache file
            async with aiofiles.open(self.cache_file, 'w') as f:
                await f.write(json.dumps(ticker_data, indent=2))

            # Update in-memory cache
            self._ticker_data = ticker_data
            self._last_updated = datetime.now()
            self._build_cik_mapping()

            logger.info(f"Successfully cached {len(ticker_data.get('data', []))} ticker entries")
            return True

        except asyncio.TimeoutError:
            logger.error("Timeout while fetching ticker data")
            return False
        except Exception as e:
            logger.error(f"Error fetching ticker data: {e}")
            return False

    async def load_cached_data(self) -> bool:
        """Load ticker data from cache file."""
        try:
            if not self.cache_file.exists():
                logger.info("No cached ticker data found")
                return False

            async with aiofiles.open(self.cache_file) as f:
                content = await f.read()
                self._ticker_data = json.loads(content)

            # Get file modification time
            self._last_updated = datetime.fromtimestamp(self.cache_file.stat().st_mtime)
            self._build_cik_mapping()

            logger.info(f"Loaded {len(self._ticker_data.get('data', []))} ticker entries from cache")
            return True

        except Exception as e:
            logger.error(f"Error loading cached ticker data: {e}")
            return False

    def _is_cache_valid(self) -> bool:
        """Check if cached data is still valid."""
        if not self.cache_file.exists() or self._last_updated is None:
            return False

        return datetime.now() - self._last_updated < self.cache_duration

    def _build_cik_mapping(self):
        """Build CIK to ticker mapping for fast lookups."""
        if not self._ticker_data:
            return

        self._cik_to_ticker = {}

        # The SEC data format is: {"fields": [...], "data": [[...], ...]}
        data_entries = self._ticker_data.get('data', [])
        fields = self._ticker_data.get('fields', [])

        # Find the indices for CIK and ticker fields
        cik_index = None
        ticker_index = None

        for i, field in enumerate(fields):
            if field.lower() == 'cik':
                cik_index = i
            elif field.lower() in ['ticker', 'symbol']:
                ticker_index = i

        if cik_index is None or ticker_index is None:
            logger.warning("Could not find CIK or ticker fields in data")
            return

        # Build the mapping
        for entry in data_entries:
            if len(entry) > max(cik_index, ticker_index):
                cik = str(entry[cik_index]).zfill(10)  # Pad CIK to 10 digits
                ticker = entry[ticker_index]
                if cik and ticker:
                    self._cik_to_ticker[cik] = ticker

        logger.info(f"Built CIK-to-ticker mapping with {len(self._cik_to_ticker)} entries")

    async def get_ticker_by_cik(self, cik: str) -> str | None:
        """Get ticker symbol by CIK."""
        # Ensure data is loaded
        if self._cik_to_ticker is None:
            await self.ensure_data_loaded()

        if self._cik_to_ticker is None:
            return None

        # Normalize CIK (pad to 10 digits)
        normalized_cik = str(cik).zfill(10)
        return self._cik_to_ticker.get(normalized_cik)

    async def get_all_ticker_data(self) -> dict | None:
        """Get all ticker data."""
        await self.ensure_data_loaded()
        return self._ticker_data

    async def ensure_data_loaded(self) -> bool:
        """Ensure ticker data is loaded, fetching if necessary."""
        # Try to load from cache first
        if self._ticker_data is None:
            if not await self.load_cached_data():
                # Cache doesn't exist or failed to load, fetch fresh data
                return await self.fetch_and_cache_tickers()

        # Check if cache is expired
        if not self._is_cache_valid():
            return await self.fetch_and_cache_tickers()

        return True

    def get_cache_info(self) -> dict:
        """Get information about the ticker cache."""
        return {
            "cache_file": str(self.cache_file),
            "cache_exists": self.cache_file.exists(),
            "last_updated": self._last_updated.isoformat() if self._last_updated else None,
            "is_valid": self._is_cache_valid(),
            "entries_count": len(self._ticker_data.get('data', [])) if self._ticker_data else 0,
            "cik_mapping_count": len(self._cik_to_ticker) if self._cik_to_ticker else 0
        }


# Global instance
ticker_service = TickerExchangeService()
