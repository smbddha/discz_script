from __future__ import annotations

import logging
import random
import time
import multiprocessing as mp
from multiprocessing import Process, Manager, Value
import concurrent.futures as cf
from concurrent.futures import ThreadPoolExecutor
import spotipy
from spotipy.oauth2 import SpotifyClientCredentials

import db
from reqs import get_recommendations, get_related_artists, get_search


class Fetcher:
    def __init__(self, credentials) -> None:
        # TODO accept settings to guide search heuristic

        self.manager = Manager()

        self.found_artists = self.manager.dict()
        self.req_count = self.manager.Value("i", 0)

        self.credentials = credentials

        self.procs = []

        self.job_queue = mp.Queue()
        self._running = Value("i", 0)

    def start(self):
        self._running.value = 1
        for client_id, client_secret in self.credentials:
            # launch a seperate process for each set of credentials to make this
            # stupidly parallel
            p = Process(
                target=_run,
                args=(
                    client_id,
                    client_secret,
                    self._running,
                    self.job_queue,
                    self.found_artists,
                    self.req_count,
                ),
                daemon=True,
            )

            self.procs.append(p)
            p.start()

        self.start_time = time.time()
        # self.job_queue.put(('related', {'id': example_id}))

        # seed job_queue with intial searches for each letter
        for job in build_search_jobs():
            self.job_queue.put(job)

    def stop(self):
        self._running.value = 0

        logging.debug(f"jobs left: {self.job_queue.qsize()}")

        # TODO this seems to fail if job queue is large enough
        # have to clear the job queue or else child processes will hang
        while not self.job_queue.empty():
            self.job_queue.get_nowait()

        # very hacky but helps
        time.sleep(0.1)
        while not self.job_queue.empty():
            self.job_queue.get_nowait()

        logging.debug(f"jobs left: {self.job_queue.qsize()}")
        for p in self.procs:
            p.join()

    def get_stats(self):
        num_artists = len(self.found_artists.keys())
        elapsed_mins = (time.time() - self.start_time) / 60

        return {
            "num_artists": num_artists,
            "artists_per_minute": num_artists / elapsed_mins,
            "artists_per_request": num_artists / (self.req_count.value + 1),
            "num_requests": self.req_count.value,
            "requests_per_minute": self.req_count.value / elapsed_mins,
        }


def _run(
    client_id,
    client_secret,
    running: Value,
    job_queue: mp.Queue,
    global_artists,
    req_count,
):
    logging.info("Proc running...")

    spotify = spotipy.Spotify(
        client_credentials_manager=SpotifyClientCredentials(
            client_id=client_id, client_secret=client_secret
        )
    )

    # currently getting these in every process ... should only be getting once
    rec_genre_seeds = spotify.recommendation_genre_seeds()["genres"]

    try:
        batch_size = 2
        with ThreadPoolExecutor() as executor:
            job = job_queue.get()
            fut = {executor.submit(do_task, spotify, job): "INITIAL"}
            while True:
                if not running.value:
                    executor.shutdown()
                    return

                done, _ = cf.wait(fut, return_when=cf.FIRST_COMPLETED)

                for future in done:
                    artists = None
                    try:
                        artists = future.result()
                    except ConnectionError as ce:
                        logging.error(f"got conn error {ce}")
                        # TODO the client will need to reconnect in
                        # this case should cancel all waiting tasks
                        # and create a new client for the process
                    except Exception as e:
                        logging.error(f"got conn error {e}")

                    if artists:
                        req_count.set(req_count.value + 1)

                        new_artists = list(
                            filter(lambda a: a[0] not in global_artists, artists)
                        )

                        for id, _, _, _ in new_artists:
                            global_artists[id] = True

                            """TODO improve heuristic """
                            job_queue.put(("related", {"id": id}))
                            job_queue.put(
                                (
                                    "recommendation",
                                    {
                                        "seed_artists": random.choices(
                                            global_artists.keys(),
                                            k=random.randint(1, 2),
                                        ),
                                        "seed_genres": random.choices(
                                            rec_genre_seeds, k=random.randint(1, 3)
                                        ),
                                        "limit": 100,
                                    },
                                )
                            )
                            job_queue.put(
                                (
                                    "recommendation",
                                    {
                                        "seed_artists": [id],
                                        "seed_genres": random.choices(
                                            rec_genre_seeds, k=random.randint(1, 3)
                                        ),
                                        "limit": 100,
                                    },
                                )
                            )

                            # TODO make async
                            # save new artists to the db
                            db.save_artists(*new_artists)

                    del fut[future]

                # start new jobs
                if running.value and executor._work_queue.qsize() < (batch_size * 2):
                    for _ in range(batch_size):
                        try:
                            job = job_queue.get_nowait()
                            fut[executor.submit(do_task, spotify, job)] = True
                        except Exception as e:
                            logging.error("unable to submit new task")
                            break

                time.sleep(0.1)

    except KeyboardInterrupt:
        # Ctrl-c // SIGINT is passed to all child processes, so have to catch it
        # here as well
        logging.info("proc received Ctrl-c")


def do_task(client, job):
    (task, args) = job

    if task == "related":
        res = get_related_artists(client, **args)

        return list(
            map(
                lambda a: (a["id"], a["name"], ",".join(a["genres"]), a["popularity"]),
                res,
            )
        )
    elif task == "recommendation":
        res = get_recommendations(client, **args)

        return list(
            map(
                lambda a: (
                    a["id"],
                    a["name"],
                    ",".join(a.get("genres", [])),
                    a.get("popularity", 0),
                ),
                res,
            )
        )
    elif task == "search":
        res = get_search(client, **args)

        return list(
            map(
                lambda a: (
                    a["id"],
                    a["name"],
                    ",".join(a.get("genres", [])),
                    a.get("popularity", 0),
                ),
                res,
            )
        )
    else:
        logging.warn(f"ERR: unrecognized task: {task} {args}")


def build_search_jobs():
    chars = "abcdefghijklmnopqrstuvwxyz"

    return [
        ("search", {"q": f"artist:{c}", "limit": 50, "offset": 0, "type": "artist"})
        for c in chars
    ]
