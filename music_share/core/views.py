from django.shortcuts import render, redirect, get_object_or_404
from .models import Room
from django.http import HttpResponse
import random
import string
import requests
from django.conf import settings
from urllib.parse import urlencode
from django.http import HttpResponse
from .spotify import get_current_song
from .models import Room, SongDedication
from django.views.decorators.csrf import csrf_exempt
from .spotify import get_song_details
from django.http import JsonResponse
from django.shortcuts import redirect
from django.http import JsonResponse
from django.core import serializers
from .models import SongDedication, Room
from django.http import JsonResponse
from .spotify import get_current_song
import requests
from django.http import JsonResponse



# Helper to generate unique room codes
def generate_code():
    return ''.join(random.choices(string.ascii_uppercase, k=6))

def home(request):
    return render(request, 'core/home.html')


def create_room(request):
    if request.method == 'POST':
        code = generate_code()
        while Room.objects.filter(code=code).exists():
            code = generate_code()

        room = Room.objects.create(code=code, host="Host")  # We will use session/Spotify name later
        return redirect('room', code=code)

    return redirect('home')


def join_room(request):
    if request.method == 'POST':
        code = request.POST.get('room_code', '').strip().upper()
        room = Room.objects.filter(code=code).first()
        if room:
            return redirect('room', code=code)
        return HttpResponse("Room not found", status=404)

    return redirect('home')


def room(request, code):
    room = get_object_or_404(Room, code=code)
    access_token = request.session.get('spotify_token')
    current_song = None
    dedications = SongDedication.objects.filter(room=room).order_by('-timestamp')

    if access_token:
        current_song = get_current_song(access_token)

    return render(request, 'core/room.html', {
        'room': room,
        'current_song': current_song,
         'dedications': dedications,
    })


def spotify_login(request):
    scopes = "user-read-playback-state user-read-currently-playing user-modify-playback-state"
    params = {
        "response_type": "code",
        "client_id": settings.SPOTIFY_CLIENT_ID,
        "scope": scopes,
        "redirect_uri": settings.SPOTIFY_REDIRECT_URI,
    }
    url = "https://accounts.spotify.com/authorize?" + urlencode(params)
    return redirect(url)


def spotify_callback(request):
    code = request.GET.get("code")
    error = request.GET.get("error")

    if error:
        return HttpResponse(f"Spotify error: {error}", status=400)

    token_url = "https://accounts.spotify.com/api/token"
    response = requests.post(token_url, data={
        "grant_type": "authorization_code",
        "code": code,
        "redirect_uri": settings.SPOTIFY_REDIRECT_URI,
        "client_id": settings.SPOTIFY_CLIENT_ID,
        "client_secret": settings.SPOTIFY_CLIENT_SECRET
    })

    response_data = response.json()
    access_token = response_data.get("access_token")

    if not access_token:
        return HttpResponse("Failed to retrieve access token", status=400)

    request.session['spotify_token'] = access_token

    # Fetch user profile
    headers = {"Authorization": f"Bearer {access_token}"}
    user_response = requests.get("https://api.spotify.com/v1/me", headers=headers)
    if user_response.status_code == 200:
        user_data = user_response.json()
        request.session['spotify_user_name'] = user_data.get('display_name')
        images = user_data.get('images')
        if images:
            request.session['spotify_user_image'] = images[0].get('url')

    return redirect('home')

@csrf_exempt
def dedicate_song(request, code):
    room = get_object_or_404(Room, code=code)

    if request.method == 'POST':
        name = request.POST.get('dedicated_by')
        url = request.POST.get('song_url')
        msg = request.POST.get('message')

        access_token = request.session.get('spotify_token')
        song_data = get_song_details(url, access_token) if access_token else {}

        SongDedication.objects.create(
            room=room,
            dedicated_by=name,
            song_url=url,
            message=msg or "",
            song_name=song_data.get('song_name', ''),
            artists=song_data.get('artists', ''),
            album_cover=song_data.get('album_cover', '')
        )

    return redirect('room', code=code)


def search_spotify(request):
    query = request.GET.get('q')
    token = request.session.get('spotify_token')

    if not query or not token:
        return JsonResponse({'error': 'Missing query or token'}, status=400)

    headers = {
        "Authorization": f"Bearer {token}"
    }

    params = {
        "q": query,
        "type": "track",
        "limit": 6
    }

    response = requests.get("https://api.spotify.com/v1/search", headers=headers, params=params)
    data = response.json()

    results = []
    for item in data.get('tracks', {}).get('items', []):
        results.append({
            "name": item["name"],
            "artists": ", ".join([a["name"] for a in item["artists"]]),
            "url": item["external_urls"]["spotify"],
            "album_cover": item["album"]["images"][0]["url"]
        })

    return JsonResponse({"results": results})


def spotify_logout(request):
    request.session.flush()
    return redirect('home')

def get_latest_dedications(request, code):
    room = get_object_or_404(Room, code=code)
    dedications = SongDedication.objects.filter(room=room).order_by('-timestamp')[:10]

    data = [
        {
            "song_name": d.song_name,
            "dedicated_by": d.dedicated_by,
            "artists": d.artists,
            "message": d.message,
            "album_cover": d.album_cover,
            "song_url": d.song_url,
            "timestamp": d.timestamp.strftime('%b %d, %H:%M')
        }
        for d in dedications
    ]
    return JsonResponse({"dedications": data})

def current_song_api(request):
    token = request.session.get('spotify_token')
    if not token:
        return JsonResponse({})
    song = get_current_song(token)
    return JsonResponse(song or {})

def get_lyrics(request):
    artist = request.GET.get('artist')
    track = request.GET.get('track')
    if not artist or not track:
        return JsonResponse({'error': 'Missing artist or track'}, status=400)

    url = f"https://api.lyrics.ovh/v1/{artist}/{track}"
    res = requests.get(url)
    if res.status_code == 200:
        return JsonResponse({'lyrics': res.json().get('lyrics', '')})
    return JsonResponse({'lyrics': 'Lyrics not found.'}, status=404)

# @csrf_exempt
# def spotify_control(request, code):
    if request.method == 'POST':
        action = request.POST.get('action')
        access_token = request.session.get('spotify_token')

        if not access_token:
            return HttpResponse("Spotify not connected", status=401)

        headers = {
            "Authorization": f"Bearer {access_token}",
            "Content-Type": "application/json"
        }

        url = ""
        method = ""
        if action == 'play':
            url = "https://api.spotify.com/v1/me/player/play"
            method = "PUT"
        elif action == 'pause':
            url = "https://api.spotify.com/v1/me/player/pause"
            method = "PUT"
        elif action == 'next':
            url = "https://api.spotify.com/v1/me/player/next"
            method = "POST"
        elif action == 'previous':
            url = "https://api.spotify.com/v1/me/player/previous"
            method = "POST"

        # Make the request and print status
        if url:
            if method == "PUT":
                r = requests.put(url, headers=headers)
            elif method == "POST":
                r = requests.post(url, headers=headers)

            print(f"[SPOTIFY {action.upper()}] STATUS: {r.status_code} | RESPONSE: {r.text}")

        return redirect('room', code=code)