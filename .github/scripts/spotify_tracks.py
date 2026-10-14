"""Writes tracks.json: artist + title for every song in the site's Spotify playlist.

The site reads this file to show the artist under each song on the
"now playing" screen (Spotify's public embed gives the browser only the title).
The playlist id is read from index.html (var SPOTIFY_PLAYLIST), so there is
only one place to change it.
"""
import json, re, sys, urllib.request

html = open("index.html", encoding="utf-8").read()
m = re.search(r'var SPOTIFY_PLAYLIST = "([A-Za-z0-9]+)"', html)
if not m:
    sys.exit("no SPOTIFY_PLAYLIST in index.html")
pid = m.group(1)

req = urllib.request.Request(
    "https://open.spotify.com/embed/playlist/" + pid,
    headers={"User-Agent": "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/605.1.15 (KHTML, like Gecko) Version/17.0 Safari/605.1.15",
             "Accept-Language": "en"},
)
page = urllib.request.urlopen(req, timeout=30).read().decode("utf-8")
nd = re.search(r'<script id="__NEXT_DATA__" type="application/json">(.*?)</script>', page, re.S)
if not nd:
    sys.exit("no __NEXT_DATA__ on the embed page")
data = json.loads(nd.group(1))


def artist_of(t):
    if isinstance(t.get("subtitle"), str) and t["subtitle"].strip():
        return t["subtitle"].replace(" ", " ").strip()
    a = t.get("artists")
    if isinstance(a, list):
        return ", ".join(x.get("name", "") for x in a if isinstance(x, dict) and x.get("name"))
    return ""


tracks = {}


def walk(o):
    if isinstance(o, dict):
        uri = o.get("uri")
        if isinstance(uri, str) and uri.startswith("spotify:track:") and (o.get("title") or o.get("name")):
            tracks.setdefault(uri, {"title": (o.get("title") or o.get("name")).strip(), "artist": artist_of(o)})
        for v in o.values():
            walk(v)
    elif isinstance(o, list):
        for v in o:
            walk(v)


walk(data)
if not tracks:
    sys.exit("found no tracks, keeping the old tracks.json")

out = json.dumps({"playlist": pid, "tracks": tracks}, ensure_ascii=False, indent=1, sort_keys=True) + "\n"
try:
    old = open("tracks.json", encoding="utf-8").read()
except FileNotFoundError:
    old = ""
if out != old:
    open("tracks.json", "w", encoding="utf-8").write(out)
print(len(tracks), "tracks")
