This repository contains a collection of notebooks and helper modules used in my simulation projects.

## Configuration

Environment variables are used to access external services. You can either set them in your shell or create a `.env` file in the project root. The following variables may be required depending on which notebooks you run:

- `OPENAI_API_KEY` &ndash; API token for the OpenAI client
- `NEO4J_URI` &ndash; connection URI for your Neo4j instance
- `NEO4J_USERNAME` &ndash; Neo4j username
- `NEO4J_LOCALPWD` &ndash; password for the above user
- `ASTRA_ENDPOINT` &ndash; endpoint URL for Astra DB
- `ASTRA_TOKEN` &ndash; API token for Astra DB (optional if using other auth)

Create a `.env` file with lines of the form `VAR=value` or export these variables before running the notebooks.

