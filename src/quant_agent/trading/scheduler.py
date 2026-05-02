"""
Recommendation Scheduler

Runs the recommendation engine on a schedule and can auto-execute paper trades.
"""

import logging
import os
from typing import Optional, Dict, List
from datetime import datetime, time

try:
    from apscheduler.schedulers.background import BackgroundScheduler
    from apscheduler.triggers.cron import CronTrigger
except ImportError:
    BackgroundScheduler = None
    CronTrigger = None

from quant_agent.sector_recommendations import SectorRecommendationEngine
from quant_agent.trading.alpaca_client import AlpacaClient
from quant_agent.trading.trading_executor import TradingExecutor


logger = logging.getLogger(__name__)


class RecommendationScheduler:
    """
    Schedules hourly recommendation generation.
    
    Runs every hour during market hours (9:30 AM - 4:00 PM ET).
    Generates sector recommendations and can auto-execute paper trades.
    """
    
    def __init__(
        self,
        alpaca_client: Optional[AlpacaClient] = None,
        recommendation_engine: Optional[SectorRecommendationEngine] = None,
        trading_executor: Optional[TradingExecutor] = None,
        auto_execute: bool = True,
        min_confidence: float = 0.80,
        market_scan_cron: str = "*/5 * * * *",
        crypto_scan_cron: str = "*/15 * * * *",
        market_position_size_pct: float = 0.12,
        market_max_position_size_pct: float = 0.35,
        market_min_confidence: float = 0.62,
        crypto_position_size_pct: float = 0.02,
        crypto_max_position_size_pct: float = 0.05,
        crypto_min_confidence: float = 0.88,
        crypto_watchlist: Optional[List[str]] = None,
        enable_crypto: bool = True,
    ):
        """
        Initialize the scheduler.
        
        Args:
            alpaca_client: Alpaca API client (initialized if None)
            recommendation_engine: Recommendation engine (initialized if None)
            trading_executor: Trading executor used for paper trades.
            auto_execute: Whether to auto-execute paper trades.
            min_confidence: Minimum confidence to execute trades (default: 0.80)
            market_scan_cron: Cron schedule for market scans.
            crypto_scan_cron: Cron schedule for crypto scans.
            market_position_size_pct: Aggressive market target allocation.
            market_max_position_size_pct: Aggressive market cap per position.
            market_min_confidence: Minimum confidence for market trades.
            crypto_position_size_pct: Conservative crypto target allocation.
            crypto_max_position_size_pct: Conservative crypto cap per position.
            crypto_min_confidence: Minimum confidence for crypto trades.
            crypto_watchlist: Symbols to scan for crypto paper trading.
            enable_crypto: Enable 24/7 crypto scans.
        """
        if BackgroundScheduler is None:
            raise RuntimeError("apscheduler not installed. Run: pip install apscheduler")
        
        self.alpaca_client = alpaca_client or AlpacaClient(paper_trading=True)
        self.recommendation_engine = recommendation_engine or SectorRecommendationEngine()
        self.trading_executor = trading_executor or TradingExecutor(self.alpaca_client)
        # Respect paper trading and global execution flag
        global_exec_enabled = os.getenv("TRADING_ENABLE_EXECUTION", "true").lower() == "true"
        self.auto_execute = bool(auto_execute and getattr(self.alpaca_client, "paper_trading", False) and global_exec_enabled)
        self.min_confidence = min_confidence
        self.market_scan_cron = market_scan_cron
        self.crypto_scan_cron = crypto_scan_cron
        self.market_position_size_pct = market_position_size_pct
        self.market_max_position_size_pct = market_max_position_size_pct
        self.market_min_confidence = market_min_confidence
        self.crypto_position_size_pct = crypto_position_size_pct
        self.crypto_max_position_size_pct = crypto_max_position_size_pct
        self.crypto_min_confidence = crypto_min_confidence
        self.crypto_watchlist = crypto_watchlist or ["BTC-USD", "ETH-USD", "SOL-USD", "DOGE-USD", "XRP-USD"]
        self.enable_crypto = enable_crypto and getattr(self.alpaca_client, "paper_trading", False)
        
        self.scheduler = BackgroundScheduler()
        self.last_run: Optional[datetime] = None
        self.last_recommendations: Dict = {}
        # Auto-start scheduler if explicitly requested via environment variable
        if os.getenv("TRADING_AUTO_EXECUTE", "false").lower() == "true":
            try:
                self.start(self.market_scan_cron)
            except Exception as e:
                logger.error(f"Failed to auto-start scheduler: {e}")
    
    def _is_market_open(self) -> bool:
        """Check if stock market is currently open (9:30 AM - 4:00 PM ET)."""
        now = datetime.now()
        # Simple check: weekday and between 9:30 AM and 4:00 PM
        if now.weekday() >= 5:  # Saturday or Sunday
            return False
        
        market_open = time(9, 30)
        market_close = time(16, 0)
        current_time = now.time()
        
        return market_open <= current_time < market_close
    
    def run_recommendations(self) -> Dict:
        """
        Generate sector recommendations and optionally execute paper trades.
        
        Returns:
            Dict with recommendations and paper-trade execution details.
        """
        if not self._is_market_open():
            logger.info("Market is closed. Skipping recommendations.")
            return {"status": "market_closed"}
        
        try:
            logger.info("Generating market recommendations...")
            
            # Generate recommendations for top sectors
            sectors_to_analyze = [
                ("technology", "semiconductors"),
                ("financials", "banks"),
                ("healthcare", "pharma"),
            ]
            
            results = {
                "timestamp": datetime.utcnow().isoformat(),
                "recommendations": [],
                "trades_executed": [],
            }
            
            for sector, subsector in sectors_to_analyze:
                try:
                    logger.info(f"Analyzing {sector}/{subsector}...")
                    
                    report = self.recommendation_engine.build_sector_report(
                        sector=sector,
                        subsector=subsector,
                        live_sources=True,
                    )
                    
                    if not report:
                        continue
                    
                    # Extract top stock pick if available
                    if report.stocks and len(report.stocks) > 0:
                        top_pick = report.stocks[0]
                        
                        rec = {
                            "sector": sector,
                            "subsector": subsector,
                            "ticker": top_pick.get("ticker"),
                            "signal": report.sector_thesis[:100],  # Summary
                            "asset_class": "market",
                        }
                        results["recommendations"].append(rec)

                        if self.auto_execute:
                            ticker = top_pick.get("ticker")
                            if ticker:
                                signal = self._signal_from_thesis(report.sector_thesis, asset_class="market")
                                confidence = self._confidence_from_thesis(report.sector_thesis, asset_class="market")

                                if signal in {"BUY", "SELL"}:
                                    order = self.trading_executor.execute_signal(
                                        ticker=ticker,
                                        signal=signal,
                                        confidence=confidence,
                                        min_confidence=self.market_min_confidence,
                                        position_size_pct=self.market_position_size_pct,
                                        max_position_size_pct=self.market_max_position_size_pct,
                                        reason=f"Paper-trading market signal from {subsector} sector analysis",
                                    )

                                    if order:
                                        results["trades_executed"].append({
                                            "ticker": ticker,
                                            "order_id": order.order_id,
                                            "side": order.side,
                                            "qty": order.qty,
                                            "asset_class": "market",
                                        })
                
                except Exception as e:
                    logger.error(f"Error analyzing {sector}/{subsector}: {e}")
                    continue
            
            self.last_run = datetime.utcnow()
            self.last_recommendations = results
            logger.info(f"Market recommendations generated: {len(results['recommendations'])} sectors analyzed")

            if self.enable_crypto:
                crypto_results = self.run_crypto_recommendations()
                results["crypto"] = crypto_results
                results["trades_executed"].extend(crypto_results.get("trades_executed", []))
            
            return results
        
        except Exception as e:
            logger.error(f"Error in recommendation generation: {e}")
            return {"status": "error", "error": str(e)}

    def run_crypto_recommendations(self) -> Dict:
        """Generate crypto recommendations and paper-trade them with tighter risk limits."""
        results = {
            "timestamp": datetime.utcnow().isoformat(),
            "recommendations": [],
            "trades_executed": [],
        }

        if not self.enable_crypto:
            return {"status": "crypto_disabled", **results}

        try:
            for symbol in self.crypto_watchlist:
                try:
                    report = self.recommendation_engine.build_report([symbol], live_sources=True)
                    if not report.items:
                        continue

                    item = report.items[0]
                    thesis = item.thesis
                    signal = self._signal_from_thesis(thesis, asset_class="crypto")
                    confidence = self._confidence_from_thesis(thesis, asset_class="crypto")

                    rec = {
                        "asset_class": "crypto",
                        "ticker": symbol,
                        "signal": signal,
                        "thesis": thesis[:140],
                    }
                    results["recommendations"].append(rec)

                    if self.auto_execute and signal in {"BUY", "SELL"}:
                        order = self.trading_executor.execute_signal(
                            ticker=symbol,
                            signal=signal,
                            confidence=confidence,
                            min_confidence=self.crypto_min_confidence,
                            position_size_pct=self.crypto_position_size_pct,
                            max_position_size_pct=self.crypto_max_position_size_pct,
                            reason=f"Paper-trading crypto signal from unstructured data scan",
                        )
                        if order:
                            results["trades_executed"].append({
                                "asset_class": "crypto",
                                "ticker": symbol,
                                "order_id": order.order_id,
                                "side": order.side,
                                "qty": order.qty,
                            })
                except Exception as e:
                    logger.error(f"Error analyzing crypto {symbol}: {e}")
                    continue

            return results
        except Exception as e:
            logger.error(f"Error in crypto recommendation generation: {e}")
            return {"status": "error", "error": str(e), **results}
    
    def start(self, cron_expression: str = "0 * * * *"):
        """
        Start the scheduler.
        
        Args:
            cron_expression: Cron schedule for recommendations (default: every hour)
                            "0 * * * *" = every hour at minute 0
                            "0 10-16 * * 1-5" = every hour 10am-4pm weekdays
        """
        if self.scheduler.running:
            logger.warning("Scheduler is already running")
            return
        
        # Schedule market recommendations during market hours.
        self.scheduler.add_job(
            self.run_recommendations,
            trigger=CronTrigger.from_crontab(cron_expression),
            id="recommendation_job",
            name="Hourly sector recommendations",
            replace_existing=True,
        )

        if self.enable_crypto:
            self.scheduler.add_job(
                self.run_crypto_recommendations,
                trigger=CronTrigger.from_crontab(self.crypto_scan_cron),
                id="crypto_recommendation_job",
                name="Crypto paper-trade recommendations",
                replace_existing=True,
            )
        
        self.scheduler.start()
        logger.info(f"Scheduler started with cron: {cron_expression}")
    
    def stop(self):
        """Stop the scheduler."""
        if self.scheduler.running:
            self.scheduler.shutdown()
            logger.info("Scheduler stopped")
    
    def get_status(self) -> Dict:
        """
        Get scheduler status and last recommendations.
        
        Returns:
            Dict with running status and recent recommendations.
        """
        return {
            "running": self.scheduler.running,
            "last_run": self.last_run.isoformat() if self.last_run else None,
            "auto_execute": self.auto_execute,
            "min_confidence": self.min_confidence,
            "market_scan_cron": self.market_scan_cron,
            "crypto_scan_cron": self.crypto_scan_cron,
            "market_position_size_pct": self.market_position_size_pct,
            "market_max_position_size_pct": self.market_max_position_size_pct,
            "market_min_confidence": self.market_min_confidence,
            "crypto_position_size_pct": self.crypto_position_size_pct,
            "crypto_max_position_size_pct": self.crypto_max_position_size_pct,
            "crypto_min_confidence": self.crypto_min_confidence,
            "crypto_watchlist": self.crypto_watchlist,
            "enable_crypto": self.enable_crypto,
            "last_recommendations": self.last_recommendations,
        }

    def _signal_from_thesis(self, thesis: str, asset_class: str) -> str:
        lowered = thesis.lower()
        if asset_class == "crypto":
            bullish = ["positive", "strength", "momentum", "upside", "breakout", "acceleration"]
            bearish = ["risk", "uncertain", "headwind", "decline", "weakness", "selloff"]
        else:
            bullish = ["positive", "strength", "growth", "demand", "momentum", "tailwind", "outperform"]
            bearish = ["risk", "uncertain", "headwind", "competition", "decline", "weakness"]

        if any(term in lowered for term in bullish):
            return "BUY"
        if any(term in lowered for term in bearish):
            return "SELL"
        return "HOLD"

    def _confidence_from_thesis(self, thesis: str, asset_class: str) -> float:
        lowered = thesis.lower()
        if asset_class == "crypto":
            if any(term in lowered for term in ["positive", "strength", "momentum", "breakout"]):
                return 0.90
            if any(term in lowered for term in ["growth", "upside", "acceleration"]):
                return 0.86
            return 0.50

        if any(term in lowered for term in ["positive", "strength", "growth", "demand", "tailwind"]):
            return 0.78
        if any(term in lowered for term in ["momentum", "outperform", "upside"]):
            return 0.72
        return 0.55
