
import asyncio
import time
import httpx

BASE_URL = "https://dev-task.elancoapps.com/data"

CACHE_DURATION = 300  # Cache data for 5 minutes


_cached_sightings = None
_cache_timestamp = 0.0
_cache_lock = asyncio.Lock()


async def get_tick_sightings():
    """
    Retrieve tick sightings from Elanco's API.

    Cache successful responses for five minutes to
    reduce API requests and avoid rate limiting.
    """

    global _cached_sightings, _cache_timestamp

    current_time = time.monotonic()

    # Return cached data if it is still valid
    if (
        _cached_sightings is not None
        and current_time - _cache_timestamp < CACHE_DURATION
    ):
        return _cached_sightings

    # Prevent simultaneous requests from refreshing
    # the cache multiple times
    async with _cache_lock:

        # Check again after acquiring the lock
        current_time = time.monotonic()

        if (
            _cached_sightings is not None
            and current_time - _cache_timestamp < CACHE_DURATION
        ):
            return _cached_sightings
        
        async with httpx.AsyncClient(timeout=15.0) as client:
            response = await client.get(
                f"{BASE_URL}/tick-sightings"
            )

            response.raise_for_status()
            data = response.json()

        if not isinstance(data, list):
            raise ValueError(
                "Unexpected response format from Elanco API"
            )

        # Only cache successfully validated responses
        _cached_sightings = data
        _cache_timestamp = time.monotonic()

        return _cached_sightings
