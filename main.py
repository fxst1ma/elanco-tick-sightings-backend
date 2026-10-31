
from fastapi import FastAPI, HTTPException
import httpx

from elanco_client import get_tick_sightings

app = FastAPI(
    title="Elanco Tick Tracker API",
    description="Backend API for tracking tick sightings across the UK",
    version="1.0.0"
)


@app.get("/")
def home():
    return {
        "message": "Welcome to the Elanco Tick Tracker API",
        "status": "running"
    }


@app.get("/health")
def health_check():
    return {"status": "healthy"}


@app.get("/sightings")
async def list_sightings():
    """Retrieve tick sightings from Elanco."""

    try:
        sightings = await get_tick_sightings()

        return {
            "count": len(sightings),
            "sightings": sightings
        }

    except httpx.TimeoutException:
        raise HTTPException(
            status_code=504,
            detail="Elanco API timed out"
        )

    except httpx.HTTPStatusError as error:
        if error.response.status_code == 429:
            raise HTTPException(
                status_code=503,
                detail="Elanco API rate limit reached. Try again later."
            )

        raise HTTPException(
            status_code=502,
            detail="Elanco API returned an error"
        )

    except httpx.RequestError:
        raise HTTPException(
            status_code=502,
            detail="Unable to connect to Elanco API"
        )

    except ValueError:
        raise HTTPException(
            status_code=502,
            detail="Elanco API returned an unexpected data format"
        )

from datetime import datetime
from fastapi import Query



@app.get("/sightings/search")
async def search_sightings(
    city: str | None = None,
    species: str | None = None,
    start_date: datetime | None = None,
    end_date: datetime | None = None
):
    """
    Search tick sightings by city, species and date range.

    Handles invalid dates and timezone differences safely.
    """

    from datetime import timezone

    def normalise_date(value):
        """Convert a datetime to UTC for consistent comparisons."""
        if value.tzinfo is None:
            return value.replace(tzinfo=timezone.utc)
        return value.astimezone(timezone.utc)

    # Normalise user-provided dates
    if start_date:
        start_date = normalise_date(start_date)

    if end_date:
        end_date = normalise_date(end_date)

    # Validate the requested date range
    if start_date and end_date and start_date > end_date:
        raise HTTPException(
            status_code=400,
            detail="Start date cannot be after end date"
        )

    response = await list_sightings()
    sightings = response["sightings"]

    filtered = []
    skipped_invalid_dates = 0

    for sighting in sightings:

        # Skip malformed records safely
        if not isinstance(sighting, dict):
            continue

        # Filter by city
        if city:
            location = sighting.get("location")
            if not isinstance(location, str) or location.casefold() != city.casefold():
                continue

        # Filter by species
        if species:
            record_species = sighting.get("species")
            if not isinstance(record_species, str) or record_species.casefold() != species.casefold():
                continue

        # Parse the date only when date filtering is requested
        if start_date or end_date:
            try:
                raw_date = sighting.get("date")

                if not isinstance(raw_date, str):
                    raise ValueError("Missing or invalid date")

                sighting_date = datetime.fromisoformat(
                    raw_date.replace("Z", "+00:00")
                )
                sighting_date = normalise_date(sighting_date)

            except (ValueError, TypeError):
                skipped_invalid_dates += 1
                continue

            if start_date and sighting_date < start_date:
                continue

            if end_date and sighting_date > end_date:
                continue

        filtered.append(sighting)

    return {
        "count": len(filtered),
        "filters": {
            "city": city,
            "species": species,
            "start_date": start_date,
            "end_date": end_date
        },
        "skipped_invalid_dates": skipped_invalid_dates,
        "sightings": filtered
    }


from collections import Counter


@app.get("/statistics/regions")
async def get_regional_statistics():
    """
    Calculate the number of tick sightings per city.
    """

    response = await list_sightings()
    sightings = response["sightings"]

    # Count sightings in each city
    city_counts = Counter()

    for sighting in sightings:
        city = sighting.get("location")

        if city and isinstance(city, str):
            city_counts[city.strip()] += 1

    # Sort cities from highest to lowest count
    sorted_cities = city_counts.most_common()

    return {
        "total_sightings": len(sightings),
        "total_cities": len(city_counts),
        "sightings_by_city": [
            {
                "city": city,
                "count": count
            }
            for city, count in sorted_cities
        ]
    }

from collections import defaultdict
from datetime import datetime


@app.get("/statistics/trends")
async def get_monthly_trends(
    city: str | None = None
):
    """
    Calculate monthly tick sighting trends.
    Optionally filter by city.
    """

    response = await list_sightings()
    sightings = response["sightings"]

    monthly_counts = defaultdict(int)
    skipped_records = 0

    for sighting in sightings:

        # Optional city filter
        location = sighting.get("location")

        if city:
            if not isinstance(location, str):
                continue

            if location.strip().casefold() != city.strip().casefold():
                continue

        # Check that a valid date exists
        date_value = sighting.get("date")

        if not isinstance(date_value, str):
            skipped_records += 1
            continue

        try:
            sighting_date = datetime.fromisoformat(
                date_value.replace("Z", "+00:00")
            )
        except ValueError:
            skipped_records += 1
            continue

        # Group sightings by year and month
        month = sighting_date.strftime("%Y-%m")
        monthly_counts[month] += 1

    # Sort results chronologically
    sorted_months = sorted(monthly_counts.items())

    return {
        "city": city or "All cities",
        "total_sightings": sum(monthly_counts.values()),
        "skipped_records": skipped_records,
        "monthly_trends": [
            {
                "month": month,
                "count": count
            }
            for month, count in sorted_months
        ]
    }

from data_quality import analyse_data_quality


@app.get("/statistics/data-quality")
async def get_data_quality_report():
    """
    Return a data quality report for Elanco's dataset.
    """

    response = await list_sightings()
    sightings = response["sightings"]

    return analyse_data_quality(sightings)
