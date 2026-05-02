# Deployment Guide: Live Trading Dashboard

This guide explains how to deploy the backend to Render and the frontend to Firebase Hosting.

## Prerequisites

1. **Alpaca Account** (Free Paper Trading)
   - Sign up at https://alpaca.markets
   - Enable paper trading
   - Get your API keys from: https://app.alpaca.markets/brokerage/account/api-keys

2. **Render Account** (Backend Hosting)
   - Sign up at https://render.com (free tier available)
   - Connect your GitHub repository

3. **Firebase Account** (Frontend Hosting)
   - Sign up at https://console.firebase.google.com
   - Create a new project

4. **Local Setup**
   ```bash
   # Install Firebase CLI globally
   npm install -g firebase-tools
   
   # Install Python dependencies
   pip install -r requirements.txt
   pip install -e .
   ```

---

## Part 1: Deploy Backend to Render

### Step 1: Prepare Environment Variables

Before deploying, you'll need your Alpaca API credentials:
- `APCA_API_KEY_ID` - Your Alpaca API key ID
- `APCA_API_SECRET_KEY` - Your Alpaca API secret key
- `APCA_API_BASE_URL` - Set to `https://paper-api.alpaca.markets` for paper trading

### Step 2: Create Render Service

1. Go to https://dashboard.render.com
2. Click "New +" → "Web Service"
3. Connect your GitHub repository
4. Configure the service:
   - **Name**: `agentic-traversal-api`
   - **Environment**: `Python 3.9`
   - **Build Command**: 
     ```
       pip install -r requirements.txt && pip install -e .
     ```
   - **Start Command**: 
     ```
          python -m uvicorn --app-dir src quant_agent.api.main:app --host 0.0.0.0 --port $PORT
     ```
   - **Plan**: Free tier
5. Click "Advanced" and add environment variables:
   - `APCA_API_KEY_ID`: [your key]
   - `APCA_API_SECRET_KEY`: [your secret]
   - `APCA_API_BASE_URL`: `https://paper-api.alpaca.markets`
   - `TRADING_MARKET_SCAN_CRON`: `*/5 * * * *`
   - `TRADING_CRYPTO_SCAN_CRON`: `*/15 * * * *`
   - `TRADING_MARKET_POSITION_SIZE_PCT`: `0.12`
   - `TRADING_MARKET_MAX_POSITION_SIZE_PCT`: `0.35`
   - `TRADING_MARKET_MIN_CONFIDENCE`: `0.62`
   - `TRADING_CRYPTO_POSITION_SIZE_PCT`: `0.02`
   - `TRADING_CRYPTO_MAX_POSITION_SIZE_PCT`: `0.05`
   - `TRADING_CRYPTO_MIN_CONFIDENCE`: `0.88`
   - `TRADING_CRYPTO_WATCHLIST`: `BTC-USD,ETH-USD,SOL-USD,DOGE-USD,XRP-USD`
   - `TRADING_ENABLE_CRYPTO`: `true`

### Step 3: Deploy

Click "Create Web Service" and wait for deployment (5-10 minutes).

Your API will be live at: `https://agentic-traversal-api.onrender.com`

---

## Part 2: Deploy Frontend to Firebase

### Step 1: Initialize Firebase Project

```bash
# Login to Firebase
firebase login

# Initialize Firebase in your project directory
firebase init hosting

# When prompted, choose:
# - Public directory: static
# - Configure as single-page app: Yes
# - Rewrite all URLs to index.html: Yes
```

### Step 2: Update Dashboard API URLs

Edit `static/trading-dashboard.html` and update the API_BASE variable to point to your Render URL. The Firebase site is read-only: it shows account, positions, trades, and scheduler status, but it does not expose any trade entry controls.

```javascript
// Replace line 214:
const API_BASE = 'https://agentic-traversal-api.onrender.com/';
```

### Step 3: Deploy Frontend

```bash
# Build (no build step needed for static files)

# Deploy to Firebase
firebase deploy --only hosting
```

Your dashboard will be live at: `https://[your-project-id].web.app/trading-dashboard.html`

---

## Part 3: Local Testing Before Deployment

### Test Backend Locally

```bash
# Set environment variables
export APCA_API_KEY_ID="your_key_id"
export APCA_API_SECRET_KEY="your_secret_key"
export APCA_API_BASE_URL="https://paper-api.alpaca.markets"

# Start the backend
python -m uvicorn --app-dir src quant_agent.api.main:app --reload

# Test endpoints
curl http://localhost:8000/health
curl http://localhost:8000/trading/account
```

### Test Frontend Locally

```bash
# Option 1: Use Python HTTP server
cd static
python -m http.server 8001

# Option 2: Use Firebase local emulator
firebase emulators:start --only hosting
```

Then visit: `http://localhost:8001/trading-dashboard.html` or `http://localhost:5000/trading-dashboard.html`

---

## API Endpoints Reference

### Account & Portfolio
- `GET /trading/account` - Get account info (equity, cash, buying power)
- `GET /trading/positions` - Get open positions with P&L
- `GET /trading/orders` - Get order history
- `GET /trading/trades` - Get trade execution log

### Order Execution
- `POST /trading/place-order` - Place a BUY/SELL order
  ```json
  {
    "symbol": "NVDA",
    "qty": 10,
    "side": "buy",
    "reason": "Optional explanation"
  }
  ```

### Scheduler Control
- `GET /trading/scheduler/status` - Get scheduler status
- `POST /trading/scheduler/start?cron=0%20*%20*%20*%20*` - Start hourly recommendations
  - Cron format: `minute hour day month weekday`
  - `0 * * * *` = Every hour at minute 0
  - `0 10-16 * * 1-5` = Every hour 10am-4pm on weekdays
- `POST /trading/scheduler/stop` - Stop the scheduler

---

## Dashboard Features

The live trading dashboard at `/trading-dashboard.html` includes:

1. **Account Overview**
   - Equity balance
   - Available cash
   - Buying power
   - Cash percentage

2. **Portfolio Tracking**
   - Open positions with P&L
   - Total portfolio gain/loss
   - Win rate and trade count

3. **Trade Execution**
   - Quick BUY/SELL form
   - Position sizing based on portfolio %
   - Order confirmation

4. **Scheduler Control**
   - Start/stop hourly recommendations
   - View last run timestamp
   - Live trade execution log

5. **Trade History**
   - All executed trades with timestamps
   - Signal type (BUY/SELL/HOLD)
   - Execution status and prices

---

## Monitoring & Troubleshooting

### Check Render Logs
```bash
# View logs in real-time
curl https://agentic-traversal-api.onrender.com/health
```

### Common Issues

**Issue**: Alpaca API returns 403 Unauthorized
- **Solution**: Check that API keys are correctly set in Render environment variables

**Issue**: Scheduler not executing trades
- **Solution**: Make sure market is open (9:30 AM - 4:00 PM ET, Monday-Friday)
- Check scheduler status at `/trading/scheduler/status`

**Issue**: Firebase deployment fails
- **Solution**: Run `firebase login` again and ensure you have the correct project ID
- Check `.firebaserc` file exists with correct project

---

## Production Recommendations

1. **Alpaca Configuration**
   - Set position size carefully (recommend starting with 1-5% per trade)
   - Enable rate limiting (Alpaca free tier has limits)
   - Monitor order fills carefully

2. **Render Configuration**
   - Upgrade to paid tier for 24/7 uptime if running scheduler
   - Enable auto-scaling for high traffic
   - Set up error monitoring/alerting

3. **Security**
   - Never commit API keys to git (use environment variables)
   - Use strong Firebase security rules
   - Enable CORS only for your dashboard domain

4. **Monitoring**
   - Set up Slack/email alerts for trade failures
   - Log all trades to a database for audit trails
   - Implement circuit breaker for portfolio risk

---

## Rolling Back

### Firebase Rollback
```bash
firebase hosting:channels:list
firebase hosting:clone from_channel to_channel
```

### Render Rollback
1. Go to Render dashboard
2. Click your service
3. Go to "Deploys" tab
4. Click "Rollback" on a previous deployment

---

## Cost Breakdown (As of May 2026)

| Service | Free Tier | Monthly Cost |
|---------|-----------|--------------|
| Render Backend | ✓ (first 750 hours/month) | $0 |
| Firebase Hosting | ✓ (1GB storage, 10GB bandwidth) | $0 |
| Alpaca Paper Trading | ✓ (unlimited) | $0 |
| **Total** | | **$0** |

---

## Next Steps

1. Deploy backend to Render
2. Deploy frontend to Firebase
3. Connect Alpaca API keys
4. Start scheduler to run hourly recommendations
5. Monitor P&L on the live dashboard

For questions, check the main [README.md](../README.md) and API documentation.
