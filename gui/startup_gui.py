import tkinter as tk
import subprocess
import threading
from gui_main import launch_gui

def run_initialize():
    try:
        subprocess.run(["python3", "initialize.py"], check=True)
        status_label.config(text="✅ Baseline initialized successfully!", fg="green")
    except subprocess.CalledProcessError:
        status_label.config(text="❌ Failed to initialize baseline", fg="red")

def start_monitoring():
    # Start monitor.py in background and open GUI
    def run_monitor():
        subprocess.Popen(["python3", "monitor.py"])
    threading.Thread(target=run_monitor, daemon=True).start()
    launch_gui()

# GUI Window
root = tk.Tk()
root.title("FIM - Startup")
root.geometry("300x200")

tk.Label(root, text="Welcome to FIM", font=("Arial", 14, "bold")).pack(pady=15)

tk.Button(root, text="🛠 Initialize Baseline", command=run_initialize, width=25).pack(pady=5)
tk.Button(root, text="🕵️ Start Monitoring", command=start_monitoring, width=25).pack(pady=5)

status_label = tk.Label(root, text="", font=("Arial", 10))
status_label.pack(pady=10)

root.mainloop()

