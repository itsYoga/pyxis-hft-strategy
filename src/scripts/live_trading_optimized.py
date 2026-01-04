"""
OKX Live Trading Bot with Optimized Strategy
============================================
使用優化後的 Aggressive Market Making Strategy 進行 OKX Demo Trading

使用方法:
    1. 設置 .env 文件（參考 .env.example）
    2. 測試連線: python src/scripts/live_trading_optimized.py --test
    3. 啟動交易: python src/scripts/live_trading_optimized.py

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
import sys
import numpy as np
import aiohttp
import csv
from pathlib import Path

# Add src to path for imports
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..'))

try:
    from dotenv import load_dotenv
    load_dotenv()
except ImportError:
    pass

# Import trading utilities and logger
try:
    from utils.okx_trading import place_order, cancel_order, get_order_status
except ImportError:
    place_order = None
    cancel_order = None
    get_order_status = None

try:
    from utils.performance_logger import PerformanceLogger
except ImportError:
    PerformanceLogger = None

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
    REST_URL = "https://www.okx.com"
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


class OptimizedOKXTradingBot:
    """
    使用優化後的 Aggressive Market Making Strategy
    
    優化包括:
    - 二次庫存懲罰 (Quadratic Inventory Penalty)
    - 反嗅探邏輯 (Anti-Sniffing Logic)
    - 指數衰減 MLOFI (Exponential Decay MLOFI)
    """
    
    def __init__(self):
        self.symbol = SYMBOL
        self.best_bid = 0.0
        self.best_ask = 0.0
        self.best_bid_qty = 0.0
        self.best_ask_qty = 0.0
        
        # Order book depth (5 levels for MLOFI)
        self.bids = []
        self.asks = []
        
        self.position = 0.0
        self.balance = 0.0
        self.running = True
        
        # Strategy parameters (from aggressive.py)
        self.tick_size = 0.1
        self.lot_size = 0.001
        self.gamma_base = 0.05
        self.k_base = 1.5
        self.max_position = 10.0
        self.order_qty = 0.01
        
        # Alpha weights
        self.micro_weight = 0.2
        self.mlofi_weight = 0.8
        self.num_levels = 5
        
        # Optimization flags
        self.use_quadratic_penalty = True
        self.use_anti_sniffing = True
        self.use_exponential_decay_mlofi = True
        self.lambda_read = 0.3
        self.max_skew_penalty = 0.5
        self.alpha_decay = 0.5
        
        # State variables
        self.mid_price_buffer = np.zeros(1000, dtype=np.float64)
        self.buffer_idx = 0
        self.is_buffer_full = False
        self.ewma_volatility = self.tick_size * 10
        self.ewma_slope = 1.0
        
        # Order tracking
        self.active_orders = {}
        self.order_id_counter = 1
        self.current_bid_order_id = None
        self.current_ask_order_id = None
        self.last_bid_price = None
        self.last_ask_price = None
        
        # Enable actual trading (set to False to disable)
        self.enable_trading = os.getenv('ENABLE_TRADING', 'false').lower() == 'true'
        
        # Performance logging
        self.logger = None
        if PerformanceLogger:
            try:
                self.logger = PerformanceLogger()
                print(f"[OK] Performance logging enabled: {self.logger.csv_file}")
            except Exception as e:
                print(f"[WARN] Performance logging disabled: {e}")
        
        # HTTP session for REST API
        self.session = None
        
    async def connect_public(self):
        """Connect to public WebSocket for market data"""
        print(f"\n[INFO] Connecting to OKX Public WebSocket...")
        print(f"   Symbol: {self.symbol}")
        print(f"   Sandbox: {IS_SANDBOX}")
        
        async with websockets.connect(WS_PUBLIC) as ws:
            # Subscribe to order book (5 levels for MLOFI)
            subscribe_msg = {
                "op": "subscribe",
                "args": [
                    {"channel": "books5", "instId": self.symbol}
                ]
            }
            await ws.send(json.dumps(subscribe_msg))
            print(f"[OK] Subscribed to {self.symbol} order book (5 levels)")
            
            while self.running:
                try:
                    msg = await asyncio.wait_for(ws.recv(), timeout=30)
                    
                    # Handle ping/pong messages (not JSON)
                    if msg == 'pong' or msg == 'ping':
                        continue
                    
                    # Skip empty messages
                    if not msg or len(msg.strip()) == 0:
                        continue
                    
                    try:
                        data = json.loads(msg)
                        
                        if 'data' in data:
                            self.process_orderbook(data['data'][0])
                    except json.JSONDecodeError:
                        # Log non-JSON messages for debugging
                        if msg != 'pong':
                            print(f"\n[WARN] Public WS non-JSON: {msg[:100]}")
                        continue
                        
                except asyncio.TimeoutError:
                    await ws.send('ping')
                    
    def process_orderbook(self, data):
        """Process order book update (5 levels)"""
        if 'bids' in data and len(data['bids']) > 0:
            self.bids = [[float(b[0]), float(b[1])] for b in data['bids'][:5]]
            self.best_bid = self.bids[0][0]
            self.best_bid_qty = self.bids[0][1]
            
        if 'asks' in data and len(data['asks']) > 0:
            self.asks = [[float(a[0]), float(a[1])] for a in data['asks'][:5]]
            self.best_ask = self.asks[0][0]
            self.best_ask_qty = self.asks[0][1]
    
    def calculate_mlofi(self):
        """Calculate Multi-Level Order Flow Imbalance"""
        if len(self.bids) < self.num_levels or len(self.asks) < self.num_levels:
            return 0.0
        
        mlofi = 0.0
        
        for i in range(min(self.num_levels, len(self.bids), len(self.asks))):
            bid_price, bid_qty = self.bids[i]
            ask_price, ask_qty = self.asks[i]
            
            if bid_qty + ask_qty > 0:
                level_imbalance = (bid_qty - ask_qty) / (bid_qty + ask_qty)
                
                # Exponential decay weight
                if self.use_exponential_decay_mlofi:
                    weight = np.exp(-self.alpha_decay * i)
                else:
                    weight = 0.7 ** i  # Power decay
                
                mlofi += weight * level_imbalance
        
        return mlofi
    
    def calculate_micro_price(self):
        """Calculate Micro Price"""
        if self.best_bid_qty + self.best_ask_qty > 0:
            return (
                self.best_bid * self.best_ask_qty + 
                self.best_ask * self.best_bid_qty
            ) / (self.best_bid_qty + self.best_ask_qty)
        return (self.best_bid + self.best_ask) / 2.0
    
    def calculate_volatility(self, mid_price):
        """Calculate EWMA volatility"""
        self.mid_price_buffer[self.buffer_idx] = mid_price
        self.buffer_idx += 1
        if self.buffer_idx >= len(self.mid_price_buffer):
            self.buffer_idx = 0
            self.is_buffer_full = True
        
        if self.is_buffer_full:
            returns = np.diff(self.mid_price_buffer)
            variance = np.var(returns)
            volatility = np.sqrt(variance) if variance > 0 else self.tick_size * 10
            self.ewma_volatility = 0.9 * self.ewma_volatility + 0.1 * volatility
        else:
            self.ewma_volatility = self.tick_size * 10
        
        return self.ewma_volatility
    
    def calculate_reservation_price(self, mid_price, forecast, volatility):
        """Calculate reservation price with optimizations"""
        position_factor = abs(self.position) / self.max_position if self.max_position > 0 else 0.0
        
        # Base inventory adjustment
        inventory_adjustment = self.position * self.gamma_base * (volatility ** 2)
        
        # Quadratic penalty
        if self.use_quadratic_penalty:
            inventory_adjustment *= (1.0 + position_factor)
        
        reservation_price = mid_price + forecast * self.tick_size - inventory_adjustment
        
        return reservation_price
    
    def calculate_spread(self, volatility):
        """Calculate optimal spread"""
        half_spread = (2.0 / self.gamma_base) * np.log(1.0 + self.gamma_base / self.k_base) / 2.0
        
        # Skew based on position
        normalized_position = self.position / self.max_position if self.max_position > 0 else 0.0
        skew = 0.2 * normalized_position
        
        # Anti-sniffing adjustment
        bid_sniff_adjust = 0.0
        ask_sniff_adjust = 0.0
        
        if self.use_anti_sniffing:
            obvious_skew = abs(skew)
            sniff_penalty = self.lambda_read * obvious_skew * self.tick_size
            sniff_penalty = max(-self.max_skew_penalty * self.tick_size, 
                              min(self.max_skew_penalty * self.tick_size, sniff_penalty))
            
            # Apply penalty to mask inventory
            if self.position > 0:  # Long position
                bid_sniff_adjust = sniff_penalty
                ask_sniff_adjust = -sniff_penalty
            elif self.position < 0:  # Short position
                bid_sniff_adjust = -sniff_penalty
                ask_sniff_adjust = sniff_penalty
        
        return half_spread, skew, bid_sniff_adjust, ask_sniff_adjust
    
    async def trading_loop(self):
        """Main trading strategy loop with optimizations"""
        print(f"\n[INFO] Starting Optimized Trading Strategy...")
        print(f"   Strategy: Aggressive Market Making (Optimized)")
        print(f"   Optimizations: Quadratic Penalty, Anti-Sniffing, Exponential MLOFI")
        print(f"   Parameters: gamma={self.gamma_base}, k={self.k_base}, max_pos={self.max_position}")
        
        while self.running:
            await asyncio.sleep(0.5)  # 500ms intervals
            
            if self.best_bid == 0 or self.best_ask == 0 or len(self.bids) < 5 or len(self.asks) < 5:
                continue
            
            # Calculate mid price
            mid_price = (self.best_bid + self.best_ask) / 2.0
            
            # Calculate Alpha signals
            micro_price = self.calculate_micro_price()
            alpha_micro = (micro_price - mid_price) / self.tick_size
            
            mlofi = self.calculate_mlofi()
            
            # Combined forecast
            forecast = self.micro_weight * alpha_micro + self.mlofi_weight * mlofi
            
            # Calculate volatility
            volatility = self.calculate_volatility(mid_price)
            
            # Calculate reservation price (with optimizations)
            reservation_price = self.calculate_reservation_price(mid_price, forecast, volatility)
            
            # Calculate spread (with anti-sniffing)
            half_spread, skew, bid_sniff_adjust, ask_sniff_adjust = self.calculate_spread(volatility)
            
            # Calculate bid/ask prices
            bid_price = reservation_price - half_spread * (1 + skew) + bid_sniff_adjust
            ask_price = reservation_price + half_spread * (1 - skew) + ask_sniff_adjust
            
            # Round to tick size
            bid_price = round(bid_price / self.tick_size) * self.tick_size
            ask_price = round(ask_price / self.tick_size) * self.tick_size
            
            # Ensure bid < ask
            if bid_price >= ask_price:
                bid_price = mid_price - self.tick_size
                ask_price = mid_price + self.tick_size
            
            # Log status
            timestamp = datetime.now().strftime("%H:%M:%S")
            trading_status = "[TRADING]" if self.enable_trading else "[OBSERVE]"
            print(f"\r[{timestamp}] {trading_status} Mid: {mid_price:.1f} | Bid: {bid_price:.1f} | Ask: {ask_price:.1f} | "
                  f"Pos: {self.position:.4f} | MLOFI: {mlofi:+.3f} | Vol: {volatility:.2f}", end='', flush=True)
            
            # Log performance data
            if self.logger:
                try:
                    self.logger.log({
                        'mid_price': mid_price,
                        'bid_price': bid_price,
                        'ask_price': ask_price,
                        'position': self.position,
                        'mlofi': mlofi,
                        'volatility': volatility,
                        'reservation_price': reservation_price,
                        'spread': ask_price - bid_price,
                        'skew': skew,
                        'balance': self.balance,
                        'equity': self.balance + self.position * mid_price,
                        'pnl': (self.balance + self.position * mid_price) - 30000.0,  # Assuming initial capital
                    })
                except Exception as e:
                    pass  # Silently fail logging
            
            # Place orders if enabled
            if self.enable_trading and place_order:
                await self.update_orders(bid_price, ask_price)
            
    async def connect_private(self):
        """Connect to private WebSocket for trading"""
        print(f"\n[INFO] Connecting to OKX Private WebSocket...")
        
        async with websockets.connect(WS_PRIVATE) as ws:
            # Login
            login_msg = get_login_params()
            await ws.send(json.dumps(login_msg))
            
            response = await ws.recv()
            result = json.loads(response)
            
            if result.get('event') == 'login' and result.get('code') == '0':
                print("[OK] Login successful!")
            else:
                print(f"[ERROR] Login failed: {result}")
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
            print("[OK] Subscribed to orders and positions")
            
            while self.running:
                try:
                    msg = await asyncio.wait_for(ws.recv(), timeout=30)
                    
                    # Handle ping/pong messages (not JSON)
                    if msg == 'pong' or msg == 'ping':
                        continue
                    
                    # Skip empty messages
                    if not msg or len(msg.strip()) == 0:
                        continue
                    
                    try:
                        data = json.loads(msg)
                        self.process_private_message(data)
                    except json.JSONDecodeError:
                        # Log non-JSON messages for debugging
                        if msg != 'pong':
                            print(f"\n[WARN] Received non-JSON message: {msg[:100]}")
                        continue
                    
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
                        
    async def run(self):
        """Run the trading bot"""
        print("\n" + "="*60)
        print("HFT Trading Bot (Optimized Strategy)")
        print("="*60)
        print(f"Symbol: {self.symbol}")
        print(f"Sandbox Mode: {IS_SANDBOX}")
        print(f"API Key: {API_KEY[:8]}..." if API_KEY else "API Key: NOT SET")
        print("="*60)
        
        if not API_KEY or not SECRET_KEY:
            print("\n[ERROR] API credentials not configured!")
            print("   Please set up your .env file:")
            print("   1. Copy .env.example to .env")
            print("   2. Fill in your OKX Demo Trading API credentials")
            return
        
        try:
            # Run all tasks concurrently
            await asyncio.gather(
                self.connect_public(),
                self.connect_private(),
                self.trading_loop()
            )
        except KeyboardInterrupt:
            print("\n\n[INFO] Stopping bot...")
            self.running = False
        except Exception as e:
            print(f"\n[ERROR] Error: {e}")
            import traceback
            traceback.print_exc()
            self.running = False
        finally:
            # Cleanup
            if self.session:
                await self.session.close()
            if self.logger:
                self.logger.close()
                print(f"\n[OK] Performance data saved to {self.logger.csv_file}")


async def test_connection():
    """Test OKX connection without trading"""
    print("\n[INFO] Testing OKX Connection...")
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
                    
            print("\n[OK] Connection test successful!")
            
    except Exception as e:
        print(f"\n[ERROR] Connection test failed: {e}")
        print("\n請檢查:")
        print("1. .env 文件是否正確設置")
        print("2. API credentials 是否正確")
        print("3. 網絡連接是否正常")


if __name__ == "__main__":
    if len(sys.argv) > 1 and sys.argv[1] == '--test':
        asyncio.run(test_connection())
    else:
        bot = OptimizedOKXTradingBot()
        asyncio.run(bot.run())

