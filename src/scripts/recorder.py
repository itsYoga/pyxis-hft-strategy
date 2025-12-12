"""
OKX Data Recorder for HFTBacktest
==================================
Records OKX WebSocket data in hftbacktest-compatible format.

Event codes use hftbacktest constants:
- EXCH_EVENT = 2147483648
- DEPTH_EVENT = 1
- TRADE_EVENT = 2
- BUY_EVENT = 536870912
- SELL_EVENT = 268435456
"""

import asyncio
import websockets
import json
import time
import numpy as np
import os

# HftBacktest event constants (must match hftbacktest library)
EXCH_EVENT = 2147483648       # Exchange event flag
LOCAL_EVENT = 1073741824      # Local event flag
DEPTH_EVENT = 1               # Depth update
TRADE_EVENT = 2               # Trade event
DEPTH_CLEAR_EVENT = 3         # Clear depth
DEPTH_SNAPSHOT_EVENT = 4      # Snapshot
BUY_EVENT = 536870912         # Buy side
SELL_EVENT = 268435456        # Sell side


async def record_okx_stream(inst_id, output_dir):
    """
    Record OKX WebSocket stream to files compatible with hftbacktest.
    
    Args:
        inst_id: OKX instrument ID (e.g., "BTC-USDT-SWAP")
        output_dir: Directory to save data files
    """
    url = "wss://ws.okx.com:8443/ws/v5/public"
    
    os.makedirs(output_dir, exist_ok=True)
    
    current_file_ts = int(time.time())
    buffer = []
    BATCH_SIZE = 10000
    
    # Data type matching hftbacktest format
    dtype = np.dtype([
        ('ev', 'u8'),
        ('exch_ts', 'i8'),
        ('local_ts', 'i8'),
        ('px', 'f8'),
        ('qty', 'f8'),
        ('order_id', 'u8'),
        ('ival', 'i8'),
        ('fval', 'f8')
    ])
    
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
                local_ts = time.time_ns()
                
                msg = json.loads(msg_raw)
                if 'data' not in msg:
                    continue
                
                channel = msg['arg']['channel']
                
                # Process Trades
                if channel == 'trades':
                    for trade in msg['data']:
                        exch_ts = int(trade['ts']) * 1_000_000  # ms -> ns
                        px = float(trade['px'])
                        sz = float(trade['sz'])
                        
                        # Correct event code: EXCH | TRADE | SIDE
                        if trade['side'] == 'buy':
                            ev = EXCH_EVENT | TRADE_EVENT | BUY_EVENT
                        else:
                            ev = EXCH_EVENT | TRADE_EVENT | SELL_EVENT
                        
                        buffer.append((ev, exch_ts, local_ts, px, sz, 0, 0, 0.0))

                # Process Depth (L2 Incremental)
                elif channel == 'books-l2-tbt':
                    data = msg['data'][0] if isinstance(msg['data'], list) else msg['data']
                    exch_ts = int(data['ts']) * 1_000_000
                    action = data.get('action', 'update')
                    
                    # Determine event type
                    if action == 'snapshot':
                        base_event = EXCH_EVENT | DEPTH_SNAPSHOT_EVENT
                    else:
                        base_event = EXCH_EVENT | DEPTH_EVENT
                    
                    # Process Bids (buy side)
                    for item in data.get('bids', []):
                        px = float(item[0])
                        qty = float(item[1])
                        ev = base_event | BUY_EVENT
                        buffer.append((ev, exch_ts, local_ts, px, qty, 0, 0, 0.0))
                    
                    # Process Asks (sell side)
                    for item in data.get('asks', []):
                        px = float(item[0])
                        qty = float(item[1])
                        ev = base_event | SELL_EVENT
                        buffer.append((ev, exch_ts, local_ts, px, qty, 0, 0, 0.0))

                # Write to disk periodically
                if len(buffer) >= BATCH_SIZE:
                    data_array = np.array(buffer, dtype=dtype)
                    filename = os.path.join(output_dir, f"okx_{inst_id}_{current_file_ts}.npz")
                    np.savez_compressed(filename, data=data_array)
                    print(f"Saved {len(buffer)} events to {filename}")
                    
                    buffer.clear()
                    current_file_ts = int(time.time())

            except websockets.exceptions.ConnectionClosed as e:
                print(f"Connection closed: {e}")
                break
            except Exception as e:
                print(f"Error: {e}")
                continue


if __name__ == "__main__":
    import argparse
    parser = argparse.ArgumentParser(description="Record OKX data for HFTBacktest")
    parser.add_argument("--symbol", type=str, default="BTC-USDT-SWAP", help="OKX Instrument ID")
    parser.add_argument("--output", type=str, default="data/okx", help="Output directory")
    args = parser.parse_args()
    
    print(f"Recording {args.symbol} to {args.output}")
    print("Press Ctrl+C to stop recording")
    
    try:
        asyncio.run(record_okx_stream(args.symbol, args.output))
    except KeyboardInterrupt:
        print("\nRecording stopped by user.")
