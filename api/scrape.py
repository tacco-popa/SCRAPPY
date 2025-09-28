from concurrent.futures import ThreadPoolExecutor, as_completed
from dataclasses import dataclass
from typing import List, Optional, Tuple
import re

import pandas as pd
import requests
from bs4 import BeautifulSoup
from fastapi import FastAPI, HTTPException
from fastapi.responses import StreamingResponse, JSONResponse
from pydantic import BaseModel, Field, HttpUrl

app = FastAPI()

HEADERS = {
    "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36"
}
PAGE_REGEX = re.compile(r"([?&])page=(\d+)")

@dataclass
class TableSpec:
    css_selector: str = "table"
    table_index: int = 0
    header_row_strategy: str = "auto"  # [auto | th | first_row]

class ScrapeRequest(BaseModel):
    template: HttpUrl | str = Field(..., description="Base URL with optional {page}. If missing, ?page= is appended.")
    css_selector: str = Field("table", description="CSS selector for the table")
    table_index: int = Field(0, ge=0)
    header_strategy: str = Field("auto", pattern=r"^(auto|th|first_row)$")
    start_page: int = Field(1, ge=1)
    end_page: int = Field(1, ge=1)
    concurrency: int = Field(10, ge=1, le=32)
    max_pages_per_request: int = Field(100, ge=1, le=100)  # serverless safety cap
    format: str = Field("csv", pattern=r"^(csv|json)$")

def build_url_from_template(template: str, page: int) -> str:
    if "{page}" in template:
        return template.replace("{page}", str(page))
    if PAGE_REGEX.search(template):
        return PAGE_REGEX.sub(lambda m: f"{m.group(1)}page={page}", template, count=1)
    return template + ("&" if "?" in template else "?") + f"page={page}"

def fetch_html(url: str, timeout: int = 20) -> Optional[str]:
    try:
        r = requests.get(url, headers=HEADERS, timeout=timeout)
        r.raise_for_status()
        return r.text
    except Exception:
        return None

def pick_table(html: str, spec: TableSpec) -> Optional[BeautifulSoup]:
    soup = BeautifulSoup(html, "html.parser")
    tables = soup.select(spec.css_selector)
    if not tables or spec.table_index >= len(tables):
        return None
    return tables[spec.table_index]

def infer_headers(table: BeautifulSoup, strategy: str = "auto") -> Tuple[List[str], List[BeautifulSoup]]:
    rows = table.find_all("tr")
    if not rows:
        return [], []
    ths = rows[0].find_all("th")
    if strategy in ("auto", "th") and ths:
        headers = [th.get_text(strip=True) or f"col_{i+1}" for i, th in enumerate(ths)]
        return headers, rows[1:]
    tds = rows[0].find_all("td")
    if strategy in ("auto", "first_row") and tds:
        headers = [td.get_text(strip=True) or f"col_{i+1}" for i, td in enumerate(tds)]
        return headers, rows[1:]
    first_data = rows[0].find_all(["td", "th"]) or []
    n = max(len(first_data), 1)
    headers = [f"col_{i+1}" for i in range(n)]
    return headers, rows

def parse_rows(data_rows: List[BeautifulSoup], ncols: int) -> List[List[str]]:
    out = []
    for r in data_rows:
        cols = r.find_all(["td", "th"])
        vals = [c.get_text(strip=True) for c in cols]
        if not vals:
            continue
        if len(vals) < ncols:
            vals += [""] * (ncols - len(vals))
        elif len(vals) > ncols:
            vals = vals[:ncols]
        out.append(vals)
    return out

def scrape_one_page(url: str, spec: TableSpec) -> Optional[pd.DataFrame]:
    html = fetch_html(url)
    if html is None:
        return None
    table = pick_table(html, spec)
    if not table:
        return None
    headers, data_rows = infer_headers(table, spec.header_row_strategy)
    data = parse_rows(data_rows, len(headers))
    if not data:
        return None
    return pd.DataFrame(data, columns=headers)

def scrape_pages(template: str, pages: List[int], spec: TableSpec, concurrency: int = 10) -> pd.DataFrame:
    results: List[pd.DataFrame] = []
    with ThreadPoolExecutor(max_workers=concurrency) as ex:
        futures = {ex.submit(scrape_one_page, build_url_from_template(template, p), spec): p for p in pages}
        for fut in as_completed(futures):
            df = fut.result()
            if df is not None and not df.empty:
                results.append(df)
    if not results:
        return pd.DataFrame()
    return pd.concat(results, ignore_index=True)

@app.get("/api/health")
async def health():
    return {"status": "ok"}

@app.post("/api/scrape")
async def scrape(req: ScrapeRequest):
    if req.end_page < req.start_page:
        raise HTTPException(status_code=400, detail="end_page must be >= start_page")
    page_count = req.end_page - req.start_page + 1
    if page_count > req.max_pages_per_request:
        raise HTTPException(status_code=400, detail=f"Too many pages (max {req.max_pages_per_request}).")

    spec = TableSpec(req.css_selector, int(req.table_index), req.header_strategy)
    pages = list(range(int(req.start_page), int(req.end_page) + 1))
    df = scrape_pages(str(req.template), pages, spec, req.concurrency)

    if df.empty:
        return JSONResponse({"rows": 0, "message": "No data found. Tweak selector/table index/header strategy."}, status_code=200)

    if req.format == "json":
        return JSONResponse({"rows": len(df), "data": df.to_dict(orient="records")})

    csv_bytes = df.to_csv(index=False).encode("utf-8")
    return StreamingResponse(
        iter([csv_bytes]),
        media_type="text/csv",
        headers={"Content-Disposition": "attachment; filename=scraped_table.csv"},
    )
