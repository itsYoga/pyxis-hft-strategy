import asyncio
import websockets
import json
import time
import numpy as np
import os
from datetime import datetime

# HftBacktest constants
EXCH_EVENT = 1
LOCAL_EVENT = 2
DEPTH_EVENT = 4
TRADE_EVENT = 8
BUY_EVENT = 16
SELL_EVENT = 32

async def record_okx_stream(inst_id, output_dir):
    url = "wss://ws.okx.com:8443/ws/v5/public"
    
    # Ensure output directory exists
    os.makedirs(output_dir, exist_ok=True)
    
    current_file_ts = int(time.time())
    buffer = []
    BATCH_SIZE = 10000
    
    print(f"Connecting to OKX for {inst_id}...")
    
    async with websockets.connect(url) as ws:
        # Subscribe to channels
        sub_param = {
            "op": "subscribe",
            "args": [
                {"channel": "books-l2-tbt", "instId": inst_id},
                {"channel": "trades", "instId": inst_id}
            ]
        }
        await ws.send(json.dumps(sub_param))
        print(f"Subscribed to {inst_id}. Recording to {output_dir}...")

        while True:
            try:
                msg_raw = await ws.recv()
                local_ts = time.time_ns() # Capture local timestamp immediately
                
                msg = json.loads(msg_raw)
                if 'data' not in msg:
                    continue
                
                channel = msg['arg']['channel']
                
                # Process Trades
                if channel == 'trades':
                    for trade in msg['data']:
                        exch_ts = int(trade['ts']) * 1_000_000 # ms -> ns
                        px = float(trade['px'])
                        sz = float(trade['sz'])
                        side = BUY_EVENT if trade['side'] == 'buy' else SELL_EVENT
                        
                        # ev, exch_ts, local_ts, px, qty, order_id, ival, fval
                        ev = EXCH_EVENT | TRADE_EVENT | side
                        buffer.append((ev, exch_ts, local_ts, px, sz, 0, 0, 0.0))

                # Process Depth (L2 Incremental)
                elif channel == 'books-l2-tbt':
                    exch_ts = int(msg['data']['ts']) * 1_000_000
                    
                    # Bids
                    for px, sz, _ in msg['data']['bids']:
                        ev = EXCH_EVENT | DEPTH_EVENT | BUY_EVENT
                        buffer.append((ev, exch_ts, local_ts, float(px), float(sz), 0, 0, 0.0))
                    
                    # Asks
                    for px, sz, _ in msg['data']['asks']:
                        ev = EXCH_EVENT | DEPTH_EVENT | SELL_EVENT
                        buffer.append((ev, exch_ts, local_ts, float(px), float(sz), 0, 0, 0.0))
                    
                    # Handle initial snapshot specifically if needed, 
                    # but hftbacktest usually treats the first messages as snapshot if they contain all levels.
                    # OKX 'action': 'snapshot' vs 'update'
                    if msg.get('action') == 'snapshot':
                        print("Received snapshot.")

                # Write to disk
                if len(buffer) >= BATCH_SIZE:
                    # Convert to numpy and save
                    # We save as raw chunks first, normalization can happen later or here.
                    # For simplicity/speed, let's just dump the list or a simple array.
                    # But the plan said "normalize.py" handles conversion. 
                    # So maybe we just save raw JSON lines? 
                    # The user prompt example code does conversion in-memory.
                    # Let's stick to the user's example which converts to numpy immediately.
                    
                    # Define dtype
                    dtype = [
                        ('ev', 'u8'),
                        ('exch_ts', 'i8'),
                        ('local_ts', 'i8'),
                        ('px', 'f8'),
                        ('qty', 'f8'),
                        ('order_id', 'u8'),
                        ('ival', 'i8'),
                        ('fval', 'f8')
                    ]
                    
                    data_array = np.array(buffer, dtype=dtype)
                    
                    filename = os.path.join(output_dir, f"okx_{inst_id}_{current_file_ts}.npz")
                    np.savez_compressed(filename, data=data_array)
                    print(f"Saved {len(buffer)} events to {filename}")
                    
                    buffer.clear()
                    current_file_ts = int(time.time())

            except Exception as e:
                print(f"Error: {e}")
                # Reconnect logic could go here
                break

if __name__ == "__main__":
    # Example usage
    # inst_id = "BTC-USDT-SWAP"
    # output_dir = "data"
    # asyncio.run(record_okx_stream(inst_id, output_dir))
    import argparse
    parser = argparse.ArgumentParser()
    parser.add_argument("--symbol", type=str, default="BTC-USDT-SWAP", help="OKX Instrument ID")
    parser.add_argument("--output", type=str, default="data", help="Output directory")
    args = parser.parse_args()
    
    try:
        asyncio.run(record_okx_stream(args.symbol, args.output))
    except KeyboardInterrupt:
        print("Recording stopped.")
