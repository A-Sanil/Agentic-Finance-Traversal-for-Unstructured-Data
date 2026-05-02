"""
Alpaca Trading API Client

Wrapper for paper trading integration with Alpaca Markets.
Supports account management, order placement, and portfolio tracking.
"""

import os
from typing import List, Dict, Optional, Any
from dataclasses import dataclass
from datetime import datetime

try:
    import alpaca_trade_api as tradeapi
except ImportError:
    tradeapi = None


@dataclass
class Position:
    """Represents a stock position in the portfolio."""
    symbol: str
    qty: float
    avg_fill_price: float
    current_price: float
    
    @property
    def market_value(self) -> float:
        return self.qty * self.current_price
    
    @property
    def cost_basis(self) -> float:
        return self.qty * self.avg_fill_price
    
    @property
    def gain_loss(self) -> float:
        return self.market_value - self.cost_basis
    
    @property
    def gain_loss_pct(self) -> float:
        if self.cost_basis == 0:
            return 0.0
        return (self.gain_loss / self.cost_basis) * 100


@dataclass
class Order:
    """Represents a completed or pending order."""
    order_id: str
    symbol: str
    qty: float
    side: str  # "buy" or "sell"
    status: str  # "pending_new", "filled", "canceled", etc.
    filled_qty: float
    filled_avg_price: float
    created_at: str
    filled_at: Optional[str] = None


@dataclass
class Account:
    """Account information and metrics."""
    account_number: str
    status: str
    cash: float
    portfolio_value: float
    buying_power: float
    
    @property
    def equity(self) -> float:
        return self.portfolio_value
    
    @property
    def cash_pct(self) -> float:
        if self.portfolio_value == 0:
            return 0.0
        return (self.cash / self.portfolio_value) * 100


class AlpacaClient:
    """
    Paper trading client for Alpaca Markets.
    
    Requires APCA_API_BASE_URL (paper trading endpoint)
    and APCA_API_KEY_ID + APCA_API_SECRET_KEY environment variables.
    """
    
    def __init__(self, paper_trading: bool = True):
        """
        Initialize Alpaca client.
        
        Args:
            paper_trading: If True, use paper trading endpoint (default).
        """
        if tradeapi is None:
            raise RuntimeError("alpaca-trade-api not installed. Run: pip install alpaca-trade-api")
        
        # Set paper trading endpoint if requested
        if paper_trading:
            os.environ.setdefault("APCA_API_BASE_URL", "https://paper-api.alpaca.markets")

        # Read API credentials from environment (do NOT hardcode keys in source)
        api_key = os.getenv("APCA_API_KEY_ID")
        api_secret = os.getenv("APCA_API_SECRET_KEY")
        base_url = os.getenv("APCA_API_BASE_URL")

        if not api_key or not api_secret:
            raise RuntimeError("Alpaca API keys not found in environment. Set APCA_API_KEY_ID and APCA_API_SECRET_KEY.")

        # Initialize API with explicit credentials
        try:
            # tradeapi.REST accepts (key_id, secret_key, base_url)
            self.api = tradeapi.REST(key_id=api_key, secret_key=api_secret, base_url=base_url)
        except Exception as e:
            raise RuntimeError(f"Failed to initialize Alpaca API: {e}. Check API keys and APCA_API_BASE_URL.")

        self.paper_trading = paper_trading
    
    def get_account(self) -> Account:
        """
        Fetch current account information.
        
        Returns:
            Account object with cash, equity, and buying power.
        """
        try:
            acct = self.api.get_account()
            return Account(
                account_number=acct.account_number,
                status=acct.status,
                cash=float(acct.cash),
                portfolio_value=float(acct.portfolio_value),
                buying_power=float(acct.buying_power),
            )
        except Exception as e:
            raise RuntimeError(f"Failed to fetch account: {e}")
    
    def get_positions(self) -> List[Position]:
        """
        Fetch all current positions.
        
        Returns:
            List of Position objects.
        """
        try:
            positions = self.api.list_positions()
            result = []
            for pos in positions:
                result.append(Position(
                    symbol=pos.symbol,
                    qty=float(pos.qty),
                    avg_fill_price=float(pos.avg_fill_price),
                    current_price=float(pos.current_price),
                ))
            return result
        except Exception as e:
            raise RuntimeError(f"Failed to fetch positions: {e}")
    
    def place_order(
        self,
        symbol: str,
        qty: float,
        side: str,
        order_type: str = "market",
        time_in_force: str = "day",
    ) -> Order:
        """
        Place an order on the paper account.
        
        Args:
            symbol: Stock ticker (e.g., "NVDA")
            qty: Order quantity
            side: "buy" or "sell"
            order_type: "market" or "limit" (default: "market")
            time_in_force: "day", "gtc", "opg", "cls" (default: "day")
        
        Returns:
            Order object with order details.
        """
        if qty <= 0:
            raise ValueError("Quantity must be positive")
        
        if side not in ["buy", "sell"]:
            raise ValueError("Side must be 'buy' or 'sell'")
        
        try:
            order = self.api.submit_order(
                symbol=symbol,
                qty=qty,
                side=side,
                type=order_type,
                time_in_force=time_in_force,
            )
            
            return Order(
                order_id=order.id,
                symbol=order.symbol,
                qty=float(order.qty),
                side=order.side,
                status=order.status,
                filled_qty=float(order.filled_qty),
                filled_avg_price=float(order.filled_avg_price) if order.filled_avg_price else 0.0,
                created_at=str(order.created_at),
                filled_at=str(order.filled_at) if order.filled_at else None,
            )
        except Exception as e:
            raise RuntimeError(f"Failed to place order for {symbol}: {e}")
    
    def get_orders(self, status: str = "all") -> List[Order]:
        """
        Fetch order history.
        
        Args:
            status: "open", "closed", or "all" (default: "all")
        
        Returns:
            List of Order objects.
        """
        try:
            orders = self.api.list_orders(status=status)
            result = []
            for ord in orders:
                result.append(Order(
                    order_id=ord.id,
                    symbol=ord.symbol,
                    qty=float(ord.qty),
                    side=ord.side,
                    status=ord.status,
                    filled_qty=float(ord.filled_qty),
                    filled_avg_price=float(ord.filled_avg_price) if ord.filled_avg_price else 0.0,
                    created_at=str(ord.created_at),
                    filled_at=str(ord.filled_at) if ord.filled_at else None,
                ))
            return result
        except Exception as e:
            raise RuntimeError(f"Failed to fetch orders: {e}")
    
    def cancel_order(self, order_id: str) -> bool:
        """
        Cancel a pending order.
        
        Args:
            order_id: ID of the order to cancel.
        
        Returns:
            True if successful, False otherwise.
        """
        try:
            self.api.cancel_order(order_id)
            return True
        except Exception as e:
            print(f"Failed to cancel order {order_id}: {e}")
            return False
    
    def get_latest_quote(self, symbol: str) -> Dict[str, Any]:
        """
        Fetch the latest quote for a symbol.
        
        Args:
            symbol: Stock ticker.
        
        Returns:
            Dict with bid, ask, last, volume info.
        """
        try:
            quote = self.api.get_last_quote(symbol)
            return {
                "symbol": symbol,
                "bid": float(quote.bid) if quote.bid else None,
                "ask": float(quote.ask) if quote.ask else None,
                "timestamp": str(quote.timestamp),
            }
        except Exception as e:
            print(f"Failed to fetch quote for {symbol}: {e}")
            return {}
    
    def close_position(self, symbol: str) -> Optional[Order]:
        """
        Close a position (sell all shares for long positions).
        
        Args:
            symbol: Stock ticker.
        
        Returns:
            Order object if successful, None otherwise.
        """
        try:
            positions = self.get_positions()
            position = next((p for p in positions if p.symbol == symbol), None)
            
            if not position:
                print(f"No position found for {symbol}")
                return None
            
            if position.qty <= 0:
                print(f"Position for {symbol} is already closed or short")
                return None
            
            # Sell all shares
            return self.place_order(symbol, position.qty, "sell")
        except Exception as e:
            print(f"Failed to close position for {symbol}: {e}")
            return None
