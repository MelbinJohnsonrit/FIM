import tkinter as tk
from tkinter import ttk
from matplotlib.backends.backend_tkagg import FigureCanvasTkAgg
import matplotlib.pyplot as plt
import json
import os
import subprocess
import threading

SCAN_INTERVAL_MS = 10000  # 10 seconds
REPORT_PATH = "data/report.json"


def read_report():
    if not os.path.exists(REPORT_PATH):
        return {"modified": [], "new": [], "deleted": []}
    try:
        with open(REPORT_PATH, "r") as f:
            return json.load(f)
    except json.JSONDecodeError:
        return {"modified": [], "new": [], "deleted": []}


def launch_gui():
    root = tk.Tk()
    root.title("File Integrity Monitor - Live")
    root.geometry("900x700")

    audio_alert_enabled = tk.BooleanVar(value=True)
    email_alert_enabled = tk.BooleanVar(value=False)

    # Top Summary Frame
    top_frame = tk.Frame(root)
    top_frame.pack(fill='x', pady=10)

    total_label = tk.Label(top_frame, text="Total Alerts: 0", font=("Arial", 12, "bold"))
    total_label.pack(side="left", padx=10)
    modified_label = tk.Label(top_frame, text="Modified: 0", font=("Arial", 12))
    modified_label.pack(side="left", padx=10)
    new_label = tk.Label(top_frame, text="New: 0", font=("Arial", 12))
    new_label.pack(side="left", padx=10)
    deleted_label = tk.Label(top_frame, text="Deleted: 0", font=("Arial", 12))
    deleted_label.pack(side="left", padx=10)

    # Middle Section
    mid_frame = tk.Frame(root)
    mid_frame.pack(fill="both", expand=True, padx=10, pady=5)

    # File Change List
    list_frame = tk.LabelFrame(mid_frame, text="Detected Changes", padx=5, pady=5)
    list_frame.pack(side="left", fill="both", expand=True)

    change_listbox = tk.Listbox(list_frame)
    change_listbox.pack(fill="both", expand=True)

    # Container frame on the right side
    right_frame = tk.Frame(mid_frame)
    right_frame.pack(side="right", fill="y", padx=10)

    # Pie Chart Frame
    chart_frame = tk.LabelFrame(right_frame, text="Change Distribution", padx=5, pady=5)
    chart_frame.pack(side="top", fill="x", pady=(0, 10))  # Top of right_frame

    fig, ax = plt.subplots(figsize=(2.5, 2.5))
    pie_canvas = FigureCanvasTkAgg(fig, master=chart_frame)
    pie_canvas.get_tk_widget().pack()

    # Startup Section Frame - just below chart_frame
    startup_frame = tk.LabelFrame(right_frame, text="Start FIM", padx=5, pady=5)
    startup_frame.pack(side="top", fill="x")

    status_label = tk.Label(startup_frame, text="", font=("Arial", 10))
    status_label.pack()
    # Bottom Controls
    bottom_frame = tk.Frame(right_frame)
    bottom_frame.pack(side="bottom",fill="x", pady=10)

    tk.Checkbutton(bottom_frame, text="Audio Alert", variable=audio_alert_enabled).pack(side="left", padx=20)
    tk.Checkbutton(bottom_frame, text="Email Alert", variable=email_alert_enabled).pack(side="left", padx=20)

    def run_initialize():
        try:
            subprocess.run(["python3", "initialize.py"], check=True)
            status_label.config(text="✅ Baseline initialized successfully!", fg="green")
        except subprocess.CalledProcessError:
            status_label.config(text="❌ Failed to initialize baseline", fg="red")

    monitor_process = None

    def start_monitoring():
        def run_monitor():
            nonlocal monitor_process
            if monitor_process is None or monitor_process.poll() is not None:
                monitor_process = subprocess.Popen(["python3", "monitor.py"])
                status_label.config(text="🕵 Monitoring started in background...", fg="blue")
            else:
                status_label.config(text="⚠ Already monitoring.", fg="orange")

        threading.Thread(target=run_monitor, daemon=True).start()

    def stop_monitoring():
        nonlocal monitor_process
        if monitor_process and monitor_process.poll() is None:
            monitor_process.terminate()
            monitor_process = None
            status_label.config(text="🛑 Monitoring stopped.", fg="red")
        else:
            status_label.config(text="⚠ No active monitoring.", fg="orange")

    tk.Button(startup_frame, text="🛠 Initialize Baseline", command=run_initialize, width=25).pack(pady=5)
    tk.Button(startup_frame, text="🕵️ Start Monitoring", command=start_monitoring, width=25).pack(pady=5)
    tk.Button(startup_frame, text="🛑 Stop Monitoring", command=stop_monitoring, width=25).pack(pady=5)

    # Update Function
    def update_gui():
        report = read_report()
        modified = report.get("modified", [])
        new = report.get("new", [])
        deleted = report.get("deleted", [])

        total = len(modified) + len(new) + len(deleted)
        total_label.config(text=f"Total Alerts: {total}")
        modified_label.config(text=f"Modified: {len(modified)}")
        new_label.config(text=f"New: {len(new)}")
        deleted_label.config(text=f"Deleted: {len(deleted)}")

        # Update Listbox
        change_listbox.delete(0, tk.END)
        for f in modified:
            change_listbox.insert(tk.END, f"{f} - Modified")
        for f in new:
            change_listbox.insert(tk.END, f"{f} - New")
        for f in deleted:
            change_listbox.insert(tk.END, f"{f} - Deleted")

        # Update Pie Chart
        ax.clear()
        values = [len(modified), len(new), len(deleted)]
        labels = ["Modified", "New", "Deleted"]
        if any(values):
            ax.pie(values, labels=labels, autopct='%1.1f%%')
        pie_canvas.draw()

        # Repeat after interval
        root.after(SCAN_INTERVAL_MS, update_gui)

    update_gui()  # Start periodic updates
    root.mainloop()


if __name__ == "__main__":
    launch_gui()
