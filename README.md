# Simulation Scripting Backend

This repository contains a collection of example notebooks and utilities that can be used to build a backend service for running simulations. The notebooks demonstrate how to interact with services like OpenAI, Neo4j and Astra DB and serve as a basis for a Flask API.

## Project Purpose

The notebooks in this project show different integration points for data storage and AI helpers that are useful when building simulation workflows. They are intended to be combined into a Flask server which exposes API endpoints for your simulations.

## Setup Steps

1. Clone the repository and create a Python virtual environment:

```bash
git clone <repo_url>
cd SimulationScripting
python3 -m venv venv
source venv/bin/activate
```

2. Install the dependencies. The notebooks rely on several libraries including Flask, OpenAI, SimPy, AstraPy and Neomodel:

```bash
pip install flask openai simpy astrapy neo4j neomodel pandas python-docx beautifulsoup4
```

## Environment Variables

A few environment variables are required for the external services used in the notebooks:

- `OPENAI_API_KEY` – API key for the OpenAI client.
- `ASTRA_ENDPOINT` – Astra DB API endpoint.
- `ASTRA_TOKEN_NAME` – Name of the token variable used with Astra DB.
- `NEO4J_URI` – Connection URI for the Neo4j instance.
- `NEO4J_USERNAME` – Username for Neo4j.
- `NEO4J_LOCALPWD` – Password for Neo4j.

Export these in your shell or define them in a `.env` file before launching the server.

## Running the Flask Server

Once the environment variables are set, run the Flask application to expose the simulation endpoints. Assuming a file named `app.py` creates the Flask application, you can start it with:

```bash
flask --app app.py run
```

The server will be available at `http://127.0.0.1:5000/`.

## Example Requests

Here is a basic example of sending a request to an API endpoint called `/simulate`:

```bash
curl -X POST http://127.0.0.1:5000/simulate \
     -H 'Content-Type: application/json' \
     -d '{"prompt": "Run financial simulation"}'
```

The actual endpoints will depend on how you combine the code from the notebooks into a Flask application.


