# Surplus App

A [Plotly Dash](https://plotly.com/dash/) app for goals-based investing surplus optimization and risk premium calculations.

## Project Structure

- `src/app.py` — the Dash application (layout, callbacks, `server` object for gunicorn)
- `Procfile` — Heroku process definition (`gunicorn --chdir src app:server`)
- `requirements.txt` — Python dependencies
- `.python-version` — Python version for Heroku (major.minor only, so patch security updates apply automatically)

## Running Locally

```
pip install -r requirements.txt
python src/app.py
```

Then navigate to http://127.0.0.1:8891/ in your browser.

## Deploying to Heroku

```
git push heroku main
```

Heroku reads `Procfile` and `.python-version` automatically; no additional configuration is required.
