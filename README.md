# 🚀 Production-Grade Automated Job Search Pipeline

An enterprise-ready, event-driven data pipeline designed to automate the discovery, tracking, and staging of targeted remote software engineering and data roles. Built entirely using Python, PostgreSQL, and Playwright, this architecture treats the traditional job search as a highly optimized data engineering lifecycle.

---

## 🛠️ Tech Stack & Architecture

- **Orchestration & Logic:** Python 3 (Asyncio, Playwright, PyPDF)
- **Database Engine:** PostgreSQL (Relational schema with status tracking)
- **Scheduling:** Linux Crontab / Task Scheduler
- **Security Blueprint:** Local persistent browser contexts & human-in-the-loop validation checkpoints

[ Web Targets / Sourcing ] ──(Async Playwright)──> [ PostgreSQL Engine ]
│
(Deterministic Profiler)
│
[ Local Machine Display ] <───(Staged Form Modal) <────────┘

---

## 📊 Database Schema Design

The system runs a normalized database layer to manage application workflows, eliminate listing duplicates, and catch UI bottlenecks natively.

```sql
CREATE TABLE job_postings (
    id SERIAL PRIMARY KEY,
    job_title VARCHAR(255) NOT NULL,
    job_url TEXT UNIQUE NOT NULL,
    status VARCHAR(50) DEFAULT 'Scraped', -- Scraped, Skipped, Staged, Failed
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

CREATE TABLE automation_errors (
    id SERIAL PRIMARY KEY,
    job_posting_id INT REFERENCES job_postings(id) ON DELETE CASCADE,
    error_step VARCHAR(100) NOT NULL,
    error_message TEXT NOT NULL,
    logged_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);
```

---

## 🧠 Key Features Implemented

### 1. Anti-Bot Evasion & Account Security
- Uses localized, persistent user data directories to preserve active session cookies and bypass login prompts.
- Avoids AI-based formatting assumptions by running deterministic keyword-to-metric maps.
- Implements microsecond-jittered pacing configurations (`random.uniform`) to replicate human typing signatures.

### 2. Defending Code Execution (Robust Error Catching)
- The core loop wraps web page navigation and DOM mutation in tight `try/except` clauses.
- If a form layout changes or hits an unmapped input element, the script catches the failure, logs the diagnostic footprint to `automation_errors`, and immediately moves to the next database row without breaking the execution stack.

### 3. Human-in-the-Loop Safeguard
- To maintain a 100% accurate application history, the submission layer pauses right before the absolute final submission click. This leaves the browser active for a visual validation window, ensuring no incorrect form states are submitted.

---

## 🚀 Getting Started

1. **Clone the repository and install system dependencies:**
   ```bash
   pip install playwright pypdf psycopg2-binary
   playwright install chromium
   ```
2. **Initialize your PostgreSQL instance and drop your baseline resume as `my_resume.pdf`.**
3. **Execute the processing orchestrator loop:**
   ```bash
   python3 run_pipeline.py
   ```
   
