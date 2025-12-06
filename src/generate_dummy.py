import numpy as np
import sys
from hftbacktest import (
    event_dtype,
    EXCH_EVENT,
    LOCAL_EVENT,
    DEPTH_EVENT,
    TRADE_EVENT,
    BUY_EVENT,
    SELL_EVENT,
    DEPTH_SNAPSHOT_EVENT
)

def generate_dummy_data(filename):
    # Generate 1 minute of data
    # 1000 events
    
    events = []
    
    start_ts = 1600000000 * 1_000_000_000 # ns
    
    mid_price = 10000.0
    
    # Use the official dtype
    dtype = event_dtype

    # Create snapshot data
    snapshot_events = []
    # hftbacktest usually expects a snapshot to build the initial book.
    # We can simulate it by sending a burst of depth updates with DEPTH_SNAPSHOT_EVENT or just DEPTH_EVENT if we use HashMapMarketDepthBacktest which handles incremental updates from start?
    # But usually it needs a clear state.
    # Let's use DEPTH_SNAPSHOT_EVENT (4) | EXCH_EVENT (1) = 5? No, DEPTH_SNAPSHOT_EVENT is a separate flag?
    # Let's check the value of DEPTH_SNAPSHOT_EVENT again. It was 4?
    # Wait, earlier I checked: DEPTH_EVENT=4.
    # What about DEPTH_SNAPSHOT_EVENT?
    # I ran `print(hftbacktest.DEPTH_SNAPSHOT_EVENT)` and it output `4`.
    # So DEPTH_SNAPSHOT_EVENT is same as DEPTH_EVENT?
    # Ah, maybe it's just how it's named in different versions.
    # But if I use `HashMapMarketDepthBacktest`, it should handle it.
    
    # The issue might be that `hftbacktest` skips until it sees a snapshot if configured?
    # Or maybe the timestamp is too far in the future/past?
    # 1600000000 is year 2020.
    
    # Let's try to add a specific snapshot event if possible.
    # Or maybe we need to set the `initial_snapshot` in `backtest.py`?
    # But we want to use the data stream itself.
    
    # Let's try to add a "snapshot" flag.
    # In `hftbacktest`, `DEPTH_SNAPSHOT_EVENT` usually indicates a snapshot.
    # If it's 4, then it's the same as `DEPTH_EVENT`.
    # Maybe `DEPTH_CLEAR_EVENT`?
    
    # Let's just ensure we have a valid order book at the start.
    # We are sending Bid and Ask updates.
    
    # Wait, `hftbacktest` might filter out events if `local_ts` < `start_time`?
    # But `start_time` is determined by the first event?
    
    # Let's try to use `DEPTH_SNAPSHOT_EVENT` explicitly if it's different.
    # But the tool output said 4.
    
    # Maybe the issue is `local_ts` vs `exch_ts`?
    # In my dummy data, they are equal.
    
    # Let's try to use `DEPTH_CLEAR_EVENT` before adding liquidity?
    # Or maybe `hftbacktest` requires `DEPTH_SNAPSHOT_EVENT` to be set on the first event to initialize?
    # If `DEPTH_EVENT` is 4, maybe `DEPTH_SNAPSHOT_EVENT` is something else in Rust?
    # But Python binding said 4.
    
    # Let's try to use a different timestamp.
    # Maybe 1600000000 is fine.
    
    # Let's try to add `DEPTH_SNAPSHOT_EVENT` explicitly.
    # And maybe `DEPTH_BBO_EVENT`?
    
    # Let's look at `example.py` again.
    # It uses `.initial_snapshot('data/btcusdt_20220830_eod.npz')`.
    # If we don't provide it, we might need to provide it in the data stream.
    
    # Let's update `generate_dummy.py` to create a separate snapshot file and use it.
    # This is the standard way.
    
    # Create snapshot data
    snapshot_events = []
    ts = start_ts
    
    # Snapshot: 10 levels
    for i in range(10):
        # Bid
        ev = EXCH_EVENT | DEPTH_SNAPSHOT_EVENT | BUY_EVENT
        snapshot_events.append((ev, ts, ts, mid_price - (i+1)*0.1, 1.0, 0, 0, 0.0))
        # Ask
        ev = EXCH_EVENT | DEPTH_SNAPSHOT_EVENT | SELL_EVENT
        snapshot_events.append((ev, ts, ts, mid_price + (i+1)*0.1, 1.0, 0, 0, 0.0))
        
    snapshot_data = np.array(snapshot_events, dtype=dtype)
    np.savez_compressed("dummy_snapshot.npz", data=snapshot_data)
    print(f"Generated snapshot to dummy_snapshot.npz")

    for i in range(1000):
        ts = start_ts + (i+1) * 10_000_000 # 10ms intervals
        
        # Add depth updates every step to keep the order book fresh
        # Simulate small price movements
        price_shift = np.sin(i * 0.01) * 2.0  # Oscillate +/- 2
        current_mid = mid_price + price_shift
        
        # Best bid update
        ev = EXCH_EVENT | DEPTH_EVENT | BUY_EVENT
        events.append((ev, ts, ts, current_mid - 0.1, 1.0, 0, 0, 0.0))
        
        # Best ask update
        ev = EXCH_EVENT | DEPTH_EVENT | SELL_EVENT
        events.append((ev, ts, ts, current_mid + 0.1, 1.0, 0, 0, 0.0))
        
        # Occasional Trade
        if i % 10 == 0:
            side = BUY_EVENT if np.random.rand() > 0.5 else SELL_EVENT
            ev = EXCH_EVENT | TRADE_EVENT | side
            px = current_mid + (0.05 if side == BUY_EVENT else -0.05)
            events.append((ev, ts, ts, px, 0.1, 0, 0, 0.0))
            
    data = np.array(events, dtype=dtype)
    # Save as npy
    filename_npy = filename.replace(".npz", ".npy")
    np.save(filename_npy, data)
    print(f"Generated {len(data)} events to {filename_npy}")

if __name__ == "__main__":
    generate_dummy_data("dummy_data.npz")
