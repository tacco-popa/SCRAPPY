# main.py
from api.scrape import app
from fastapi.responses import HTMLResponse
from pathlib import Path

@app.get("/", response_class=HTMLResponse)
def home():
    return Path("index.html").read_text(encoding="utf-8")
