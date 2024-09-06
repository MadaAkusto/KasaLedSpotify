import asyncio
import os
import threading
import tkinter as tk
from tkinter import ttk, messagebox
import sv_ttk
import colorsys
import requests
import subprocess
from spotify_api import get_image_url_from_spotify, get_current_track_id
from colorthief import ColorThief
from kasa import SmartLightStrip
import logging

# Logging
logging.basicConfig(level=logging.INFO)

import sys

if sys.platform == 'win32':
    asyncio.set_event_loop_policy(asyncio.WindowsSelectorEventLoopPolicy())


device_ip = None
brightness = 100  # Default brightness level (0-100)
loop = None  # Event loop will be initialized later
brightness_update_event = asyncio.Event()  # Event to signal brightness update
brightness_update_event.set()  # Start with the event set, meaning not paused

def save_image_from_url(url, file_path):
    response = requests.get(url)
    with open(file_path, 'wb') as f:
        f.write(response.content)

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


async def update_brightness_loop(strip_ip):
    global brightness
    while True:
        await brightness_update_event.wait()  # Wait here if the event is cleared
        try:
            strip = SmartLightStrip(strip_ip)
            await strip.update()

            hsv_color = colorsys.rgb_to_hsv(color[0] / 255, color[1] / 255, color[2] / 255)
            await strip.set_hsv(
                hue=int(hsv_color[0] * 360),
                saturation=int(hsv_color[1] * 100),
                value=int(brightness)
            )
            logging.info(f"Brightness updated to {brightness}")
            await asyncio.sleep(2)  # Give the device time to process the update
        except Exception as e:
            logging.error(f"Error updating brightness: {e}")


async def set_strip_color(strip_ip, color, brightness):
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
                value=int(brightness)
            )
            
            await asyncio.sleep(1)  # Adjusted sleep time to give device more processing time
            await strip.update()

            logging.info("Successfully set the strip color and brightness")
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

async def main_loop(status_label, strip_ip):
    global brightness
    global color
    current_track_id = None
    try:
        while True:
            new_track_id = get_current_track_id()
            if new_track_id and new_track_id != current_track_id:
                current_track_id = new_track_id
                logging.info(f"Track changed to {current_track_id}")
                color = get_dominant_color()  # Get the dominant color for the new track
                if color:
                    await set_strip_color(strip_ip, color, brightness)
                    root.after(0, status_label.config, {'text': f"Updated color for track ID: {current_track_id}"})
            await asyncio.sleep(5)  # Increased sleep time to reduce command frequency
    except asyncio.CancelledError:
        logging.info("Main loop was cancelled")

def run_asyncio_loop(loop, status_label, strip_ip):
    asyncio.set_event_loop(loop)
    try:
        loop.create_task(main_loop(status_label, strip_ip))
        loop.create_task(update_brightness_loop(strip_ip))  # Start the brightness update loop
        loop.run_forever()
    finally:
        loop.close()

def start_program(status_label, strip_ip):
    global loop
    if loop is None:
        loop = asyncio.new_event_loop()
        t = threading.Thread(target=run_asyncio_loop, args=(loop, status_label, strip_ip))
        t.start()
        status_label.config(text="Program started")
    else:
        if loop.is_running():
            logging.warning("Event loop is already running.")
            status_label.config(text="Program is already running")

def update_brightness(value):
    global brightness
    try:
        brightness = int(round(float(value)))  # Convert to float, round, then to int
        status_label.config(text=f"Brightness set to {brightness}")
        brightness_update_event.set()  # Signal brightness update
    except ValueError as e:
        logging.error(f"Error updating brightness: {e}")

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

def on_device_select(event, devices_listbox, devices, status_label, start_button, selection_window):
    global device_ip
    selection = devices_listbox.curselection()
    if selection:
        index = selection[0]
        device_name, device_ip = devices[index]  # Retrieve the IP based on the selected device name
        status_label.config(text=f"Selected device: {device_name} with IP: {device_ip}")
        start_button.config(state=tk.NORMAL)
        selection_window.destroy()  # Close the selection window

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
    
    devices_listbox.bind('<<ListboxSelect>>', lambda event: on_device_select(event, devices_listbox, devices, status_label, start_button, selection_window))

def create_ui():
    global brightness  # To be accessed within the slider callback
    global status_label  # Ensure status_label is accessible

    def update_brightness(value):
        global brightness
        try:
            brightness = int(round(float(value)))  # Convert to float, round, then to int
            status_label.config(text=f"Brightness set to {brightness}")
            brightness_update_event.set()  # Signal brightness update
        except ValueError as e:
            logging.error(f"Error updating brightness: {e}")

    global root
    root = tk.Tk()
    root.title("Spotify LED Controller")
    root.geometry("400x300")  # Set the main window size

    sv_ttk.set_theme("dark")

    status_label = ttk.Label(root, text="Status: Not running")
    status_label.pack(pady=10)

    discover_button = ttk.Button(root, text="Discover Devices", command=lambda: open_device_selection_window(status_label, start_button))
    discover_button.pack(pady=10)

    start_button = ttk.Button(root, text="Start", state=tk.DISABLED, command=lambda: start_program(status_label, device_ip))
    start_button.pack(pady=10)

    brightness_label = ttk.Label(root, text="Brightness:")
    brightness_label.pack(pady=5)

    brightness_slider = ttk.Scale(root, from_=0, to=100, orient=tk.HORIZONTAL, command=update_brightness)
    brightness_slider.set(brightness)  # Initialize slider with current brightness
    brightness_slider.pack(pady=5)

    root.mainloop()

create_ui()