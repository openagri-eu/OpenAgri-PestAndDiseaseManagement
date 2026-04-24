# Pest and Disease Management

:eu: *"This service was created in the context of OpenAgri project (https://horizon-openagri.eu/). OpenAgri has received funding from the EU’s Horizon Europe research and innovation programme under Grant Agreement no. 101134083."*
# Description

The Pest and Disease Management(P&DM) service supports farmers by providing multiple ways of calculating a risk associated with
diseases, Growing Degree Days for pests and other mechanisms.

The service now includes a **fuzzy risk engine** (Mamdani fuzzy inference) that replaces the previous rule-engine approach. Crops and their associated threat models (pests/diseases) are managed via dedicated APIs, and risk scores (0–100) with classifications (Low / Moderate / High / Critical) are returned in the OpenAGRI JSON-LD format.

# Requirements

<ul>
    <li>git</li>
    <li>docker</li>
    <li>docker-compose</li>
</ul>

Docker version used during development: 27.0.3

# Installation

There are two ways to install this service, via docker or directly from source.

<h3> Deploying from source </h3>

When deploying from source, use python 3:11.\
Also, you should use a [venv](https://peps.python.org/pep-0405/) when doing this.

A list of libraries that are required for this service is present in the "requirements.txt" file.\
This service uses FastAPI as a web framework to serve APIs, alembic for database migrations sqlalchemy for database ORM mapping.

<h3> Deploying via docker </h3>

After installing <code> docker </code> you can run the following commands to run the application:

```
docker compose build
docker compose up
```

The application will be served on http://127.0.0.1:{SERVICE_PORT}, where SERVICE_PORT is the value read from the .env (default 8003)

# Documentation
You can find working examples for GDD and Risk Index calculation in the following pages:

- [GDD](scripts/gdd.md)
- [Risk Index](scripts/riskindex.md)

A list of APIs can be viewed in the [API.md](https://github.com/openagri-eu/pest-and-disease-management/blob/main/API.md) file, and a full list of APIs can be viewed [here](https://editor-next.swagger.io/?url=https://gist.githubusercontent.com/vlf-stefan-drobic/71d21b192db0b968278a48d6e5e6d9cb/raw/dd4bd697421dba235210040fa272a0bb1fbaaa5c/gistfile1.txt).

The basic flow for this service is as follows:
1. The user registers and/or logs in;
2. The user creates their parcel/s (historical weather data is seeded automatically on creation)
3. The user creates one or more pest and/or disease models
4. The user queries the system for either risk index or growing degree days (GDD) for pest and disease models respectively

**Fuzzy risk flow (new):**
1. Crops and threat models (with fuzzy rules and biological parameters) are pre-seeded from the reference dataset on first migration
2. The user creates a parcel — one year of historical weather data is fetched automatically from OpenMeteo
3. The user calls `/api/v1/fuzzy-risk/calculate/` with a parcel ID and date range for historical risk, or `/api/v1/fuzzy-risk/forecast/` for a forward-looking risk over the coming days
4. Responses follow the OpenAGRI JSON-LD format with a 0–100 risk score and a risk class per pest per day

New API prefixes:

| Prefix | Purpose |
|--------|---------|
| `/api/v1/crop/` | Manage crop records |
| `/api/v1/threat-model/` | Manage per-pest fuzzy rule sets; bulk import from Excel or JSON |
| `/api/v1/fuzzy-risk/` | Calculate historical or forecast pest/disease risk |

# Contribution
Please contact the maintainer of this repository.

# License
This project code is licensed under the EUPL 1.2 license, see the [LICENSE](https://github.com/agstack/OpenAgri-PestAndDiseaseManagement/blob/main/LICENSE) file for more details.
Please note that each service may have different licenses, which can be found their specific source code repository.
