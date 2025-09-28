# 📊 SCRAPPY — Smart Web Scraping Toolkit

> **Easily scrape data from any paginated website, auto-detect tables, and export your results — deployable instantly on Vercel.**

**Live Demo:** [https://scrappy-git-main-tbzs-projects-722eb033.vercel.app/](https://scrappy-git-main-tbzs-projects-722eb033.vercel.app/)

SCRAPPY is a lightweight, **Vercel-ready web scraping solution** built with **FastAPI** and **BeautifulSoup**.  
It features a clean static HTML frontend and a serverless backend, perfect for fast deployments and scalable scraping tasks.

---

## 🚀 Features

- 🔎 **Smart Table Detection** – Automatically finds headers and rows.  
- 📄 **Pagination Support** – Works with `{page}` placeholders or query params like `?page=2`.  
- ⚡ **Concurrent Scraping** – Fetch multiple pages in parallel for speed.  
- 📊 **Flexible Output** – Download results as CSV or JSON.  
- ☁️ **Vercel-Ready** – Deploy in one click, fully serverless.  
- 🖥️ **Simple UI** – Paste a URL and start scraping right away.

---

## 📂 Project Structure

```
SCRAPPY/
│
├── api/               # Serverless backend
│   └── scrape.py      # FastAPI scraping function
│
├── index.html         # Static frontend UI
├── main.py            # Entrypoint for Vercel (serves index + routes API)
├── requirements.txt   # Python dependencies
└── README.md          # This file
```

---

## 🛠️ Getting Started

### 1. Clone the Repo
```bash
git clone https://github.com/your-username/SCRAPPY.git
cd SCRAPPY
```

### 2. Install Dependencies
Make sure you have **Python 3.11+** installed.

```bash
pip install -r requirements.txt
```

### 3. Run Locally
Start the FastAPI server:
```bash
uvicorn api.scrape:app --reload
```

Visit:
- **Frontend:** [http://127.0.0.1:8000/](http://127.0.0.1:8000/)
- **API Endpoint:** [http://127.0.0.1:8000/api/scrape](http://127.0.0.1:8000/api/scrape)

---

## 🌐 Deploying to Vercel

### **Option A — Simplest Setup**
Deploy directly:
1. Push your code to GitHub.
2. Go to [Vercel](https://vercel.com/).
3. Import your repo.
4. Vercel automatically detects:
   - `index.html` → static site root
   - `api/` → Python serverless function
5. Click **Deploy** 🚀

**Live version:** [https://scrappy-git-main-tbzs-projects-722eb033.vercel.app/](https://scrappy-git-main-tbzs-projects-722eb033.vercel.app/)

---

### **Option B — With FastAPI Preset**
If Vercel needs an explicit app:
- Keep `main.py` at the root with this content:
  ```python
  from api.scrape import app
  from fastapi.responses import HTMLResponse
  from pathlib import Path

  @app.get("/", response_class=HTMLResponse)
  def home():
      return Path("index.html").read_text(encoding="utf-8")
  ```
- Then redeploy.

---

## 📡 Example API Payload

You can test the backend directly by POSTing JSON to `/api/scrape`.

Example request:
```json
{
  "template": "https://example.com/products?page={page}",
  "css_selector": "table",
  "table_index": 0,
  "header_strategy": "auto",
  "start_page": 1,
  "end_page": 5,
  "concurrency": 10,
  "format": "csv"
}
```

Using **cURL**:
```bash
curl -X POST https://scrappy-git-main-tbzs-projects-722eb033.vercel.app/api/scrape -H "Content-Type: application/json" -d '{
  "template": "https://example.com/products?page={page}",
  "start_page": 1,
  "end_page": 3
}'
```

---

## 📸 Screenshots


![Screenshot_28-9-2025_13257_scrappy-git-main-tbzs-projects-722eb033 vercel app](https://github.com/user-attachments/assets/7e55402f-844a-4086-8f29-114cb02f40e7)



---

## 🤝 Contributing
Conributions are welcomed 
To contribute:
1. Fork this repo
2. Create a feature branch (`git checkout -b feature-name`)
3. Commit your changes
4. Push and open a pull request

---

## 📝 License
This project is open source and available under the **MIT License**.
