import os
import subprocess
from datetime import datetime, timedelta
import tkinter as tk
from tkinter import ttk, messagebox
import threading
import schedule
import time as t
import json
import requests
from config_manager import get_config

# === CONFIG ===
config = get_config()
HDHR_IP = config.get_hdhr_ip()
SAVE_DIR = str(config.get_recording_dir())
FFMPEG_PATH = config.get_ffmpeg_path()
SCHEDULE_FILE = os.path.join(SAVE_DIR, "scheduled_jobs.json")

os.makedirs(SAVE_DIR, exist_ok=True)
scheduled_jobs = []
current_process = None
stop_event = threading.Event()

# === FUNCTIONS ===

def get_hdhr_channels(ip):
    url = f"http://{ip}/lineup.json"
    try:
        r = requests.get(url, timeout=5)
        r.raise_for_status()
        lineup = r.json()
        channels_dict = {}
        for ch in lineup:
            vch = ch.get("GuideNumber")
            name = ch.get("GuideName")
            if vch and name:
                channels_dict[vch] = name
        return channels_dict
    except Exception as e:
        print(f"Error fetching channel lineup: {e}")
        return {}

def record_channel(channel_key, duration_min, crf=23, preset="fast", update_progress=True):
    global current_process, stop_event
    chname = channels[channel_key]
    now = datetime.now().strftime("%Y-%m-%d_%H-%M")
    # Determine format
    record_format = record_format_var.get() if record_format_var else "mp4"
    ext = ".mp4" if record_format == "mp4" else ".ts"
    filename = f"{chname}_{now}{ext}"
    filepath = os.path.join(SAVE_DIR, filename)
    url = f"http://{HDHR_IP}:5004/auto/v{channel_key}"

    if update_progress:
        stop_event.clear()
        progress_var.set(f"Recording {chname}...")
        root.update_idletasks()

    if record_format == "mp4":
        cmd = [
            FFMPEG_PATH,
            "-i", url,
            "-t", str(duration_min*60),
            "-c:v", "libx264",
            "-preset", preset,
            "-crf", str(crf),
            "-c:a", "aac",
            "-b:a", "160k",
            "-movflags", "+faststart",
            "-y",
            filepath
        ]
    else:  # TS
        cmd = [
            FFMPEG_PATH,
            "-i", url,
            "-t", str(duration_min*60),
            "-c:v", "libx264",
            "-preset", preset,
            "-crf", str(crf),
            "-c:a", "ac3",
            "-b:a", "192k",
            "-y",
            filepath
        ]

    # Allow sending 'q' to stop gracefully

    print(f"Starting ffmpeg recording: {' '.join(cmd)}")
    current_process = subprocess.Popen(
        cmd,
        stdin=subprocess.PIPE,
        stdout=subprocess.PIPE,
        stderr=subprocess.STDOUT
    )

    # Show ffmpeg output in real time
    def stream_ffmpeg_output(proc):
        while True:
            line = proc.stdout.readline()
            if not line:
                break
            print(line.decode(errors='ignore').strip())

    ffmpeg_thread = threading.Thread(target=stream_ffmpeg_output, args=(current_process,), daemon=True)
    ffmpeg_thread.start()

    if update_progress:
        end_time = datetime.now() + timedelta(minutes=duration_min)
        while datetime.now() < end_time:
            if stop_event.is_set():
                try:
                    # Send 'q' to ffmpeg to finalize MP4
                    current_process.stdin.write(b'q\n')
                    current_process.stdin.flush()
                    progress_var.set("Stopping recording gracefully...")
                except Exception as e:
                    print(f"Error stopping process: {e}")
                break
            remaining = end_time - datetime.now()
            mins, secs = divmod(remaining.seconds, 60)
            progress_var.set(f"Recording {chname}: {mins:02d}:{secs:02d} remaining")
            root.update_idletasks()
            t.sleep(1)


    current_process.wait()
    if update_progress:
        progress_var.set(f"Recording {chname} completed!")
        root.update_idletasks()
    current_process = None

    # === POST-PROCESSING: Ensure moov atom is at the start (only for mp4) ===
    if record_format == "mp4":
        fixed_filepath = filepath.replace('.mp4', '_fixed.mp4')
        post_cmd = [
            FFMPEG_PATH,
            '-i', filepath,
            '-c', 'copy',
            '-movflags', '+faststart',
            '-y', fixed_filepath
        ]
        print(f"Post-processing: fixing moov atom for {filename}...")
        try:
            post_proc = subprocess.Popen(post_cmd, stdout=subprocess.PIPE, stderr=subprocess.STDOUT)
            for line in iter(post_proc.stdout.readline, b''):
                if not line:
                    break
                print(line.decode(errors='ignore').strip())
            post_proc.wait()
            if post_proc.returncode == 0:
                print(f"Moov atom fixed. Output: {fixed_filepath}")
                # Optionally replace original file
                os.replace(fixed_filepath, filepath)
            else:
                print(f"Post-processing failed for {filename}")
        except Exception as e:
            print(f"Error during post-processing: {e}")

def run_threaded(job_func, *args):
    threading.Thread(target=job_func, args=args, daemon=True).start()

def start_now():
    channel_key = channel_var.get()
    try:
        duration = int(duration_var.get())
        crf = int(crf_var.get())
        preset = preset_var.get()
    except:
        messagebox.showerror("Error", "Duration and CRF must be numbers")
        return
    run_threaded(record_channel, channel_key, duration, crf, preset)

def stop_recording():
    global stop_event
    if current_process:
        stop_event.set()
        try:
            current_process.stdin.write(b'q\n')
            current_process.stdin.flush()
            progress_var.set("Stopping recording gracefully...")
        except Exception as e:
            print(f"Error stopping process: {e}")
    else:
        messagebox.showinfo("Info", "No recording is currently running.")

def schedule_recording():
    channel_key = channel_var.get()
    try:
        duration = int(duration_var.get())
        crf = int(crf_var.get())
        preset = preset_var.get()
    except:
        messagebox.showerror("Error", "Duration and CRF must be numbers")
        return

    day_map = {
        "Mon": "monday",
        "Tue": "tuesday",
        "Wed": "wednesday",
        "Thu": "thursday",
        "Fri": "friday",
        "Sat": "saturday",
        "Sun": "sunday"
    }
    days_selected = [day_map[day] for day, var in day_vars.items() if var.get()]

    try:
        hour, minute = map(int, time_var.get().split(":"))
    except:
        messagebox.showerror("Error", "Time must be in HH:MM format")
        return

    for day in days_selected:
        job = getattr(schedule.every(), day).at(f"{hour:02d}:{minute:02d}").do(
            run_threaded, record_channel, channel_key, duration, crf, preset
        )
        scheduled_jobs.append((job, f"{channels[channel_key]} - {day} at {hour:02d}:{minute:02d} for {duration} min"))

    update_scheduled_list()
    save_schedule()
    messagebox.showinfo("Scheduled", "Recording(s) scheduled successfully.")

def update_scheduled_list():
    listbox_scheduled.delete(0, tk.END)
    for _, desc in scheduled_jobs:
        listbox_scheduled.insert(tk.END, desc)

def cancel_selected():
    selected = listbox_scheduled.curselection()
    if not selected:
        return
    idx = selected[0]
    if idx < len(scheduled_jobs):
        job, _ = scheduled_jobs.pop(idx)
        schedule.cancel_job(job)
    listbox_scheduled.delete(idx)
    save_schedule()

def save_schedule():
    data = [desc for _, desc in scheduled_jobs]
    with open(SCHEDULE_FILE, "w") as f:
        json.dump(data, f)

def load_schedule():
    if not os.path.exists(SCHEDULE_FILE):
        return
    with open(SCHEDULE_FILE, "r") as f:
        data = json.load(f)
    for desc in data:
        listbox_scheduled.insert(tk.END, desc)

# === GUI ===
# Add format selection to GUI

root = tk.Tk()
root.title("HDHomeRun DVR")

frame = ttk.Frame(root, padding=20)
frame.grid()

channels = get_hdhr_channels(HDHR_IP)
if not channels:
    channels = {"7.1": "Fox"}  # fallback

ttk.Label(frame, text="Channel:").grid(row=0, column=0)
channel_var = tk.StringVar()
ttk.Combobox(frame, textvariable=channel_var, values=list(channels.keys())).grid(row=0, column=1)
channel_var.set(list(channels.keys())[0])

ttk.Label(frame, text="Duration (minutes):").grid(row=1, column=0)
duration_var = tk.StringVar(value="30")
ttk.Entry(frame, textvariable=duration_var).grid(row=1, column=1)

# Add format selection to GUI
ttk.Label(frame, text="Format:").grid(row=1, column=2)
record_format_var = tk.StringVar(value="mp4")
ttk.Combobox(frame, textvariable=record_format_var, values=["mp4", "ts"]).grid(row=1, column=3)

ttk.Label(frame, text="CRF (lower=better quality):").grid(row=2, column=0)
crf_var = tk.StringVar(value="23")
ttk.Entry(frame, textvariable=crf_var).grid(row=2, column=1)

ttk.Label(frame, text="Preset:").grid(row=2, column=2)
preset_var = tk.StringVar(value="fast")
ttk.Combobox(frame, textvariable=preset_var, values=["ultrafast","superfast","veryfast","faster","fast","medium","slow","slower","veryslow"]).grid(row=2, column=3)

ttk.Label(frame, text="Days:").grid(row=3, column=0)
days = ["Mon","Tue","Wed","Thu","Fri","Sat","Sun"]
day_vars = {}
for i, day in enumerate(days):
    var = tk.BooleanVar()
    tk.Checkbutton(frame, text=day, variable=var).grid(row=3, column=i+1)
    day_vars[day] = var

ttk.Label(frame, text="Time (HH:MM):").grid(row=4, column=0)
time_var = tk.StringVar(value="20:00")
ttk.Entry(frame, textvariable=time_var).grid(row=4, column=1)

ttk.Button(frame, text="Record Now", command=start_now).grid(row=5, column=0, pady=10)
ttk.Button(frame, text="Stop Recording", command=stop_recording).grid(row=5, column=1, pady=10)
ttk.Button(frame, text="Schedule Recording", command=schedule_recording).grid(row=5, column=2, pady=10)

progress_var = tk.StringVar()
ttk.Label(frame, textvariable=progress_var).grid(row=6, column=0, columnspan=8)

ttk.Label(frame, text="Scheduled Recordings:").grid(row=7, column=0, sticky="w")
listbox_scheduled = tk.Listbox(frame, width=80)
listbox_scheduled.grid(row=8, column=0, columnspan=8)
ttk.Button(frame, text="Cancel Selected", command=cancel_selected).grid(row=9, column=0, pady=5)

load_schedule()

def run_schedule_loop():
    while True:
        schedule.run_pending()
        t.sleep(10)

threading.Thread(target=run_schedule_loop, daemon=True).start()
root.mainloop()

