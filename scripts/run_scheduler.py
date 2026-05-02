"""Simple runner to start the RecommendationScheduler in the foreground.

This script reads environment variables for Alpaca and scheduler behavior.
Do NOT commit secrets to source control. Provide credentials via env vars.
"""
import time
import logging
from quant_agent.trading.scheduler import RecommendationScheduler

logging.basicConfig(level=logging.INFO)

if __name__ == '__main__':
    scheduler = RecommendationScheduler()
    # start with configured cron expression (scheduler auto-starts if TRADING_AUTO_EXECUTE=true)
    try:
        scheduler.start()
    except Exception as e:
        logging.info(f"Scheduler start call returned/raised: {e}")

    logging.info("Scheduler is running. Press Ctrl-C to stop.")
    try:
        while True:
            time.sleep(60)
    except KeyboardInterrupt:
        logging.info("Shutdown requested, stopping scheduler...")
        scheduler.stop()
