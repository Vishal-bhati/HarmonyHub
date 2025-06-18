from django.db import models

import string, random

def generate_code():
    return ''.join(random.choices(string.ascii_uppercase, k=6))

class Room(models.Model):
    code = models.CharField(max_length=6, default=generate_code, unique=True)
    host = models.CharField(max_length=100)
    created_at = models.DateTimeField(auto_now_add=True)


class SongDedication(models.Model):
    room = models.ForeignKey(Room, on_delete=models.CASCADE)
    dedicated_by = models.CharField(max_length=100)
    song_url = models.URLField()
    song_name = models.CharField(max_length=200, blank=True)
    artists = models.CharField(max_length=200, blank=True)
    album_cover = models.URLField(blank=True)
    message = models.TextField(blank=True)
    timestamp = models.DateTimeField(auto_now_add=True)