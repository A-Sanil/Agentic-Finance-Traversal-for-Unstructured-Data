"""
Trading Execution Engine

Converts recommendation signals into orders on the Alpaca paper account.
Includes position sizing, risk management, and trade logging.
"""

import json
import os
from datetime import datetime
from typing import Dict, List, Optional
from pathlib import Path

from quant_agent.trading.alpaca_client import AlpacaClient, Order, Position


class TradeLog:
    """Logs all executed trades for audit and analysis."""
    
    def __init__(self, log_file: str = "trades.jsonl"):
        self.log_file = Path(log_file)
        self.log_file.parent.mkdir(parents=True, exist_ok=True)
    
    def log_trade(
        self,
        ticker: str,
        signal: str,
        quantity: float,
        reason: str,
        order: Optional[Order] = None,
    ) -> None:
        """Log a trade execution."""
        entry = {
            "timestamp": datetime.utcnow().isoformat(),
            "ticker": ticker,
            "signal": signal,
            "quantity": quantity,
            "reason": reason,
            "order_id": order.order_id if order else None,
            "status": order.status if order else "error",
            "filled_price": order.filled_avg_price if order else None,
        }
        
        with open(self.log_file, "a") as f:
            f.write(json.dumps(entry) + "\n")
    
    def get_trades(self) -> List[Dict]:
        """Retrieve all logged trades."""
        if not self.log_file.exists():
            return []
        
        trades = []
        with open(self.log_file, "r") as f:
            for line in f:
                if line.strip():
                    trades.append(json.loads(line))
        return trades


class TradingExecutor:
    """
    Executes trades based on recommendation signals.
    
    Features:
    - Position sizing (% of portfolio or fixed qty)
    - Risk management (max position size, stop-loss)
    - Trade logging for audit trail
    - Safe execution with error handling
    """
    
    def __init__(
        self,
        alpaca_client: AlpacaClient,
        position_size_pct: float = 0.05,
        max_position_size_pct: float = 0.20,
        min_confidence: float = 0.50,
        log_file: str = "trades.jsonl",
    ):
        """
        Initialize trading executor.
        
        Args:
            alpaca_client: Alpaca API client instance
            position_size_pct: Percentage of portfolio to use per trade (default: 5%)
            max_position_size_pct: Maximum allowed position size as % of portfolio
            min_confidence: Minimum confidence required to execute a trade
            log_file: Path to trade log file
        """
        self.client = alpaca_client

        # Allow environment overrides for sizing and execution enablement
        env_pos = os.getenv("TRADING_POSITION_SIZE_PCT")
        env_max_pos = os.getenv("TRADING_MAX_POSITION_SIZE_PCT")
        env_min_conf = os.getenv("TRADING_MIN_CONFIDENCE")

        self.position_size_pct = float(env_pos) if env_pos is not None else position_size_pct
        self.max_position_size_pct = float(env_max_pos) if env_max_pos is not None else max_position_size_pct
        self.min_confidence = float(env_min_conf) if env_min_conf is not None else min_confidence
        self.trade_log = TradeLog(log_file)
    
    def calculate_position_size(
        self,
        account_value: float,
        price: float,
        position_size_pct: Optional[float] = None,
        max_position_size_pct: Optional[float] = None,
    ) -> float:
        """
        Calculate safe position size based on portfolio percentage.
        
        Args:
            account_value: Total portfolio value
            price: Current stock price
            position_size_pct: Optional override for target position size.
            max_position_size_pct: Optional override for max allowed position size.
        
        Returns:
            Number of shares to buy
        """
        target_pct = self.position_size_pct if position_size_pct is None else position_size_pct
        max_pct = self.max_position_size_pct if max_position_size_pct is None else max_position_size_pct

        max_dollar_amount = account_value * max_pct
        position_dollar_amount = account_value * target_pct
        
        qty = min(
            position_dollar_amount / price,
            max_dollar_amount / price,
        )
        
        return int(qty)
    
    def execute_signal(
        self,
        ticker: str,
        signal: str,
        confidence: float = 0.8,
        min_confidence: Optional[float] = None,
        position_size_pct: Optional[float] = None,
        max_position_size_pct: Optional[float] = None,
        reason: str = "",
    ) -> Optional[Order]:
        """
        Execute a BUY/SELL/HOLD signal.
        
        Args:
            ticker: Stock ticker
            signal: "BUY", "SELL", or "HOLD"
            confidence: Confidence score (0-1)
            min_confidence: Optional per-trade minimum confidence override.
            position_size_pct: Optional override for portfolio percentage sizing.
            max_position_size_pct: Optional override for max size sizing.
            reason: Explanation for the signal
        
        Returns:
            Order object if trade was placed, None otherwise.
        """
        # Global execution enable/disable (safety kill-switch)
        exec_enabled = os.getenv("TRADING_ENABLE_EXECUTION", "true").lower() == "true"
        if not exec_enabled:
            print("Trading execution disabled by TRADING_ENABLE_EXECUTION flag. Skipping execution.")
            self.trade_log.log_trade(ticker, signal, 0, "Execution disabled")
            return None

        if signal == "HOLD":
            self.trade_log.log_trade(ticker, "HOLD", 0, reason)
            return None
        
        confidence_floor = self.min_confidence if min_confidence is None else min_confidence
        if confidence < confidence_floor:
            print(f"Signal confidence {confidence:.1%} too low for {ticker}. Skipping.")
            return None
        
        try:
            # Get account and positions
            account = self.client.get_account()
            positions = self.client.get_positions()
            existing_position = next((p for p in positions if p.symbol == ticker), None)
            
            if signal == "BUY":
                # Calculate position size
                quote = self.client.get_latest_quote(ticker)
                if not quote or "ask" not in quote:
                    print(f"Could not fetch quote for {ticker}")
                    return None
                
                price = quote.get("ask", 0)
                if price <= 0:
                    print(f"Invalid price for {ticker}: {price}")
                    return None
                
                qty = self.calculate_position_size(
                    account.equity,
                    price,
                    position_size_pct=position_size_pct,
                    max_position_size_pct=max_position_size_pct,
                )
                
                if qty <= 0:
                    print(f"Calculated quantity is 0 for {ticker}. Skipping.")
                    return None
                
                # Check if we have buying power
                if qty * price > account.buying_power:
                    print(f"Insufficient buying power for {ticker}. Have ${account.buying_power:.2f}, need ${qty * price:.2f}")
                    return None
                
                # Place buy order
                order = self.client.place_order(ticker, qty, "buy")
                self.trade_log.log_trade(ticker, "BUY", qty, reason, order)
                print(f"✓ BUY order placed: {qty} shares of {ticker} at ~${price:.2f}")
                return order
            
            elif signal == "SELL":
                # Check if we have a position to sell
                if not existing_position or existing_position.qty <= 0:
                    print(f"No position to sell for {ticker}")
                    return None
                
                qty = existing_position.qty
                order = self.client.place_order(ticker, qty, "sell")
                self.trade_log.log_trade(ticker, "SELL", qty, reason, order)
                print(f"✓ SELL order placed: {qty} shares of {ticker}")
                return order
        
        except Exception as e:
            print(f"Error executing signal for {ticker}: {e}")
            self.trade_log.log_trade(ticker, signal, 0, f"Error: {e}")
            return None
    
    def get_trade_history(self) -> List[Dict]:
        """Get all executed trades."""
        return self.trade_log.get_trades()
    
    def get_summary(self) -> Dict:
        """
        Get summary of recent trading activity.
        
        Returns:
            Dict with trade count, P&L, win rate, etc.
        """
        trades = self.get_trade_history()
        
        if not trades:
            return {
                "total_trades": 0,
                "buy_orders": 0,
                "sell_orders": 0,
                "open_positions": 0,
            }
        
        buy_trades = [t for t in trades if t["signal"] == "BUY"]
        sell_trades = [t for t in trades if t["signal"] == "SELL"]
        
        # Get current positions
        try:
            positions = self.client.get_positions()
            account = self.client.get_account()
            
            total_gain = sum(p.gain_loss for p in positions)
            total_gain_pct = (total_gain / account.equity) * 100 if account.equity else 0
            
            return {
                "total_trades": len([t for t in trades if t["signal"] in ["BUY", "SELL"]]),
                "buy_orders": len(buy_trades),
                "sell_orders": len(sell_trades),
                "open_positions": len(positions),
                "total_position_gain_loss": total_gain,
                "total_position_gain_loss_pct": total_gain_pct,
                "account_equity": account.equity,
                "account_cash": account.cash,
                "buying_power": account.buying_power,
            }
        except Exception as e:
            print(f"Error fetching summary: {e}")
            return {
                "total_trades": len([t for t in trades if t["signal"] in ["BUY", "SELL"]]),
                "buy_orders": len(buy_trades),
                "sell_orders": len(sell_trades),
                "error": str(e),
            }
