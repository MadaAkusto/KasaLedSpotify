# KasaLedSpotify

Student hobby project that changes the color of kasa smart light led strip based on the currently playing song on Spotify.

## Disclaimer
At the moment the Spotipy API codes must be created manually (This will be changed in the future)

Kasa devices seem to go unresponsive if too many requests are made if you run into this problem a device reset might be necessary, hold the power button on your light strips for 10 seconds and re-setup your device from the Kasa app

## Setup

You will need to create a .env file with the following template:

```
SPOTIPY_CLIENT_ID = ""
SPOTIPY_CLIENT_SECRET = ""
SPOTIPY_REDIRECT_URI = "http://localhost:8888/callback"
```


This program is a fun side project and will be updated as I see fit :)
