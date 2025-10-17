# ========== IMPORTS ==========
import pandas as pd
import spotipy
from spotipy.oauth2 import SpotifyOAuth
import time

# ========== CONFIGURATION ==========
CLIENT_ID = "e209a1ece33c41f6a91b08ca0e7d3a6f"
CLIENT_SECRET = "479c0d292eb2416fb860765ed0ce25bc"
REDIRECT_URI = "http://127.0.0.1:8888/callback"
SCOPE = "playlist-read-private playlist-read-collaborative"
CACHE = ".spotify_token_cache"

sp_oauth = SpotifyOAuth(
    client_id=CLIENT_ID,
    client_secret=CLIENT_SECRET,
    redirect_uri=REDIRECT_URI,
    scope=SCOPE,
    cache_path=CACHE
)
sp = spotipy.Spotify(auth_manager=sp_oauth)

# ========== DATA COLLECTION ==========
PLAYLISTS = [
    "3yVJRNZfjUc0mnH7bsSlWZ",
    "2NkiBYytKAMFnmbLDbAdsa"
]

def get_playlist_tracks(playlist_id):
    tracks = []
    try:
        results = sp.playlist_items(playlist_id, additional_types=["track"], market="from_token")
    except spotipy.SpotifyException as e:
        print(f"❌ Could not fetch playlist {playlist_id}: {e}")
        return tracks

    while results:
        for item in results['items']:
            track = item['track']
            if track and track.get('id'):
                tracks.append({
                    "song_name": track['name'],
                    "artist": ", ".join([a['name'] for a in track['artists']]),
                    "artists_list": [a['name'] for a in track['artists']],
                    "track_id": track['id'],
                    "popularity": track['popularity']
                })
        if results['next']:
            results = sp.next(results)
        else:
            results = None
    return tracks

print("Collecting playlist tracks...")
all_tracks = []
for pl in PLAYLISTS:
    tracks = get_playlist_tracks(pl)
    all_tracks.extend(tracks)
    print(f"   Playlist {pl}: {len(tracks)} tracks")

df = pd.DataFrame(all_tracks)
print(f"✅ Collected {len(df)} tracks")

if len(df) == 0:
    raise SystemExit("No tracks collected. Exiting script.")

# ========== AUDIO FEATURES ==========
print("Fetching audio features...")
track_ids = df['track_id'].tolist()
features = []

# Use smaller batches and better error handling
for i in range(0, len(track_ids), 10):  # batch size 10
    batch = track_ids[i:i+10]
    print(f"   Processing batch {i//10 + 1}/{(len(track_ids)-1)//10 + 1}")
    
    try:
        batch_features = sp.audio_features(batch)
        batch_features = [f for f in batch_features if f is not None]
        features.extend(batch_features)
        print(f"     ✅ Got {len(batch_features)} features")
        time.sleep(0.2) # rate limiting
    except spotipy.SpotifyException as e:
        print(f"     ❌ Failed to fetch audio features for batch: {e}")

if features:
    features_df = pd.DataFrame(features)
    df = df.merge(features_df, left_on='track_id', right_on='id', how='left')
    print(f"✅ Merged audio features for {len(features)} tracks")
else:
    print("❌ No audio features were fetched")
    audio_feature_columns = ['danceability', 'energy', 'valence', 'tempo', 'acousticness']
    for col in audio_feature_columns:
        df[col] = None

# ========== CLEAN DATA ==========
if 'danceability' in df.columns and not df['danceability'].isna().all():
    original_count = len(df)
    df = df.dropna(subset=['danceability', 'energy', 'valence'])
    print(f"✅ {len(df)} tracks after cleaning audio features (dropped {original_count - len(df)})")
else:
    print("⚠️ No audio features available for analysis")
    pass

# ========== 4. SAVE RESULTS ==========
df.to_csv("spotify_song_analysis.csv", index=False)
print(f"\n💾 Data saved to spotify_song_analysis.csv")
