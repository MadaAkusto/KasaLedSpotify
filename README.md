# KasaLedSpotify

Student hobby project that changes the color of kasa smart light led strip based on the currently playing song on Spotify.

## Disclaimer
At the moment the Spotipy API codes must be inputted manually (This will be changed in the future)

Kasa devices seem to go unresponsive if too many requests are made (Looking into this) if you run into this problem a device reset might be necessary, hold the power button on your light strips for 10 seconds and re-setup your device from the Kasa app

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

This program is a fun side project and will be updated as I see fit :)
