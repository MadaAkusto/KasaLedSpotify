# KasaLedSpotify

Student hobby project that changes the color of kasa smart light led strip based on the currently playing song on Spotify.

At the moment everything from the Spotipy API codes to the device discovery must be done manually (This will be changed in the future)

## Setup

Everything that is needed to be imported is in the Required Packages.txt file

You will need to create a .env file with the following template:

```
SPOTIPY_CLIENT_ID = ""
SPOTIPY_CLIENT_SECRET = ""
SPOTIPY_REDIRECT_URI = "http://localhost:8888/callback"

```

To discover your device IP using the Python-Kasa API:

```
Kasa discover

```

The device IP will be under Host and must be typed into the 'INSERT DEVICE IP HERE' section of main.py



This program is a fun side project and will be updated as I see fit :)
