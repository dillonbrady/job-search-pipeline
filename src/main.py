import asyncio
import time
import random
import psycopg2
# Updated folder paths for clean module initialization
from pipeline import execute_safe_pipeline, TITLE_BLACKLIST, RESUME_PDF_PATH
from outreach import automate_recruiter_outreach



import os
from dotenv import load_dotenv

# Automatically look for and read the local hidden .env file
load_dotenv()

# Build the connection parameter matrix dynamically using the extracted environment strings
DB_CONN_STRING = (
    f"dbname={os.getenv('DB_NAME')} "
    f"user={os.getenv('DB_USER')} "
    f"password={os.getenv('DB_PASSWORD')} "
    f"host={os.getenv('DB_HOST')} "
    f"port={os.getenv('DB_PORT')}"
)



def get_next_scraped_jobs(limit=5):
    """Fetches a batch of unapplied jobs from the PostgreSQL database."""
    conn = psycopg2.connect(DB_CONN_STRING)
    cur = conn.cursor()
    cur.execute("""
        SELECT id, job_title, job_url 
        FROM job_postings 
        WHERE status = 'Scraped' 
        ORDER BY created_at ASC 
        LIMIT %s;
    """, (limit,))
    jobs = cur.fetchall()
    cur.close()
    conn.close()
    return jobs

def flag_skipped_job(job_id, reason):
    """Updates database status for filtered jobs."""
    conn = psycopg2.connect(DB_CONN_STRING)
    cur = conn.cursor()
    cur.execute("UPDATE job_postings SET status = %s WHERE id = %s;", (reason, job_id))
    conn.commit()
    cur.close()
    conn.close()

async def run_master_orchestrator():
    print("[*] Starting Master Job Application and Outreach Orchestrator...")
    
    # 1. Fetch available queue rows
    jobs = get_next_scraped_jobs(limit=5)
    if not jobs:
        print("[*] Queue empty. No jobs marked 'Scraped' found in database.")
        return
        
    print(f"[*] Processing a batch of {len(jobs)} jobs...")
    
    for job_id, title, url in jobs:
        # 2. Check against your optimized Title Blacklist
        if any(keyword in title.lower() for keyword in TITLE_BLACKLIST):
            print(f"[Skipping] '{title}' matches excluded management keywords.")
            flag_skipped_job(job_id, 'Skipped (Blacklist)')
            continue
            
        print(f"\n[Processing] Application starting for: {title}")
        
        # 3. Trigger the safe form application logic
        await execute_safe_pipeline(job_id, url, RESUME_PDF_PATH)
        
        # Jittered pacing delay between browser tasks to simulate human behavior
        sleep_time = random.uniform(10.0, 20.0)
        print(f"[*] Post-application cooldown: Sleeping for {sleep_time:.1f}s...")
        await asyncio.sleep(sleep_time)

    # 4. Trigger the recruiter messaging loop for any successfully 'Staged' apps
    print("\n[*] Main applications processed. Initializing Recruiter Outreach...")
    await automate_recruiter_outreach()
    print("[*] Batch completed successfully.")

if __name__ == "__main__":
    asyncio.run(run_master_orchestrator())
