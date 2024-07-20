import threading
import tkinter as tk
import asyncio
import colorsys
import requests
import os
import logging
from spotify_api import get_image_url_from_spotify, get_current_track_id
from colorthief import ColorThief
from kasa import SmartLightStrip

# Configure logging
logging.basicConfig(level=logging.INFO)

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

# Main function to create the UI
def create_ui():
    root = tk.Tk()
    root.title("Spotify LED Controller")

    status_label = tk.Label(root, text="Status: Not running")
    status_label.pack(pady=10)

    start_button = tk.Button(root, text="Start", command=lambda: start_program(status_label, 'INSERT DEVICE IP HERE'))
    start_button.pack(pady=10)

    stop_button = tk.Button(root, text="Stop", command=lambda: stop_program(status_label))
    stop_button.pack(pady=10)

    root.mainloop()

if __name__ == "__main__":
    create_ui()







