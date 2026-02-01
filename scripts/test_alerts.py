"""Quick test to verify alerting system works."""

import asyncio
import logging
from datetime import datetime

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s | %(levelname)-8s | %(name)s | %(message)s",
)

logger = logging.getLogger("test_alerts")


async def main():
    """Generate test alerts."""
    print("Generating test alerts for monitoring system...")
    print(f"Timestamp: {datetime.now().isoformat()}")
    print("-" * 60)

    # Generate different severity levels
    logger.warning("This is a WARNING test alert")
    await asyncio.sleep(0.5)

    logger.error("This is an ERROR test alert - database connection failed")
    await asyncio.sleep(0.5)

    logger.critical("This is a CRITICAL test alert - system is down!")
    await asyncio.sleep(0.5)

    # Generate some noise that should be filtered
    logger.info("This is INFO - should NOT appear in alerts")
    logger.debug("This is DEBUG - should NOT appear in alerts")

    print("-" * 60)
    print("✅ Test alerts generated!")
    print("")
    print("Next steps:")
    print("1. Wait 30-60 seconds for Promtail to ship logs to Elasticsearch")
    print("2. Test API: http://localhost:8000/api/v1/monitoring/alerts?minutes=5")
    print("3. Open frontend: http://localhost:5173")
    print("4. Alert banner should appear at top within 30 seconds")


if __name__ == "__main__":
    asyncio.run(main())
