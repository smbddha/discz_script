# spotify artists 'collector'

## Running

1. Setup a virtual env (optional)
2. Install packages:
```
$ pip install -r requirements.txt
```
3. Add your credentials to the config. You can add multiple credential pairs to the `SPOTIFY_CREDENTIALS` list... if so inclined.
```
# /config.py
SPOTIFY_CLIENT_ID="YOUR_ID_HERE"
SPOTIFY_CLIENT_SECRET="YOUR_SECRET_HERE"
```
4. Run the script
```
$ python main.py
```

## Approach

From what I found there were three enpoints endpoints that could be
used find new artists for which you didnt already have the id. 

1. the search endpoint (`/search`)
   max artists per request: `50`
   
2. the related artists endpoint (`/artists/{id}/related`)
   max artists per request: `20`
   
3. the recommendations endpoint (`/recommendations`)
   max artists per request: `100` (but endpoint returns tracks)
   
The related artists endpoint is best for systematic exploration of
spotify artists, as you can easily conduct a graph search of spotify
artists. However, this endpoint returns the fewest artists of the
three, and in practice the  number of unseen artists return by this
endpoint declines quickly if it is seed with just a single
artist. This is most likely because if two artists are both related to
a third artist, there is high likelihood that those two artists are
themselves also related.
	The search endpoint returns more artists per request, but is not
conducive for systematic exploration of artists, as it's not trivial
to come up with good queries that will return unseen artists at a good
rate.
	Similarly the recommendations retrieves new artists in a more
random manner. But its api, accepting lists of seed artists and
genres, allow for a simplier enumeration/exploration of possible
inputs, at least compared to the search endpoint that can receive any
string search parameter.
	So, in my attempt to retreive all artists in the faster manner I
implemented a heuristic that makes use of all endpoints. First, I use
the search endpoint and query for artists using every letter of the
alphabet. I then use those results to spawn related and recommendation
requests. While the 'collector' starts of fast, reaching speeds of
`4000-5000` artists discovered per minute. This rate starts slowly
declining... I've yet to run it long enough to see its
convergence. I'd assume this is due to the related endpoint causing
too many of the same artists to be returned after a while, and its
possible that the recommendation requests reenforce this. They may,
however, allow for more variance since the genres and other seed
artist ids are varied amongst these requests.

### Future work//idea
heuristic improvements...
	


