#!/usr/bin/env python3
from __future__ import annotations

import logging
import logging
import time

import config
import db
from colors import bold, gr, bl
from fetcher import Fetcher


# setup a logger 
logging.basicConfig(
    filename=config.LOG_FILE,
    filemode="a",
    format="%(process)d %(asctime)s,%(msecs)d %(name)s %(levelname)s %(message)s",
    datefmt="%H:%M:%S",
    level=logging.DEBUG,
)

# tap into spotipy's logs for more vis
logging.getLogger("spotipy").setLevel(logging.ERROR)


TICK_RATE=1
def main():
    logging.debug("STARTING...")

    fetcher = Fetcher(credentials=config.SPOTIFY_CREDENTIALS)

    try:
        start_time = time.time()
        fetcher.start()

        while True:
            stats = fetcher.get_stats()

            num_artists = f'{stats["num_artists"]:<8}'
            artists_per_minute = f'{stats["artists_per_minute"]:8.1f}'
            artists_per_request = f'{stats["artists_per_request"]:6.1f}'
            num_requests = stats["num_requests"]
            _elapsed_mins = (time.time() - start_time) / 60
            elapsed_mins = f"{_elapsed_mins:.2f}"
            requests_per_minute = f"{num_requests/_elapsed_mins:7.2f}"

            # print status line (rewrite previous) with a little bit of color
            print(
                f"{bold('Total artists found')}: {gr(num_artists)} - {bold('total reqs')}: {gr(num_requests)} : {gr(artists_per_minute)} artists/min - {bl(requests_per_minute)} req/min - {bl(artists_per_request)} artists/req - {bl(elapsed_mins)} m elapsed",
                end="\r",
            )

            time.sleep(TICK_RATE)

    except KeyboardInterrupt:
        log.debu("received CTRL-C...")
    finally:
        print("stopping procs/threads...")
        fetcher.stop()
        print(f"shutting down")


if __name__ == "__main__":
    # TODO argparse, allow for some args maybe ? 
    db.create_tables()
    main()
