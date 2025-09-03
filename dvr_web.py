import os
import subprocess
from datetime import datetime, timedelta
import threading
import schedule
import time as t
import json
import requests
from flask import Flask, render_template, request, jsonify

# === CONFIG ===
HDHR_IP = "192.168.1.246"
SAVE_DIR = r"F:\TV_Recordings"
FFMPEG_PATH = r"C:\FFMPEG\ffmpeg-2025-08-25-git-1b62f9d3ae-essentials_build\bin\ffmpeg.exe"
SCHEDULE_FILE = os.path.join(SAVE_DIR, "scheduled_jobs.json")

os.makedirs(SAVE_DIR, exist_ok=True)
scheduled_jobs = []
current_process = None
stop_event = threading.Event()

app = Flask(__name__)

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
        return {"7.1": "Fox"}  # fallback

channels = get_hdhr_channels(HDHR_IP)
days_list = ["Mon","Tue","Wed","Thu","Fri","Sat","Sun"]

def record_channel(channel_key, duration_min, crf=23, preset="fast", record_format="mp4"):
    global current_process, stop_event
    chname = channels[channel_key]
    now = datetime.now().strftime("%Y-%m-%d_%H-%M")
    ext = ".mp4" if record_format=="mp4" else ".ts"
    filename = f"{chname}_{now}{ext}"
    filepath = os.path.join(SAVE_DIR, filename)
    url = f"http://{HDHR_IP}:5004/auto/v{channel_key}"

    stop_event.clear()

    if record_format == "mp4":
        cmd = [
            FFMPEG_PATH, "-i", url, "-t", str(duration_min*60),
            "-c:v","libx264", "-preset",preset, "-crf",str(crf),
            "-c:a","aac","-b:a","160k","-movflags","+faststart","-y", filepath
        ]
    else:  # TS
        cmd = [
            FFMPEG_PATH, "-i", url, "-t", str(duration_min*60),
            "-c:v","libx264","-preset",preset,"-crf",str(crf),
            "-c:a","ac3","-b:a","192k","-y", filepath
        ]

    current_process = subprocess.Popen(cmd, stdin=subprocess.PIPE, stdout=subprocess.PIPE, stderr=subprocess.STDOUT)

    def stream_output(proc):
        for line in iter(proc.stdout.readline, b''):
            if not line: break
            print(line.decode(errors='ignore').strip())
    threading.Thread(target=stream_output, args=(current_process,), daemon=True).start()

    while current_process.poll() is None:
        if stop_event.is_set():
            try:
                current_process.stdin.write(b'q\n')
                current_process.stdin.flush()
            except:
                pass
            break
        t.sleep(1)

    current_process.wait()
    current_process = None

    # Post-process MP4
    if record_format=="mp4":
        fixed = filepath.replace(".mp4","_fixed.mp4")
        post_cmd = [FFMPEG_PATH,'-i',filepath,'-c','copy','-movflags','+faststart','-y',fixed]
        try:
            post_proc = subprocess.Popen(post_cmd, stdout=subprocess.PIPE, stderr=subprocess.STDOUT)
            for line in iter(post_proc.stdout.readline, b''):
                if not line: break
                print(line.decode(errors='ignore').strip())
            post_proc.wait()
            if post_proc.returncode==0:
                os.replace(fixed, filepath)
        except Exception as e:
            print(f"Post-processing failed: {e}")

def run_threaded(func, *args):
    threading.Thread(target=func, args=args, daemon=True).start()

# === Schedule management ===
def save_schedule():
    data = [desc for _, desc in scheduled_jobs]
    with open(SCHEDULE_FILE,"w") as f:
        json.dump(data,f)

def load_schedule():
    if not os.path.exists(SCHEDULE_FILE): return []
    with open(SCHEDULE_FILE,"r") as f:
        return json.load(f)

def run_schedule_loop():
    while True:
        schedule.run_pending()
        t.sleep(5)

threading.Thread(target=run_schedule_loop, daemon=True).start()

# === Flask Routes ===

@app.route("/")
def index():
    scheduled = [desc for _, desc in scheduled_jobs]
    return render_template("index.html", channels=channels.keys(), scheduled=scheduled, days=days_list)

@app.route("/record_now", methods=["POST"])
def record_now():
    data = request.get_json()
    run_threaded(record_channel, data['channel'], int(data['duration']),
                 int(data['crf']), data['preset'], data['format'])
    return jsonify({"message": f"Recording {data['channel']} started."})

@app.route("/stop_recording", methods=["POST"])
def stop_recording():
    global stop_event
    stop_event.set()
    return jsonify({"message":"Stop signal sent."})

@app.route("/schedule", methods=["POST"])
def schedule_recording():
    data = request.get_json()
    try:
        for day in data['days']:
            job = getattr(schedule.every(), day.lower()).at(data['time']).do(
                run_threaded, record_channel, data['channel'], int(data['duration']),
                int(data['crf']), data['preset'], data['format']
            )
            scheduled_jobs.append((job, f"{channels[data['channel']]} - {day} at {data['time']} for {data['duration']} min"))
        save_schedule()
        return jsonify({"message":"Recording(s) scheduled successfully."})
    except Exception as e:
        return jsonify({"message":f"Error scheduling: {e}"}), 400

@app.route("/cancel", methods=["POST"])
def cancel():
    data = request.get_json()
    idx = int(data['idx'])
    if 0 <= idx < len(scheduled_jobs):
        job,_ = scheduled_jobs.pop(idx)
        schedule.cancel_job(job)
        save_schedule()
        return jsonify({"message":"Scheduled recording canceled."})
    return jsonify({"message":"Invalid index."}), 400

if __name__=="__main__":
    app.run(host="0.0.0.0", port=5000)
