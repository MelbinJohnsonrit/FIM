import os
import json
import time
from utils.file_utils import get_file_metadata
from utils.config_loader import load_config
from utils.email_alert import send_email_alert, play_beep

config = load_config()

MONITOR_PATH = config["monitor_path"]
BASELINE_PATH = config["baseline_file"]
REPORT_PATH = config["report_file"]
AI_REPORT_PATH = config.get("ai_report_file", "data/ai_risk_report.json")
exclude = config["exclude"]
SCAN_INTERVAL = config.get("scan_interval", 10)
AI_ENABLED = config.get("ai_risk_scoring", True)

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

def print_report(modified, deleted, new):
    print("\n📂 Comparison Report:")
    print("----------------------")

    if not modified and not deleted and not new:
        print("✅ No changes detected. All files are intact.")
    else:
        if modified:
            print(f"\n✏ Modified files ({len(modified)}):")
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

def main():
    if not os.path.isdir(MONITOR_PATH):
        print("Invalid directory.")
        return

    baseline = load_baseline()
    if baseline is None:
        return

    last_modified = set()
    last_deleted = set()
    last_new = set()

    audio_last_modified = set()
    audio_last_deleted = set()
    audio_last_new = set()

    print(f" Starting periodic scan every {SCAN_INTERVAL} seconds...\n(Press Ctrl+C to stop)\n")
    try:
        while True:
            # Reload config each iteration to pick up GUI changes
            current_config = load_config()

            current_state = scan_current_state(MONITOR_PATH)
            modified, deleted, new = compare_states(baseline, current_state)
            print_report(modified, deleted, new)
            save_report(modified, deleted, new)

            current_modified = set(modified)
            current_deleted = set(deleted)
            current_new = set(new)

            if current_config.get("email_alert"):
                if(current_modified != last_modified or
                   current_deleted != last_deleted or
                   current_new != last_new):
                    body=""
                    if modified:
                        body += "Modified files:\n"+"\n".join(f" -{f}" for f in modified) + "\n\n"
                    if deleted:
                        body += "Deleted files:\n"+"\n".join(f" -{f}" for f in deleted) + "\n\n"
                    if new:
                        body += "New files:\n"+"\n".join(f" -{f}" for f in new) + "\n\n" 

                    send_email_alert(body.strip())

                    last_modified = current_modified
                    last_deleted = current_deleted
                    last_new = current_new

            if current_config.get("beep_on_change", False):
                if(current_modified != audio_last_modified or
                   current_deleted != audio_last_deleted or
                   current_new != audio_last_new):
                    play_beep(current_config)

                    audio_last_modified = current_modified
                    audio_last_deleted = current_deleted
                    audio_last_new = current_new

            time.sleep(SCAN_INTERVAL)

    except KeyboardInterrupt:
        print("\nMonitoring stopped by user.")

if __name__ == "__main__":
    main()
