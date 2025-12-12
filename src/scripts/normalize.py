import numpy as np
import glob
import os
import argparse

def normalize(input_dir, output_file):
    # Find all npz files in the directory
    files = sorted(glob.glob(os.path.join(input_dir, "*.npz")))
    if not files:
        print(f"No .npz files found in {input_dir}")
        return

    print(f"Found {len(files)} files. Merging...")
    
    all_data = []
    
    for f in files:
        try:
            with np.load(f) as data:
                # Assuming the recorder saved it under the key 'data'
                chunk = data['data']
                all_data.append(chunk)
        except Exception as e:
            print(f"Error reading {f}: {e}")

    if not all_data:
        print("No data loaded.")
        return

    # Concatenate all chunks
    merged_data = np.concatenate(all_data)
    
    # Sort by local_ts to ensure time monotonicity (crucial for hftbacktest)
    # Although recorder should be monotonic, network jitter or chunk boundaries might cause slight issues if not careful.
    # But strictly speaking, we should sort by local_ts.
    merged_data.sort(order='local_ts')
    
    # Save to single file
    np.savez_compressed(output_file, data=merged_data)
    print(f"Saved merged data to {output_file} ({len(merged_data)} rows)")

if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument("--input", type=str, default="data", help="Input directory containing chunked .npz files")
    parser.add_argument("--output", type=str, default="okx_merged.npz", help="Output .npz file")
    args = parser.parse_args()
    
    normalize(args.input, args.output)
