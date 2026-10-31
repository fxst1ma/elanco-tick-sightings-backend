
import pytest
from unittest.mock import patch
from fastapi.testclient import TestClient

from main import app

client = TestClient(app)

# Sample data for testing
SAMPLE_SIGHTINGS = [
    {
        "id": "1",
        "date": "2024-01-15T10:00:00",
        "location": "London",
        "species": "Marsh tick",
        "latinName": "Ixodes apronophorus"
    },
    {
        "id": "2",
        "date": "2024-02-20T12:00:00",
        "location": "Manchester",
        "species": "Marsh tick",
        "latinName": "Ixodes apronophorus"
    },
    {
        "id": "3",
        "date": "2025-03-10T09:00:00",
        "location": "London",
        "species": "Tree-hole tick",
        "latinName": "Ixodes arboricola"
    }
]


@pytest.fixture
def mock_sightings():
    async def fake_get_sightings():
        return SAMPLE_SIGHTINGS

    with patch(
        "main.get_tick_sightings",
        side_effect=fake_get_sightings
    ):
        yield


def test_home():
    response = client.get("/")
    assert response.status_code == 200
    assert response.json()["status"] == "running"


def test_health():
    response = client.get("/health")
    assert response.status_code == 200
    assert response.json()["status"] == "healthy"


def test_get_sightings(mock_sightings):
    response = client.get("/sightings")

    assert response.status_code == 200
    assert response.json()["count"] == 3


def test_filter_by_city(mock_sightings):
    response = client.get(
        "/sightings/search",
        params={"city": "London"}
    )

    assert response.status_code == 200
    assert response.json()["count"] == 2


def test_filter_by_date(mock_sightings):
    response = client.get(
        "/sightings/search",
        params={
            "start_date": "2025-01-01T00:00:00"
        }
    )

    assert response.status_code == 200
    assert response.json()["count"] == 1


def test_invalid_date_range():
    response = client.get(
        "/sightings/search",
        params={
            "start_date": "2025-12-31T00:00:00",
            "end_date": "2024-01-01T00:00:00"
        }
    )

    assert response.status_code == 400


def test_regional_statistics(mock_sightings):
    response = client.get("/statistics/regions")

    assert response.status_code == 200

    data = response.json()

    assert data["total_sightings"] == 3
    assert data["total_cities"] == 2


def test_monthly_trends(mock_sightings):
    response = client.get("/statistics/trends")

    assert response.status_code == 200

    data = response.json()

    assert data["total_sightings"] == 3
    assert len(data["monthly_trends"]) == 3


from data_quality import analyse_data_quality


def test_duplicate_detection():
    sightings = [
        {
            "id": "123",
            "date": "2024-01-15T10:00:00",
            "location": "London",
            "species": "Marsh tick",
            "latinName": "Ixodes apronophorus"
        },
        {
            "id": "123",
            "date": "2024-01-15T10:00:00",
            "location": "London",
            "species": "Marsh tick",
            "latinName": "Ixodes apronophorus"
        }
    ]

    result = analyse_data_quality(sightings)

    assert result["duplicate_id_count"] == 1
    assert result["valid_unique_records"] == 1


def test_missing_fields():
    sightings = [
        {
            "id": "456",
            "date": "2024-01-15T10:00:00",
            "location": "London"
        }
    ]

    result = analyse_data_quality(sightings)

    assert result["invalid_records"] == 1
    assert result["valid_unique_records"] == 0


def test_invalid_date():
    sightings = [
        {
            "id": "789",
            "date": "not-a-date",
            "location": "London",
            "species": "Marsh tick",
            "latinName": "Ixodes apronophorus"
        }
    ]

    result = analyse_data_quality(sightings)

    assert result["invalid_records"] == 1
    assert result["valid_unique_records"] == 0


def test_search_skips_invalid_dates(mock_sightings):
    """Invalid dates should not crash a date-filtered search."""

    with patch(
        "main.list_sightings",
        return_value={
            "sightings": [
                {
                    "id": "1",
                    "date": "not-a-date",
                    "location": "London",
                    "species": "Marsh tick"
                },
                {
                    "id": "2",
                    "date": "2024-01-15T10:00:00",
                    "location": "London",
                    "species": "Marsh tick"
                }
            ]
        }
    ):
        response = client.get(
            "/sightings/search",
            params={"start_date": "2024-01-01T00:00:00"}
        )

    assert response.status_code == 200
    assert response.json()["count"] == 1
    assert response.json()["skipped_invalid_dates"] == 1


def test_search_handles_timezones(mock_sightings):
    """Timezone-aware and naive dates should be comparable."""

    response = client.get(
        "/sightings/search",
        params={"start_date": "2024-01-01T00:00:00Z"}
    )

    assert response.status_code == 200
    assert response.json()["count"] == 3
