import os
import json
from utils.file_utils import get_file_metadata

BASELINE_PATH = "data/baseline.json"

def load_baseline():
    if not os.path.exists(BASELINE_PATH):
        print("Baseline not found. Please run initialize.py first.")
        return None

    with open(BASELINE_PATH, "r") as f:
        return json.load(f)

def scan_current_state(directory):
    current_data = {}
    for root, dirs, files in os.walk(directory):
        for fname in files:
            file_path = os.path.join(root, fname)
            metadata = get_file_metadata(file_path)

            if metadata:
                relative_path = os.path.relpath(file_path, directory)
                current_data[relative_path] = metadata

    return current_data

def compare_states(baseline, current):
    modified = []
    deleted = []
    new = []

    # Check for modified and deleted files
    for path in baseline:
        if path not in current:
            deleted.append(path)
        elif baseline[path]['hash'] != current[path]['hash']:
            modified.append(path)

    # Check for new files
    for path in current:
        if path not in baseline:
            new.append(path)

    return modified, deleted, new

def main():
    target_directory = input("Enter the directory to monitor: ").strip()

    if not os.path.isdir(target_directory):
        print("Invalid directory.")
        return

    baseline = load_baseline()
    if baseline is None:
        return

    current_state = scan_current_state(target_directory)
    modified, deleted, new = compare_states(baseline, current_state)

    print("\n📂 Comparison Report:")
    print("----------------------")

    if modified:
        print(f"\n✏️ Modified files ({len(modified)}):")
        for f in modified:
            print(f" - {f}")
    else:
        print("\n✅ No modified files.")

    if deleted:
        print(f"\n❌ Deleted files ({len(deleted)}):")
        for f in deleted:
            print(f" - {f}")
    else:
        print("\n✅ No deleted files.")

    if new:
        print(f"\n➕ New files ({len(new)}):")
        for f in new:
            print(f" - {f}")
    else:
        print("\n✅ No new files.")

if __name__ == "__main__":
    main()
