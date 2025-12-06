"""
OKX Live Trading Bot
====================
連接 OKX Demo Trading (Sandbox) 執行自動交易策略

使用方法:
    python live_trading.py

環境變數 (在 .env 檔案中設定):
    OKX_API_KEY - Trade 權限的 API Key
    OKX_SECRET_KEY - Secret Key
    OKX_PASSPHRASE - API 密碼
"""

import asyncio
import json
import time
import hmac
import base64
import hashlib
from datetime import datetime
import websockets
import os

try:
    from dotenv import load_dotenv
    load_dotenv()
except ImportError:
    pass

# Configuration
API_KEY = os.getenv('OKX_API_KEY', '')
SECRET_KEY = os.getenv('OKX_SECRET_KEY', '')
PASSPHRASE = os.getenv('OKX_PASSPHRASE', '')
SYMBOL = os.getenv('SYMBOL', 'BTC-USDT-SWAP')
IS_SANDBOX = os.getenv('SANDBOX', 'true').lower() == 'true'

# OKX WebSocket URLs
if IS_SANDBOX:
    WS_PUBLIC = "wss://wspap.okx.com:8443/ws/v5/public?brokerId=9999"
    WS_PRIVATE = "wss://wspap.okx.com:8443/ws/v5/private?brokerId=9999"
    REST_URL = "https://www.okx.com"  # Sandbox uses same URL with simulated header
else:
    WS_PUBLIC = "wss://ws.okx.com:8443/ws/v5/public"
    WS_PRIVATE = "wss://ws.okx.com:8443/ws/v5/private"
    REST_URL = "https://www.okx.com"


def generate_signature(timestamp, method, request_path, body=''):
    """Generate OKX API signature"""
    message = timestamp + method + request_path + body
    mac = hmac.new(
        bytes(SECRET_KEY, encoding='utf8'),
        bytes(message, encoding='utf-8'),
        digestmod='sha256'
    )
    return base64.b64encode(mac.digest()).decode()


def get_login_params():
    """Generate login parameters for private WebSocket"""
    timestamp = str(int(time.time()))
    sign = generate_signature(timestamp, 'GET', '/users/self/verify')
    return {
        "op": "login",
        "args": [{
            "apiKey": API_KEY,
            "passphrase": PASSPHRASE,
            "timestamp": timestamp,
            "sign": sign
        }]
    }


class OKXTradingBot:
    def __init__(self):
        self.symbol = SYMBOL
        self.best_bid = 0.0
        self.best_ask = 0.0
        self.best_bid_qty = 0.0
        self.best_ask_qty = 0.0
        self.position = 0.0
        self.balance = 0.0
        self.running = True
        
        # Strategy parameters
        self.gamma = 0.1
        self.k = 1.5
        self.alpha_weight = 0.3
        self.max_position = 10.0
        self.order_qty = 0.01
        
        # Order tracking
        self.active_orders = {}
        self.order_id_counter = 1
        
    async def connect_public(self):
        """Connect to public WebSocket for market data"""
        print(f"\n📡 Connecting to OKX Public WebSocket...")
        print(f"   Symbol: {self.symbol}")
        print(f"   Sandbox: {IS_SANDBOX}")
        
        async with websockets.connect(WS_PUBLIC) as ws:
            # Subscribe to order book
            subscribe_msg = {
                "op": "subscribe",
                "args": [
                    {"channel": "books5", "instId": self.symbol}
                ]
            }
            await ws.send(json.dumps(subscribe_msg))
            print(f"✅ Subscribed to {self.symbol} order book")
            
            while self.running:
                try:
                    msg = await asyncio.wait_for(ws.recv(), timeout=30)
                    data = json.loads(msg)
                    
                    if 'data' in data:
                        self.process_orderbook(data['data'][0])
                        
                except asyncio.TimeoutError:
                    # Send ping
                    await ws.send('ping')
                    
    def process_orderbook(self, data):
        """Process order book update"""
        if 'bids' in data and len(data['bids']) > 0:
            self.best_bid = float(data['bids'][0][0])
            self.best_bid_qty = float(data['bids'][0][1])
            
        if 'asks' in data and len(data['asks']) > 0:
            self.best_ask = float(data['asks'][0][0])
            self.best_ask_qty = float(data['asks'][0][1])
    
    async def connect_private(self):
        """Connect to private WebSocket for trading"""
        print(f"\n🔐 Connecting to OKX Private WebSocket...")
        
        async with websockets.connect(WS_PRIVATE) as ws:
            # Login
            login_msg = get_login_params()
            await ws.send(json.dumps(login_msg))
            
            response = await ws.recv()
            result = json.loads(response)
            
            if result.get('event') == 'login' and result.get('code') == '0':
                print("✅ Login successful!")
            else:
                print(f"❌ Login failed: {result}")
                return
            
            # Subscribe to orders and positions
            subscribe_msg = {
                "op": "subscribe",
                "args": [
                    {"channel": "orders", "instType": "SWAP", "instId": self.symbol},
                    {"channel": "positions", "instType": "SWAP", "instId": self.symbol}
                ]
            }
            await ws.send(json.dumps(subscribe_msg))
            print("✅ Subscribed to orders and positions")
            
            while self.running:
                try:
                    msg = await asyncio.wait_for(ws.recv(), timeout=30)
                    data = json.loads(msg)
                    self.process_private_message(data)
                    
                except asyncio.TimeoutError:
                    await ws.send('ping')
                    
    def process_private_message(self, data):
        """Process private channel messages"""
        if 'data' not in data:
            return
            
        channel = data.get('arg', {}).get('channel', '')
        
        if channel == 'positions':
            for pos in data['data']:
                if pos.get('instId') == self.symbol:
                    self.position = float(pos.get('pos', 0))
                    
        elif channel == 'orders':
            for order in data['data']:
                state = order.get('state', '')
                if state in ['filled', 'canceled']:
                    order_id = order.get('clOrdId', '')
                    if order_id in self.active_orders:
                        del self.active_orders[order_id]
                        
    async def trading_loop(self):
        """Main trading strategy loop"""
        print(f"\n🚀 Starting trading strategy...")
        print(f"   Parameters: gamma={self.gamma}, k={self.k}, alpha_weight={self.alpha_weight}")
        
        while self.running:
            await asyncio.sleep(0.5)  # 500ms intervals
            
            if self.best_bid == 0 or self.best_ask == 0:
                continue
                
            # Calculate mid price
            mid_price = (self.best_bid + self.best_ask) / 2.0
            
            # Calculate Alpha signals
            if self.best_bid_qty + self.best_ask_qty > 0:
                micro_price = (
                    self.best_bid * self.best_ask_qty + 
                    self.best_ask * self.best_bid_qty
                ) / (self.best_bid_qty + self.best_ask_qty)
                
                alpha_micro = (micro_price - mid_price)
                bbo_imbalance = (
                    self.best_bid_qty - self.best_ask_qty
                ) / (self.best_bid_qty + self.best_ask_qty)
            else:
                alpha_micro = 0
                bbo_imbalance = 0
            
            # Forecast
            forecast = self.alpha_weight * (alpha_micro + bbo_imbalance * 0.5)
            
            # Calculate reservation price (AS model + Alpha)
            tick_size = 0.1
            reservation_price = (
                mid_price 
                + forecast
                - self.position * self.gamma * 1.0
            )
            
            # Calculate spread
            half_spread = (2.0 / self.gamma) * (1.0 + self.gamma / self.k) / 2.0
            
            bid_price = round(reservation_price - half_spread, 1)
            ask_price = round(reservation_price + half_spread, 1)
            
            # Log status
            timestamp = datetime.now().strftime("%H:%M:%S")
            print(f"\r[{timestamp}] Mid: {mid_price:.1f} | Bid: {bid_price:.1f} | Ask: {ask_price:.1f} | Pos: {self.position:.4f} | Imb: {bbo_imbalance:+.3f}", end='')
            
            # Place orders (in real trading, you would send orders here)
            # For now, we just log
            
    async def run(self):
        """Run the trading bot"""
        print("\n" + "="*50)
        print("🤖 Pyxis HFT Trading Bot")
        print("="*50)
        print(f"Symbol: {self.symbol}")
        print(f"Sandbox Mode: {IS_SANDBOX}")
        print(f"API Key: {API_KEY[:8]}...")
        print("="*50)
        
        if not API_KEY or not SECRET_KEY:
            print("\n❌ Error: API credentials not configured!")
            print("   Please set up your .env file")
            return
        
        try:
            # Run all tasks concurrently
            await asyncio.gather(
                self.connect_public(),
                self.connect_private(),
                self.trading_loop()
            )
        except KeyboardInterrupt:
            print("\n\n⏹️  Stopping bot...")
            self.running = False
        except Exception as e:
            print(f"\n❌ Error: {e}")
            self.running = False


async def test_connection():
    """Test OKX connection without trading"""
    print("\n🔍 Testing OKX Connection...")
    print(f"   Sandbox: {IS_SANDBOX}")
    print(f"   API Key: {API_KEY[:8]}..." if API_KEY else "   API Key: NOT SET")
    
    try:
        async with websockets.connect(WS_PUBLIC) as ws:
            # Subscribe to BTC ticker
            msg = {
                "op": "subscribe",
                "args": [{"channel": "tickers", "instId": "BTC-USDT-SWAP"}]
            }
            await ws.send(json.dumps(msg))
            
            for i in range(5):
                response = await asyncio.wait_for(ws.recv(), timeout=10)
                data = json.loads(response)
                if 'data' in data:
                    price = data['data'][0].get('last', 'N/A')
                    print(f"   BTC Price: {price}")
                    break
                    
            print("\n✅ Connection test successful!")
            
    except Exception as e:
        print(f"\n❌ Connection test failed: {e}")


if __name__ == "__main__":
    import sys
    
    if len(sys.argv) > 1 and sys.argv[1] == '--test':
        asyncio.run(test_connection())
    else:
        bot = OKXTradingBot()
        asyncio.run(bot.run())
