import os
import json
import time
import hashlib
from utils.file_utils import get_file_metadata

BASELINE_PATH = "data/baseline.json"

def build_baseline(directory):
    baseline_data = {}

    for root, dirs, files in os.walk(directory):
        for fname in files:
            file_path = os.path.join(root, fname)
            metadata = get_file_metadata(file_path)

            if metadata:
                relative_path = os.path.relpath(file_path, directory)
                baseline_data[relative_path] = metadata

    return baseline_data

def save_baseline(data):
    with open(BASELINE_PATH, "w") as f:
        json.dump(data, f, indent=4)
    print(f"Baseline saved to {BASELINE_PATH}")

def main():
    target_directory = input("Enter the directory to monitor: ").strip()

    if not os.path.isdir(target_directory):
        print("Invalid directory path.")
        return

    baseline = build_baseline(target_directory)
    save_baseline(baseline)

if __name__ == "__main__":
    main()
