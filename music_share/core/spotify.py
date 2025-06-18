import requests

def get_current_song(access_token):
    endpoint = "https://api.spotify.com/v1/me/player/currently-playing"
    headers = {
        "Authorization": f"Bearer {access_token}"
    }

    response = requests.get(endpoint, headers=headers)

    if response.status_code != 200 or not response.json():
        return None

    data = response.json()
    item = data.get("item")

    if item is None:
        return None

    song = {
        "name": item["name"],
        "artists": ", ".join([artist["name"] for artist in item["artists"]]),
        "album_cover": item["album"]["images"][0]["url"],
        "spotify_url": item["external_urls"]["spotify"],
        "is_playing": data.get("is_playing", False),
        "duration_ms": item["duration_ms"],
        "progress_ms": data.get("progress_ms", 0),
    }
    return song

def get_song_details(track_url, access_token):
    try:
        track_id = track_url.split("/track/")[1].split("?")[0]
    except IndexError:
        return None

    endpoint = f"https://api.spotify.com/v1/tracks/{track_id}"
    headers = {
        "Authorization": f"Bearer {access_token}"
    }

    response = requests.get(endpoint, headers=headers)

    if response.status_code != 200:
        return None

    data = response.json()
    return {
        "song_name": data["name"],
        "artists": ", ".join(artist["name"] for artist in data["artists"]),
        "album_cover": data["album"]["images"][0]["url"]
    }
