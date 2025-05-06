## agent-test

A sample project demonstrating an AI-powered agents, built with FastAPI and Dash.

### Features

* **FastAPI** backend exposing a `/chat` endpoint for conversational queries via LLM agents.
* **Dash** front-end UI for real-time chat with selectable AI models and agents.
* **Research Agent**: performs multi-step Google searches and fetches page content.
* **Aula Agent**: integrates with the Danish Aula school system to fetch profiles, messages, calendar events, etc.
* Configuration via environment variables (`.env`).

### Prerequisites

* Python 3.13+
* A valid Azure OpenAI key and endpoint (optional)
* Anthropic API credentials (optional)
* Aula login credentials (for `aula_agent`)
* `git`, `pip` or `poetry`

Please check src/constants.py, and list available models.

### Installation

1. Clone the repository:

   ```bash
   git clone git@github.com:A-Hoier/agents-playground.git
   cd agent-playground
   ```

3. Install dependencies:

   ```bash
   uv sync
   ```

4. Copy the example environment file and fill in your credentials:

   ```bash
   cp .env.example .env
   ```

5. Edit `.env` and set all required variables (see **Configuration** below).

### Configuration

The application uses \[pydantic-settings] to load variables from `.env`. 

* **Frontend**

  * `BACKEND_URL` (e.g. `http://localhost:8000/`)

### Usage


#### Use docker compose:


```bash
docker compose up
```

### Alternatively, run the backend and frontend separately:
#### Start the backend

```bash
uv run uvicorn api:app --reload
```

* The API will be available at `http://localhost:8000`
* Swagger UI docs at `http://localhost:8000/docs`

#### Start the Dash UI
in another terminal:

```bash
uv run python app.py
```

* Opens a local server (default `http://127.0.0.1:8050`) with the chat interface.

#### Chatting

* Select an **LLM model** (e.g. `gpt-4o`) and an **agent** (`research_agent` or `aula_agent`).
* Type a message and hit **Send** or **enter**.
