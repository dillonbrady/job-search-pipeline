-- Track individual companies and their career page metadata
CREATE TABLE companies (
    id SERIAL PRIMARY KEY,
    company_name VARCHAR(255) UNIQUE NOT NULL,
    career_page_url TEXT
);

-- Main data engine tracking job listings and workflow application pipelines
CREATE TABLE job_postings (
    id SERIAL PRIMARY KEY,
    company_id INT REFERENCES companies(id) ON DELETE SET NULL,
    job_title VARCHAR(255) NOT NULL,
    job_url TEXT UNIQUE NOT NULL,
    job_description TEXT,
    posted_date DATE,
    status VARCHAR(50) DEFAULT 'Scraped', -- Tracks state: Scraped, Skipped, Staged, Failed, Applied
    tailored_resume_path TEXT,
    recruiter_name VARCHAR(255),
    recruiter_url TEXT,
    outreach_status VARCHAR(50) DEFAULT 'Pending', -- State: Pending, Contacted, Failed, No Recruiter
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- Defensive fault-tolerance table to log automation and DOM exceptions natively
CREATE TABLE automation_errors (
    id SERIAL PRIMARY KEY,
    job_posting_id INT REFERENCES job_postings(id) ON DELETE CASCADE,
    error_step VARCHAR(100) NOT NULL, -- Step failure context (e.g., 'Navigation', 'File Upload')
    error_message TEXT NOT NULL,
    dom_snapshot TEXT, -- Captures raw HTML layout block at failure time for local debugging
    logged_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);
