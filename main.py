# main_program.py
import colorsys
import asyncio
import logging
import threading
from kasa import SmartLightStrip
from spotify_api import get_image_url_from_spotify, get_current_track_id, get_current_track_analysis
from colorthief import ColorThief
import requests
import os

# Logging setup
logging.basicConfig(level=logging.INFO)

device_ip = None  # This will be set when the device is selected via tray_app
brightness = 100  # Default brightness level (0-100)
loop = None  # Event loop will be initialized later

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

async def apply_brightness(brightness):
    """ Asynchronously apply brightness to the light strip. """
    global device_ip
    try:
        if device_ip:
            strip = SmartLightStrip(device_ip)
            await strip.update()
            await strip.set_brightness(brightness)
            await strip.update()
            logging.info(f"Brightness set to {brightness}")
        else:
            logging.error("Device IP is not set.")
    except Exception as e:
        logging.error(f"Error applying brightness: {e}")

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

async def main_loop():
    global brightness
    global color
    global device_ip
    current_track_id = None
    try:
        while True:
            new_track_id = get_current_track_id()
            if new_track_id and new_track_id != current_track_id:
                current_track_id = new_track_id
                logging.info(f"Track changed to {current_track_id}")
                color = get_dominant_color()  # Get the dominant color for the new track
                if color:
                    await set_strip_color(device_ip, color, brightness)
            await asyncio.sleep(5)  # Increased sleep time to reduce command frequency
    except asyncio.CancelledError:
        logging.info("Main loop was cancelled")

def start_program():
    """ Function to start the main event loop """
    global loop
    if loop is None:
        loop = asyncio.new_event_loop()
        t = threading.Thread(target=run_asyncio_loop, args=(loop,))
        t.start()
    else:
        if loop.is_running():
            logging.warning("Event loop is already running.")

def run_asyncio_loop(loop):
    asyncio.set_event_loop(loop)
    try:
        loop.create_task(main_loop())
        loop.run_forever()
    finally:
        loop.close()
