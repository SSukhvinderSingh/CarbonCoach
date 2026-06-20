# CarbonCoach

A Flask-based web app that tracks your daily carbon footprint, provides personalized recommendations, and generates conversational insights using Google Gemini AI.

## Features

- **Chat-based activity logging** — Describe your day in natural language (e.g., "I drove 10 km and had chicken for dinner") and CarbonCoach extracts activities automatically
- **Footprint calculation** — Estimates CO₂ emissions across transport, diet, home energy, and waste
- **Personalized recommendations** — Suggests the most impactful swaps based on your highest-emitting category
- **Trend tracking** — Monitors your 7-day trend (improving / steady / worsening)
- **Benchmarking** — Compares your daily total against India and global averages
- **CSV export** — Download your activity history
- **Multiple profiles** — Switch between different users
- **Gemini AI integration** — Optional Google Gemini API key for smarter activity extraction and responses
- **Fallback mode** — Works fully without an API key using keyword-based extraction and template replies

## Requirements

- Python 3.10+
- pip

## Setup

1. Clone the repo and navigate into it:
   ```bash
   git clone https://github.com/SSukhvinderSingh/CarbonCoach.git
   cd CarbonCoach
   ```

2. Create a virtual environment and install dependencies:
   ```bash
   python -m venv .venv
   source .venv/bin/activate    # Linux/macOS
   .venv\Scripts\activate       # Windows
   pip install -r requirements.txt
   ```

3. (Optional) Create a `.env` file for Gemini AI integration:
   ```bash
   cp .env.example .env
   ```
   Then edit `.env` and add your `GEMINI_API_KEY`. The app works without this — it falls back to keyword extraction and template replies.

4. Run the app:
   ```bash
   python app.py
   ```
   Open http://localhost:5000 in your browser.

## Usage

1. Enter your name on the login screen and tap **Login**
2. Start chatting — e.g., *"I took the bus for 5 km and had a veg meal"*
3. CarbonCoach logs the activity, calculates the CO₂ footprint, and shows suggestions
4. Use the **Summary** panel to see daily totals, category breakdown, trend, and recommendations
5. Export your data as CSV with the **Export** button

## API Endpoints

| Method | Path | Description |
|--------|------|-------------|
| POST | `/api/login` | Create/switch to a guest session |
| GET | `/api/sessions` | List all sessions |
| POST | `/api/chat` | Log activities via chat message |
| GET | `/api/summary` | Get daily footprint summary with recommendations |
| GET | `/api/activities` | Get today's logged activities |
| GET | `/api/export` | Download activity history as CSV |
| POST | `/api/clear` | Clear session data |

## Configuration

Environment variables (`.env`):

| Variable | Default | Description |
|----------|---------|-------------|
| `GEMINI_API_KEY` | — | Google Gemini API key (optional) |
| `GEMINI_MODEL` | `gemini-2.0-flash` | Gemini model name |
| `GRID_FACTOR_KG_CO2_PER_KWH` | `0.71` | Grid emission factor (India default) |
| `PORT` | `5000` | Server port |
| `FLASK_ENV` | — | Set to `development` for debug mode |

## Deployment (PythonAnywhere)

### One-time setup

1. Create a free account at [pythonanywhere.com](https://www.pythonanywhere.com)
2. Open a **Bash console** from the Dashboard and run:
   ```bash
   git clone https://github.com/SSukhvinderSingh/CarbonCoach.git
   cd CarbonCoach
   python -m venv .venv
   source .venv/bin/activate
   pip install -r requirements.txt
   ```
3. Go to **Web → Add a new web app → Manual configuration → Python 3.12**
4. Set the **Source code** to: `/home/YOUR_USERNAME/CarbonCoach`
5. Set the **Working directory** to: `/home/YOUR_USERNAME/CarbonCoach`
6. Set the **Virtualenv** to: `/home/YOUR_USERNAME/CarbonCoach/.venv`
7. Open the **WSGI configuration file** link and replace its contents with:
   ```python
   import sys
   import os
   path = os.path.dirname(os.path.abspath(__file__))
   if path not in sys.path:
       sys.path.insert(0, path)
   from app import app as application
   ```
8. Go back and click the **Reload** button. Your app is live at `YOUR_USERNAME.pythonanywhere.com`.

### Auto-deploy (GitHub Actions)

The repo includes a workflow that auto-deploys on every `git push` to `main`. To enable it:

1. **Generate an SSH key** (in your terminal, NOT on PA):
   ```bash
   ssh-keygen -t ed25519 -f ~/.ssh/pa_deploy -C "github-actions"
   ```
2. **Add the public key** to PythonAnywhere: go to **Account → SSH keys → Add a new key** and paste `~/.ssh/pa_deploy.pub`
3. **Add secrets** to GitHub at https://github.com/SSukhvinderSingh/CarbonCoach/settings/secrets/actions:
   - `PA_USER` — your PythonAnywhere username
   - `PA_SSH_KEY` — the contents of `~/.ssh/pa_deploy` (the private key)

After that, every push to `main` automatically pulls on PA and reloads the app.

### Environment variables on PA

Set these via **Web → Environment variables** on PythonAnywhere:
- `GEMINI_API_KEY` — your Google Gemini key (optional)
- `GEMINI_MODEL` — `gemini-2.0-flash`
- `GRID_FACTOR_KG_CO2_PER_KWH` — `0.71`

## Project Structure

```
CarbonCoach/
├── app.py                               # Flask application & API routes
├── footprint_calculator.py              # CO₂ calculation logic
├── recommendation_engine.py             # Trend analysis & swap suggestions
├── conversational_insight_generator.py  # NLU & Gemini integration
├── progress_tracker.py                  # SQLite session & activity storage
├── templates/
│   └── index.html                       # Single-page frontend
├── tests/
│   ├── test_footprint_calculator.py
│   ├── test_recommendation_engine.py
│   ├── test_conversational_agent.py
│   ├── test_progress_tracker.py
│   └── test_agent.py
├── requirements.txt
└── .env.example
```

## Running Tests

```bash
pytest -v
```
