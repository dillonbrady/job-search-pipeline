import asyncio
import random
import sqlite3  # Native Python serverless database engine
from playwright.async_api import async_playwright

DB_FILE = "jobs.db"

# --- SENIOR OUTREACH TEMPLATE ---
OUTREACH_TEMPLATE = (
    "Hi {recruiter_name},\n\n"
    "I just submitted my application for the {job_title} role at {company_name}. "
    "Given my 10+ years of engineering experience specializing in Python, SQL, and robust "
    "web architectures, I wanted to reach out directly. I excel at designing high-throughput, "
    "fault-tolerant data systems and automations, and I would love to connect to discuss how "
    "my technical background aligns with your current infrastructure goals.\n\n"
    "Best regards,\nDillon Brady"
)

async def automate_recruiter_outreach():
    conn = sqlite3.connect(DB_FILE)
    cur = conn.cursor()
    
    # Select jobs that are staged but haven't had recruiter outreach yet
    cur.execute("""
        SELECT j.id, j.job_title, j.job_url, j.job_title -- Placeholder fallback for company name
        FROM job_postings j
        WHERE j.status = 'Staged' AND j.outreach_status = 'Pending'
        LIMIT 5;
    """)
    jobs_to_message = cur.fetchall()
    
    if not jobs_to_message:
        print("[*] No pending job applications require recruiter outreach right now.")
        return

    async with async_playwright() as p:
        context = await p.chromium.launch_persistent_context("/tmp/linkedin_profile", headless=False)
        page = await context.new_page()
        
        for job_id, job_title, job_url, company_name in jobs_to_message:
            print(f"[*] Extracting recruiter metadata for: {job_title}")
            await page.goto(job_url)
            await page.wait_for_timeout(2000)
            
            recruiter_section = page.locator(".hirer-card__hirer-information a")
            
            if await recruiter_section.count() == 0:
                print(f"[-] No direct recruiter profile attached to posting ID {job_id}.")
                cur.execute("UPDATE job_postings SET outreach_status = 'No Recruiter' WHERE id = ?;", (job_id,))
                conn.commit()
                continue
                
            recruiter_url = await recruiter_section.first.get_attribute("href")
            recruiter_name_raw = await recruiter_section.first.locator(".jobs-poster__name").inner_text()
            recruiter_name = recruiter_name_raw.split()[0] if recruiter_name_raw else "There"
            
            print(f"[+] Found recruiter: {recruiter_name}. Opening profile window...")
            await page.goto(recruiter_url)
            await page.wait_for_timeout(3000)
            
            message_btn = page.locator("button:has-text('Message')")
            
            if await message_btn.count() > 0 and await message_btn.is_visible():
                await message_btn.click()
                await page.wait_for_timeout(1500)
                
                final_message = OUTREACH_TEMPLATE.format(
                    recruiter_name=recruiter_name,
                    job_title=job_title,
                    company_name=company_name
                )
                
                textbox = page.locator("div[role='textbox']")
                await textbox.click()
                await textbox.fill(final_message)
                
                print(f"[!] Message perfectly drafted for {recruiter_name}. Review and hit Send manually.")
                cur.execute("""
                    UPDATE job_postings 
                    SET outreach_status = 'Contacted', recruiter_name = ?, recruiter_url = ? 
                    WHERE id = ?;
                """, (recruiter_name_raw, recruiter_url, job_id))
                conn.commit()
                
                await asyncio.sleep(30)
            else:
                print(f"[!] Message box locked for {recruiter_name} (Premium wall).")
                cur.execute("UPDATE job_postings SET outreach_status = 'Failed' WHERE id = ?;", (job_id,))
                conn.commit()
                
            await asyncio.sleep(random.uniform(5.0, 15.0))
            
        await context.close()
    cur.close()
    conn.close()

if __name__ == "__main__":
    asyncio.run(automate_recruiter_outreach())
