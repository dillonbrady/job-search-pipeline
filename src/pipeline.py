import asyncio
import random
import traceback
import psycopg2
from playwright.async_api import async_playwright
from pypdf import PdfReader

# --- SYSTEM CONFIGURATION ---
DB_CONN_STRING = "dbname=job_pipeline user=postgres password=secret host=localhost port=5432"
RESUME_PDF_PATH = "my_resume.pdf"

# Senior-level candidate profile map (10+ Years Exp / $125k Target)
MY_PROFILE_DATA = {
    "python": "10",            
    "sql": "10",               
    "html": "12",              
    "experience": "10",        
    "work authorization": "Yes", 
    "authorized": "Yes",
    "citizen": "Yes",         
    "sponsorship": "No",      
    "salary": "125000",        
    "compensation": "125000"   
}

# Optimized blacklist: removed 'senior' so you can target high-paying matching roles
TITLE_BLACKLIST = ["manager", "director", "head", "principal"]

def extract_text_from_pdf(pdf_path: str) -> str:
    """Reads a local PDF file and extracts raw text content."""
    try:
        reader = PdfReader(pdf_path)
        return "".join([page.extract_text() for page in reader.pages if page.extract_text()])
    except Exception as e:
        print(f"[-] Error reading PDF file: {e}")
        return ""

async def answer_screener_questions_deterministic(page):
    """Answers form questions using exact dictionary matches instead of AI."""
    form_elements = await page.locator(".jobs-easy-apply-form-section").all()
    
    for element in form_elements:
        label_locator = element.locator("label")
        if await label_locator.count() == 0:
            continue
        
        question_text = (await label_locator.inner_text()).lower()
        input_field = element.locator("input[type='text']")
        
        if await input_field.count() > 0 and await input_field.is_visible():
            current_val = await input_field.input_value()
            if not current_val:  
                for key, value in MY_PROFILE_DATA.items():
                    if key in question_text:
                        await input_field.fill(value)
                        break

        select_field = element.locator("select")
        if await select_field.count() > 0 and await select_field.is_visible():
            options = await select_field.locator("option").all_inner_texts()
            options_lower = [o.lower() for o in options]
            
            if "yes" in options_lower and any(k in question_text for k in ["auth", "citizen", "live in"]):
                await select_field.select_option(label="Yes")
            elif "no" in options_lower and "sponsorship" in question_text:
                await select_field.select_option(label="No")

async def execute_safe_pipeline(job_id, job_url, pdf_path):
    conn = psycopg2.connect(DB_CONN_STRING)
    cur = conn.cursor()
    
    async with async_playwright() as p:
        context = await p.chromium.launch_persistent_context("/tmp/linkedin_profile", headless=False)
        page = await context.new_page()
        
        current_step = "Navigation"
        try:
            await page.goto(job_url, timeout=30000)
            apply_btn = page.locator("button.jobs-apply-button")
            
            if await apply_btn.count() == 0:
                print(f"[-] Easy Apply button not present for: {job_url}")
                cur.execute("UPDATE job_postings SET status = 'Skipped' WHERE id = %s;", (job_id,))
                return
                
            await apply_btn.click()
            await page.wait_for_timeout(2000)
            
            while True:
                current_step = "Processing Form Fields"
                await answer_screener_questions_deterministic(page)
                
                file_input = page.locator("input[type='file']")
                if await file_input.count() > 0:
                    await file_input.set_input_files(pdf_path)
                    
                next_btn = page.locator("button:has-text('Next')")
                review_btn = page.locator("button:has-text('Review')")
                submit_btn = page.locator("button:has-text('Submit application')")
                
                if await next_btn.count() > 0 and await next_btn.is_visible():
                    await next_btn.click()
                elif await review_btn.count() > 0 and await review_btn.is_visible():
                    await review_btn.click()
                elif await submit_btn.count() > 0 and await submit_btn.is_visible():
                    print(f"[!] Staged application for {job_url}. Review manually.")
                    cur.execute("UPDATE job_postings SET status = 'Staged' WHERE id = %s;", (job_id,))
                    await asyncio.sleep(60)
                    break
                else:
                    break
                await page.wait_for_timeout(random.uniform(1500, 2500))
                
        except Exception as e:
            error_msg = f"{str(e)}\n{traceback.format_exc()}"
            try:
                dom_snapshot = await page.locator(".jobs-easy-apply-content").inner_html()
            except:
                dom_snapshot = "Failed to capture DOM."
            
            cur.execute("UPDATE job_postings SET status = 'Failed' WHERE id = %s;", (job_id,))
            cur.execute("""
                INSERT INTO automation_errors (job_posting_id, error_step, error_message, dom_snapshot) 
                VALUES (%s, %s, %s, %s);
            """, (job_id, current_step, error_msg, dom_snapshot))
        finally:
            conn.commit()
            cur.close()
            conn.close()
            await context.close()
