import os
from dotenv import load_dotenv
import spotipy
from spotipy.oauth2 import SpotifyOAuth

load_dotenv()

def get_spotify_client():
    clientid = os.getenv("SPOTIPY_CLIENT_ID")
    clientsecret = os.getenv("SPOTIPY_CLIENT_SECRET")
    redirecturi = os.getenv("SPOTIPY_REDIRECT_URI")

    # Set the scope of access you need
    scope = 'user-read-currently-playing'

    return spotipy.Spotify(auth_manager=SpotifyOAuth(client_id=clientid, client_secret=clientsecret, redirect_uri=redirecturi, scope=scope))

def get_image_url_from_spotify():
    sp = get_spotify_client()

    result = sp.currently_playing()

    if result and 'item' in result:
        album_info = result['item']['album']
        if 'images' in album_info:
            image_url = album_info['images'][0]['url']
            print(f"Image URL: {image_url}")
            return image_url
        else:
            print("No images found in album_info.")
    else:
        print("No 'item' key found in the result.")

def get_current_track_id():
    sp = get_spotify_client()

    result = sp.currently_playing()

    if result and 'item' in result:
        return result['item']['id']
    else:
        print("No 'item' key found in the result.")
        return None

if __name__ == "__main__":
    get_image_url_from_spotify()
