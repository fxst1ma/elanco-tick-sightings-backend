# Elanco Tick Sightings — Backend API

A Python REST API developed using FastAPI for the Elanco Software Engineering Placement technical assessment.

## Project Overview

This application retrieves tick-sighting records from Elanco's provided data API and offers additional functionality for searching, filtering, analysing and assessing the quality of the data.

The backend is designed to provide structured JSON responses, handle external API failures and reduce unnecessary requests through caching.

## Technologies Used

- Python 3.13
- FastAPI
- HTTPX
- Uvicorn
- Pytest

## Features

**1. External API Integration**

Retrieves tick-sighting records from Elanco's read-only API.

**2. Search and Filtering**

Supports filtering by city, species and date range, including combinations of filters.

**3. Regional Statistics**

Calculates the number of reported sightings in each city and sorts the results by frequency.

**4. Monthly Trend Analysis**

Groups sightings by year and month, with optional city filtering.

**5. Data Quality Analysis**

Identifies missing required fields, invalid dates and duplicate sighting IDs.

**6. Caching**

Uses a five-minute in-memory cache to reduce repeated requests to Elanco's API.

**7. Error Handling**

Handles external API timeouts, connection failures, rate limiting and unexpected response formats.

**8. Automated Testing**

Includes 13 automated tests covering API endpoints, filtering, statistics, data quality, invalid dates and timezone handling.

## Installation

Requires Python 3.10 or newer.

Clone the repository and open the project directory.

Create a virtual environment:

```powershell
py -m venv .venv
```

Install the dependencies:

```powershell
.\.venv\Scripts\python.exe -m pip install -r requirements.txt
```

Start the application:

```powershell
.\.venv\Scripts\python.exe -m uvicorn main:app --reload
```

Open the interactive API documentation:

http://127.0.0.1:8000/docs

## API Endpoints

| Method | Endpoint | Description |
|---|---|---|
| GET | `/` | Welcome endpoint |
| GET | `/health` | Basic health check |
| GET | `/sightings` | Retrieve tick sightings |
| GET | `/sightings/search` | Filter by city, species and date |
| GET | `/statistics/regions` | Sightings grouped by city |
| GET | `/statistics/trends` | Monthly sighting trends |
| GET | `/statistics/data-quality` | Data quality report |

### Example Request

`GET /sightings/search?city=London`

Returns matching records and the number of sightings found.

## Running Automated Tests

Run:

```powershell
.\.venv\Scripts\python.exe -m pytest -v
```

The current test suite contains 13 tests.

## Engineering Decisions

**Separation of concerns:** External API communication, data quality analysis and HTTP endpoints are organised into separate Python modules.

**Asynchronous API requests:** HTTPX supports non-blocking requests to the external data service.

**Caching:** Successful API responses are stored temporarily to reduce unnecessary requests and the likelihood of rate limiting.

**Input validation:** Invalid date ranges are rejected, and data quality checks identify incomplete or malformed records.

**Testability:** Automated tests use controlled sample data rather than depending on the availability of Elanco's external API.

## Limitations and Future Improvements

- The cache is stored in memory and is cleared when the application restarts.
- Data quality issues are reported but invalid records are not yet consistently excluded from every statistical calculation.
- Monthly trends include months with sightings; months with zero sightings are not currently included.
- A future frontend could provide interactive visualisations and a map-based interface.
- Additional tests could cover external API failures, caching behaviour and malformed records.

## Data Source

Elanco Tick Sightings API:

https://dev-task.elancoapps.com/

The dataset is provided for educational purposes as part of Elanco's 2026 student placement exercise.

This project reports recorded sightings and does not estimate tick prevalence or disease risk.