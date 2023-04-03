import logging
import spotipy
from ratelimit import sleep_and_retry, limits

ONE_MINUTE = 60
MAX_CALLS_PER_MINUTE = 80


@sleep_and_retry
@limits(MAX_CALLS_PER_MINUTE / 10, ONE_MINUTE / 10)
def _call_api(f):
    # a simple wrapper for api requests to enforce a hard ratelimit
    return f()


def get_related_artists(client: spotipy.Spotify, id: str):
    def _get_related_artists():
        return client.artist_related_artists(id)

    try:
        res = _call_api(_get_related_artists)
        return res["artists"]
    except Exception as e:
        logging.error(f"error getting related artists {e}")
        raise e


def get_recommendations(client: spotipy.Spotify, **kwargs):
    def _get_recommendations():
        return client.recommendations(**kwargs)

    try:
        res = _call_api(_get_recommendations)

        return [artist for track in res["tracks"] for artist in track["artists"]]
    except Exception as e:
        logging.error(f"error getting recommendations {e}")
        raise e


def get_search(client: spotipy.Spotify, **kwargs):
    def _get_search():
        return client.search(**kwargs)

    try:
        res = _call_api(_get_search)
        return res["artists"]["items"]
    except Exception as e:
        logging.error(f"error searching {e}")
        raise e
