import threading
import tkinter as tk
from tkinter import ttk, messagebox
import sv_ttk
import asyncio
import colorsys
import requests
import os
import subprocess
from spotify_api import get_image_url_from_spotify, get_current_track_id
from colorthief import ColorThief
from kasa import SmartLightStrip

# Logging
import logging
logging.basicConfig(level=logging.INFO)

device_ip = None

# Function to save image from URL
def save_image_from_url(url, file_path):
    response = requests.get(url)
    with open(file_path, 'wb') as f:
        f.write(response.content)

# Function to get dominant color
def get_dominant_color():
    url = get_image_url_from_spotify()
    if not url:
        return None

    image_file_path = 'temp_image.jpg'
    save_image_from_url(url, image_file_path)

    color_thief = ColorThief(image_file_path)
    dominant_color = color_thief.get_color(quality=1)
    logging.info(f"Dominant Color: {dominant_color}")

    os.remove(image_file_path)
    return dominant_color

# Async function to set strip color
async def set_strip_color(strip_ip, color):
    retries = 5
    delay = 1

    for i in range(retries):
        try:
            strip = SmartLightStrip(strip_ip)
            await strip.update()
            hsv_color = colorsys.rgb_to_hsv(color[0] / 255, color[1] / 255, color[2] / 255)
            await strip.set_hsv(
                hue=int(hsv_color[0] * 360),
                saturation=int(hsv_color[1] * 100),
                value=int(hsv_color[2] * 100)
            )
            await strip.update()
            logging.info("Successfully set the strip color")
            return
        except Exception as e:
            logging.error(f"Error setting color: {e}")
            if i < retries - 1:
                logging.info(f"Retrying in {delay} seconds...")
                await asyncio.sleep(delay)
                delay *= 2
            else:
                logging.error("Max retries reached, could not set strip color")
                return

# Main function to check for track changes and update color
async def main_loop(status_label, strip_ip):
    current_track_id = None
    while True:
        new_track_id = get_current_track_id()
        if new_track_id and new_track_id != current_track_id:
            current_track_id = new_track_id
            logging.info(f"Track changed to {current_track_id}")
            color = get_dominant_color()
            if color:
                await set_strip_color(strip_ip, color)
                status_label.config(text=f"Updated color for track ID: {current_track_id}")
        await asyncio.sleep(1)

# Function to run the asyncio loop in a separate thread
def run_asyncio_loop(loop, status_label, strip_ip):
    asyncio.set_event_loop(loop)
    loop.run_until_complete(main_loop(status_label, strip_ip))

# Function to start the program
def start_program(status_label, strip_ip):
    loop = asyncio.new_event_loop()
    t = threading.Thread(target=run_asyncio_loop, args=(loop, status_label, strip_ip))
    t.start()
    status_label.config(text="Program started")

# Function to stop the program
def stop_program(status_label):
    status_label.config(text="Program stopped")

# Function to discover devices and show them in a new window
def discover_devices():
    result = subprocess.run(["kasa", "discover"], capture_output=True, text=True, check=True)
    output_lines = result.stdout.splitlines()

    devices = []
    for i, line in enumerate(output_lines):
        if "==" in line:  # Device name found
            device_name = line.split("==")[1].strip()
            if i + 1 < len(output_lines):
                host_line = output_lines[i + 1]
                if host_line.startswith("Host:"):
                    ip_address = host_line.split(":")[1].strip()
                    devices.append((device_name, ip_address))

    if not devices:
        messagebox.showerror("No Devices Found", "No devices were found during the discovery process.")
        return None

    return devices

# Function to handle device selection
def on_device_select(event, devices_listbox, devices, status_label, start_button):
    global device_ip
    selection = devices_listbox.curselection()
    if selection:
        index = selection[0]
        device_name, device_ip = devices[index]  # Retrieve the IP based on the selected device name
        status_label.config(text=f"Selected device: {device_name} with IP: {device_ip}")
        start_button.config(state=tk.NORMAL)


# Function to create the device selection window
def open_device_selection_window(status_label, start_button):
    devices = discover_devices()
    if not devices:
        return

    selection_window = tk.Toplevel()
    selection_window.title("Select a Device")

    label = ttk.Label(selection_window, text="Select a device:")
    label.pack(pady=10)

    devices_listbox = tk.Listbox(selection_window, height=10)
    for device_name, _ in devices:  # Display only the device name
        devices_listbox.insert(tk.END, device_name)
    devices_listbox.pack(pady=10)
    
    devices_listbox.bind('<<ListboxSelect>>', lambda event: on_device_select(event, devices_listbox, devices, status_label, start_button))

# Main function to create the UI
def create_ui():
    root = tk.Tk()
    root.title("Spotify LED Controller")

    sv_ttk.set_theme("dark")

    status_label = ttk.Label(root, text="Status: Not running")
    status_label.pack(pady=10)

    discover_button = ttk.Button(root, text="Discover Devices", command=lambda: open_device_selection_window(status_label, start_button))
    discover_button.pack(pady=10)

    start_button = ttk.Button(root, text="Start", state=tk.DISABLED, command=lambda: start_program(status_label, device_ip))
    start_button.pack(pady=10)

    stop_button = ttk.Button(root, text="Stop", command=lambda: stop_program(status_label))
    stop_button.pack(pady=10)

    root.mainloop()

if __name__ == "__main__":
    create_ui()