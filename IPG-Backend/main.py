from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
from typing import Optional
import os
import time
import requests

app = FastAPI(title="IPG Backend API")

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

class PostRequest(BaseModel):
    content: str
    linkedin_email: str
    linkedin_password: str

class JobSearchRequest(BaseModel):
    skills: list[str]
    locations: list[str] = ["Remote"]

class WhatsAppRequest(BaseModel):
    phone: str
    message: str

class ResumeParseRequest(BaseModel):
    resume_text: str
    api_key: str

@app.get("/")
async def root():
    return {"status": "ok", "message": "IPG Backend API is running"}

@app.get("/health")
async def health():
    return {"status": "healthy"}

@app.post("/api/linkedin/post")
async def post_to_linkedin(data: PostRequest):
    try:
        from selenium import webdriver
        from selenium.webdriver.common.by import By
        from selenium.webdriver.support.ui import WebDriverWait
        from selenium.webdriver.support import expected_conditions as EC
        from selenium.webdriver.chrome.options import Options
        from selenium.webdriver.common.keys import Keys
        import time
        
        chrome_options = Options()
        chrome_options.add_argument('--headless')
        chrome_options.add_argument('--no-sandbox')
        chrome_options.add_argument('--disable-dev-shm-usage')
        chrome_options.add_argument('--disable-blink-features=AutomationControlled')
        chrome_options.add_argument('--user-agent=Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36')
        
        driver = webdriver.Chrome(options=chrome_options)
        wait = WebDriverWait(driver, 20)
        
        driver.get('https://www.linkedin.com/login')
        time.sleep(2)
        
        email_field = wait.until(EC.presence_of_element_located((By.ID, 'username')))
        email_field.send_keys(data.linkedin_email)
        
        password_field = driver.find_element(By.ID, 'password')
        password_field.send_keys(data.linkedin_password)
        
        login_btn = driver.find_element(By.XPATH, '//button[@type="submit"]')
        login_btn.click()
        time.sleep(5)
        
        if 'feed' not in driver.current_url:
            driver.quit()
            return {"success": False, "message": "Login failed. Check credentials."}
        
        driver.get('https://www.linkedin.com/feed/')
        time.sleep(3)
        
        start_post = wait.until(EC.element_to_be_clickable((By.XPATH, '//button[contains(@aria-label, "Start a post")]')))
        start_post.click()
        time.sleep(2)
        
        text_area = wait.until(EC.presence_of_element_located((By.XPATH, '//div[@role="textbox"]')))
        text_area.click()
        time.sleep(1)
        
        for line in data.content.split('\n'):
            text_area.send_keys(line)
            text_area.send_keys(Keys.SHIFT + Keys.ENTER)
            time.sleep(0.2)
        
        time.sleep(2)
        post_btn = driver.find_element(By.XPATH, '//button[@type="submit" and contains(@class, "share-actions__primary-action")]')
        post_btn.click()
        time.sleep(3)
        
        driver.quit()
        
        return {"success": True, "message": "Posted to LinkedIn successfully"}
        
    except Exception as e:
        if 'driver' in locals():
            driver.quit()
        return {"success": False, "message": str(e)}

@app.post("/api/jobs/search")
async def search_jobs(data: JobSearchRequest):
    try:
        from bs4 import BeautifulSoup
        
        jobs = []
        
        for skill in data.skills[:5]:
            url = f"https://www.indeed.com/jobs?q={skill.replace(' ', '+')}&l={data.locations[0].replace(' ', '+')}&sort=date"
            headers = {'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36'}
            response = requests.get(url, headers=headers, timeout=10)
            
            if response.status_code == 200:
                soup = BeautifulSoup(response.text, 'html.parser')
                cards = soup.find_all('div', class_='job_seen_beacon')[:5]
                
                for card in cards:
                    title_tag = card.find('h2', class_='jobTitle')
                    company_tag = card.find('span', class_='companyName')
                    location_tag = card.find('div', class_='companyLocation')
                    link_tag = title_tag.find('a') if title_tag else None
                    
                    if title_tag and link_tag:
                        jobs.append({
                            'title': title_tag.get_text(strip=True),
                            'company': company_tag.get_text(strip=True) if company_tag else 'N/A',
                            'location': location_tag.get_text(strip=True) if location_tag else 'N/A',
                            'url': f"https://www.indeed.com{link_tag.get('href')}",
                            'skill': skill,
                            'match_score': 70,
                        })
        
        return {"jobs": jobs, "total": len(jobs)}
        
    except Exception as e:
        return {"jobs": [], "total": 0, "error": str(e)}

@app.post("/api/whatsapp/send")
async def send_whatsapp(data: WhatsAppRequest):
    try:
        url = f"https://api.callmebot.com/whatsapp.php?phone={data.phone}&text={requests.utils.quote(data.message)}&apikey="
        response = requests.get(url, timeout=10)
        
        if response.status_code == 200:
            return {"success": True, "message": "WhatsApp message sent"}
        else:
            return {"success": False, "message": f"WhatsApp API error: {response.status_code}"}
            
    except Exception as e:
        return {"success": False, "message": str(e)}

@app.post("/api/resume/parse")
async def parse_resume(data: ResumeParseRequest):
    try:
        import openai
        
        client = openai.OpenAI(
            base_url="https://openrouter.ai/api/v1",
            api_key=data.api_key
        )
        
        response = client.chat.completions.create(
            model="qwen/qwen-2.5-coder-32b-instruct",
            messages=[
                {"role": "system", "content": "Extract ALL skills from this resume text. Return ONLY a JSON array of strings."},
                {"role": "user", "content": data.resume_text[:3000]}
            ],
            max_tokens=300,
            temperature=0.1,
        )
        
        import json
        skills = json.loads(response.choices[0].message.content)
        return {"skills": skills if isinstance(skills, list) else []}
        
    except Exception as e:
        return {"skills": [], "error": str(e)}

@app.post("/api/ai/generate")
async def ai_generate(data: dict):
    try:
        import openai
        
        client = openai.OpenAI(
            base_url="https://openrouter.ai/api/v1",
            api_key=data.get('api_key', '')
        )
        
        response = client.chat.completions.create(
            model=data.get('model', 'qwen/qwen-2.5-coder-32b-instruct'),
            messages=[
                {"role": "system", "content": data.get('system', 'You are a LinkedIn content creator.')},
                {"role": "user", "content": data.get('prompt', '')}
            ],
            max_tokens=data.get('max_tokens', 400),
            temperature=data.get('temperature', 0.8),
        )
        
        return {"content": response.choices[0].message.content}
        
    except Exception as e:
        return {"content": "", "error": str(e)}

if __name__ == "__main__":
    import uvicorn
    port = int(os.getenv("PORT", 8000))
    uvicorn.run(app, host="0.0.0.0", port=port)
