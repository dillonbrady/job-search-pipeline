import sqlite3

def add_live_job():
    conn = sqlite3.connect("jobs.db")
    cur = conn.cursor()
    
    print("--- 📥 Real-Time Job Ingestion Tool ---")
    title = input("Enter Job Title: ")
    url = input("Enter LinkedIn Job URL: ")
    
    try:
        cur.execute("INSERT INTO job_postings (job_title, job_url, status) VALUES (?, ?, 'Scraped');", (title, url))
        conn.commit()
        print("[+] Job successfully injected into the automation queue!")
    except sqlite3.IntegrityError:
        print("[-] Error: This exact URL is already in your tracking database.")
        
    cur.close(); conn.close()

if __name__ == "__main__":
    add_live_job()
