import os
import json
from utils.file_utils import get_file_metadata
from utils.config_loader import load_config

config = load_config()

MONITOR_PATH = config["monitor_path"]
BASELINE_PATH = config["baseline_file"]
REPORT_PATH = config["report_file"]
exclude = config["exclude"]

def is_excluded(path):
    return any(excluded in path for excluded in exclude)

def load_baseline():
    if not os.path.exists(BASELINE_PATH):
        print("Baseline not found. Please run initialize.py first.")
        return None

    with open(BASELINE_PATH, "r") as f:
        return json.load(f)

def scan_current_state(directory):
    current_data = {}
    for root, dirs, files in os.walk(directory):
        dirs[:] = [d for d in dirs if not is_excluded(os.path.join(root, d))]
        for fname in files:
            file_path = os.path.join(root, fname)
            if is_excluded(file_path):
                continue
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

def save_report(modified, deleted, new):
    report = {
        "modified": modified,
        "deleted": deleted,
        "new": new
    }
    with open(REPORT_PATH, "w") as f:
        json.dump(report, f, indent=4)
    print(f"\n📄 Report saved to {REPORT_PATH}")

def main():
    #target_directory = input("Enter the directory to monitor: ").strip()

    if not os.path.isdir(MONITOR_PATH):
        print("Invalid directory.")
        return

    baseline = load_baseline()
    if baseline is None:
        return

    current_state = scan_current_state(MONITOR_PATH)
    modified, deleted, new = compare_states(baseline, current_state)

    print("\n📂 Comparison Report:")
    print("----------------------")

    if not modified and not deleted and not new:
        print("✅ No changes detected. All files are intact.")
    else:
        if modified:
            print(f"\n✏️ Modified files ({len(modified)}):")
            for f in modified:
                print(f" - {f}")

        if deleted:
            print(f"\n❌ Deleted files ({len(deleted)}):")
            for f in deleted:
                print(f" - {f}")

        if new:
            print(f"\n➕ New files ({len(new)}):")
            for f in new:
                print(f" - {f}")

    save_report(modified, deleted, new)

if __name__ == "__main__":
    main()
