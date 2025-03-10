# pest-and-disease-management

# Description

The Pest and Disease Management service takes in data via datasets or live measurements and rules created\
by a user, and returns when a rule was satisfied on the specified dataset.

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
A list of APIs can be viewed in the API.md file, and a full list of APIs can be viewed [here](https://editor-next.swagger.io/?url=https://gist.githubusercontent.com/vlf-stefan-drobic/71d21b192db0b968278a48d6e5e6d9cb/raw/dd4bd697421dba235210040fa272a0bb1fbaaa5c/gistfile1.txt).

The basic flow for this service is as follows:
1. The user registers and/or logs in;
2. The user creates their parcel/s
3. The user creates one or more pest and/or disease models
4. The user queries the system for either risk index or growing degree days (GDD) for pest and disease models respectively

# Contribution
Please contact the maintainer of this repository.

# License
[European Union Public License 1.2](https://github.com/openagri-eu/pest-and-disease-management/blob/main/LICENSE)
