"""
Trading Dashboard Route

Provides a live trading dashboard showing account, positions, and trade execution.
"""

from fastapi import APIRouter

router = APIRouter()


@router.get("/dashboard")
def trading_dashboard():
    """Provide dashboard URLs and API endpoints for live trading monitoring."""
    return {
        "message": "Open /trading-dashboard.html for start/stop controls and live evidence tabs.",
        "dashboards": {
            "live_trading": "/trading-dashboard.html",
            "agent_tracker": "/agent-tracker.html",
        },
        "api_endpoints": {
            "account": "/trading/account",
            "positions": "/trading/positions",
            "orders": "/trading/orders",
            "trades": "/trading/trades",
            "scheduler_status": "/trading/scheduler/status",
            "scheduler_start": "/trading/scheduler/start",
            "scheduler_stop": "/trading/scheduler/stop",
        }
    }
