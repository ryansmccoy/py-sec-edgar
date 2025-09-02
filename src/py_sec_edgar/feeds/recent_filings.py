"""
Recent SEC EDGAR Filings Feed
Fetch and parse the most recent SEC filings from the RSS feed.
"""

import asyncio
import logging
from datetime import datetime

import aiohttp
import feedparser

logger = logging.getLogger(__name__)


class RecentFilingsFeed:
    """Handler for fetching recent SEC EDGAR filings from RSS feed."""

    def __init__(self):
        self.base_url = "https://www.sec.gov/cgi-bin/browse-edgar"
        self.default_params = {
            "action": "getcurrent",
            "CIK": "",
            "type": "",
            "company": "",
            "dateb": "",
            "owner": "include",
            "start": "0",
            "count": "40",
            "output": "atom"
        }
        self._ticker_service = None

    def _get_ticker_service(self):
        """Lazy import to avoid circular dependencies."""
        if self._ticker_service is None:
            try:
                from ..ticker_service import ticker_service
                self._ticker_service = ticker_service
            except ImportError:
                logger.warning("Ticker service not available")
                self._ticker_service = None
        return self._ticker_service

    async def fetch_recent_filings(
        self,
        count: int = 40,
        form_type: str | None = None,
        cik: str | None = None,
        company: str | None = None
    ) -> list[dict]:
        """
        Fetch recent SEC filings from the RSS feed.
        
        Args:
            count: Number of filings to retrieve (max 400)
            form_type: Filter by form type (e.g., '8-K', '10-K', '10-Q')
            cik: Filter by company CIK
            company: Filter by company name
            
        Returns:
            List of filing dictionaries with parsed data
        """
        try:
            # Build request parameters
            params = self.default_params.copy()
            params["count"] = str(min(count, 400))  # SEC limits to 400

            if form_type:
                params["type"] = form_type
            if cik:
                params["CIK"] = cik
            if company:
                params["company"] = company

            # Build URL
            url = self.base_url
            param_string = "&".join([f"{k}={v}" for k, v in params.items() if v])
            full_url = f"{url}?{param_string}"

            logger.info(f"Fetching recent filings from: {full_url}")

            # Fetch RSS feed
            async with aiohttp.ClientSession() as session:
                async with session.get(
                    full_url,
                    headers={
                        'User-Agent': 'SEC EDGAR Filings App contact@example.com',
                        'Accept': 'application/atom+xml, application/xml, text/xml'
                    },
                    timeout=aiohttp.ClientTimeout(total=30)
                ) as response:
                    if response.status != 200:
                        logger.error(f"Failed to fetch RSS feed: HTTP {response.status}")
                        return []

                    feed_content = await response.text()

            # Parse RSS feed
            feed = feedparser.parse(feed_content)

            if not feed.entries:
                logger.warning("No entries found in RSS feed")
                return []

            # Parse and structure the filings data
            filings = []
            for entry in feed.entries:
                filing_data = await self._parse_filing_entry(entry)
                if filing_data:
                    filings.append(filing_data)

            logger.info(f"Successfully parsed {len(filings)} recent filings")
            return filings

        except asyncio.TimeoutError:
            logger.error("Timeout while fetching recent filings")
            return []
        except Exception as e:
            logger.error(f"Error fetching recent filings: {e}")
            return []

    async def _parse_filing_entry(self, entry) -> dict | None:
        """Parse a single RSS feed entry into structured filing data."""
        try:
            # Import required modules at the top
            import re

            # Extract basic information
            title = getattr(entry, 'title', '')
            summary = getattr(entry, 'summary', '')
            link = getattr(entry, 'link', '')
            published = getattr(entry, 'published', '')
            updated = getattr(entry, 'updated', '')

            # Parse title to extract form type, company, and CIK
            # Title format is typically: "FORM_TYPE - COMPANY_NAME (CIK)"
            form_type = ""
            company_name = ""
            cik = ""

            if title:
                # Try to extract form type (first part before " - ")
                if " - " in title:
                    form_type = title.split(" - ")[0].strip()
                    remainder = title.split(" - ", 1)[1]

                    # Extract CIK from parentheses - handle format like "(0001234567) (Issuer)"
                    cik_match = re.search(r'\((\d{10})\)', remainder)
                    if cik_match:
                        cik = cik_match.group(1)
                        # Company name is everything before the first CIK parentheses
                        company_name = re.sub(r'\s*\(\d{10}\).*$', '', remainder).strip()
                    else:
                        company_name = remainder.strip()

            # Get ticker symbol using CIK
            ticker = ""
            symbol = ""
            if cik:
                ticker_service = self._get_ticker_service()
                if ticker_service:
                    try:
                        ticker = await ticker_service.get_ticker_by_cik(cik)
                        symbol = ticker  # Use same value for both fields
                    except Exception as e:
                        logger.debug(f"Could not get ticker for CIK {cik}: {e}")

            # Parse dates
            filed_datetime = None
            if published:
                try:
                    # Parse the published date
                    filed_datetime = datetime(*published[:6]) if hasattr(published, '__iter__') else datetime.strptime(published, '%a, %d %b %Y %H:%M:%S %z')
                except:
                    try:
                        # Try alternative parsing
                        filed_datetime = datetime.fromisoformat(published.replace('Z', '+00:00'))
                    except:
                        logger.debug(f"Could not parse date: {published}")

            # Extract filing URL from link
            filing_url = link

            # Generate unique ID
            unique_id = f"{cik}_{form_type}_{int(datetime.now().timestamp())}" if cik and form_type else f"filing_{int(datetime.now().timestamp())}"

            filing_data = {
                "id": unique_id,
                "ticker": ticker or "",  # Now populated from ticker service
                "symbol": symbol or "",  # Now populated from ticker service
                "company_name": company_name,
                "form_type": form_type,
                "cik": cik,
                "period_reported": "",  # Not available in RSS feed
                "filing_name": title,
                "description": summary,
                "filed_date": filed_datetime.strftime("%Y-%m-%d") if filed_datetime else "",
                "filed_time": filed_datetime.strftime("%H:%M:%S") if filed_datetime else "",
                "capture_datetime": datetime.now().isoformat(),
                "capture_date": datetime.now().strftime("%Y-%m-%d"),
                "capture_time": datetime.now().strftime("%H:%M:%S"),
                "timestamp": filed_datetime.isoformat() if filed_datetime else datetime.now().isoformat(),
                "filing_url": filing_url,
                "sec_link": filing_url,
                "status": "Filed",
                "source": "SEC RSS Feed",
                "raw_title": title,
                "raw_summary": summary,
                "raw_link": link,
                "published": published,
                "updated": updated
            }

            return filing_data

        except Exception as e:
            logger.error(f"Error parsing filing entry: {e}")
            return None


# Global instance
recent_filings_feed = RecentFilingsFeed()


async def fetch_recent_rss_filings_async(
    count: int = 40,
    form_type: str | None = None,
    cik: str | None = None,
    company: str | None = None
) -> list[dict]:
    """
    Async function to fetch recent SEC filings from RSS feed.
    
    Args:
        count: Number of filings to retrieve (max 400)
        form_type: Filter by form type (e.g., '8-K', '10-K', '10-Q')
        cik: Filter by company CIK
        company: Filter by company name
        
    Returns:
        List of filing dictionaries with parsed data
    """
    return await recent_filings_feed.fetch_recent_filings(
        count=count,
        form_type=form_type,
        cik=cik,
        company=company
    )


def fetch_recent_rss_filings(
    count: int = 40,
    form_type: str | None = None,
    cik: str | None = None,
    company: str | None = None
) -> list[dict]:
    """
    Synchronous wrapper to fetch recent SEC filings from RSS feed.
    
    Args:
        count: Number of filings to retrieve (max 400)
        form_type: Filter by form type (e.g., '8-K', '10-K', '10-Q')
        cik: Filter by company CIK
        company: Filter by company name
        
    Returns:
        List of filing dictionaries with parsed data
    """
    import asyncio
    
    try:
        # Try to get the existing event loop
        loop = asyncio.get_event_loop()
        if loop.is_running():
            # If loop is already running, we need to use asyncio.create_task
            # But since we're in a sync context, we'll need to handle this differently
            logger.warning("Event loop already running, creating new event loop for RSS fetch")
            import threading
            
            result = []
            exception = None
            
            def run_async():
                nonlocal result, exception
                try:
                    new_loop = asyncio.new_event_loop()
                    asyncio.set_event_loop(new_loop)
                    result = new_loop.run_until_complete(
                        fetch_recent_rss_filings_async(count, form_type, cik, company)
                    )
                    new_loop.close()
                except Exception as e:
                    exception = e
            
            thread = threading.Thread(target=run_async)
            thread.start()
            thread.join()
            
            if exception:
                raise exception
            return result
        else:
            # No event loop running, we can use asyncio.run
            return asyncio.run(fetch_recent_rss_filings_async(count, form_type, cik, company))
    except RuntimeError:
        # No event loop, use asyncio.run
        return asyncio.run(fetch_recent_rss_filings_async(count, form_type, cik, company))
