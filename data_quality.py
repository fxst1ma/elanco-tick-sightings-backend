
from datetime import datetime


def analyse_data_quality(sightings):
    """
    Analyse duplicate IDs and invalid records
    without modifying the original dataset.
    """

    seen_ids = set()
    duplicate_ids = set()
    invalid_records = 0
    valid_unique_records = 0

    required_fields = [
        "id",
        "date",
        "location",
        "species",
        "latinName"
    ]

    for sighting in sightings:

        if not isinstance(sighting, dict):
            invalid_records += 1
            continue

        # Check required fields
        if any(
            not isinstance(sighting.get(field), str)
            or not sighting[field].strip()
            for field in required_fields
        ):
            invalid_records += 1
            continue

        # Validate date
        try:
            datetime.fromisoformat(
                sighting["date"].replace("Z", "+00:00")
            )
        except ValueError:
            invalid_records += 1
            continue

        # Detect duplicate IDs
        sighting_id = sighting["id"]

        if sighting_id in seen_ids:
            duplicate_ids.add(sighting_id)
            continue

        seen_ids.add(sighting_id)
        valid_unique_records += 1

    return {
        "total_records": len(sightings),
        "valid_unique_records": valid_unique_records,
        "invalid_records": invalid_records,
        "duplicate_id_count": len(duplicate_ids),
        "duplicate_ids": sorted(duplicate_ids)
    }
