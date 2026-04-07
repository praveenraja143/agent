from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
from typing import Optional
import os
import json
import time
import logging
import random
from datetime import datetime

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

app = FastAPI(title="IPG Agent API")

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

class PostRequest(BaseModel):
    content: str
    linkedin_email: Optional[str] = None
    linkedin_password: Optional[str] = None

class CertificateRequest(BaseModel):
    cert_name: str
    issuing_org: str
    skills: list[str] = []
    linkedin_email: Optional[str] = None
    linkedin_password: Optional[str] = None

class JobSearchRequest(BaseModel):
    skills: list[str]
    locations: list[str] = ["Remote"]

class WhatsAppRequest(BaseModel):
    phone: str
    message: str

class ResumeParseRequest(BaseModel):
    resume_text: str
    api_key: Optional[str] = None

class ConfigRequest(BaseModel):
    linkedin_email: str
    linkedin_password: str
    openrouter_api_key: str
    whatsapp_phone: str = ""
    skills: list[str] = []
    locations: list[str] = []

CONFIG_FILE = "data/config.json"
STATE_FILE = "data/state.json"

def get_config():
    if os.path.exists(CONFIG_FILE):
        with open(CONFIG_FILE, 'r') as f:
            return json.load(f)
    return {}

def save_config(config):
    os.makedirs("data", exist_ok=True)
    with open(CONFIG_FILE, 'w') as f:
        json.dump(config, f, indent=2)

def get_state():
    if os.path.exists(STATE_FILE):
        with open(STATE_FILE, 'r') as f:
            return json.load(f)
    return {"post_count": 0, "cert_count": 0, "skills": []}

def save_state(state):
    os.makedirs("data", exist_ok=True)
    with open(STATE_FILE, 'w') as f:
        json.dump(state, f, indent=2)

@app.get("/")
async def root():
    return {
        "name": "IPG Agent API",
        "status": "running",
        "version": "1.0.0",
        "endpoints": [
            "POST /api/config - Save configuration",
            "GET /api/config - Get configuration",
            "POST /api/linkedin/post - Post to LinkedIn",
            "POST /api/certificate - Post certificate",
            "POST /api/jobs/search - Search jobs",
            "POST /api/whatsapp/send - Send WhatsApp message",
            "POST /api/resume/parse - Parse resume",
            "POST /api/ai/generate - Generate AI content",
            "GET /api/state - Get agent state",
            "GET /health - Health check",
        ]
    }

@app.get("/health")
async def health():
    return {"status": "healthy", "time": datetime.now().isoformat()}

@app.post("/api/config")
async def save_config_endpoint(config: ConfigRequest):
    data = {
        "linkedin_email": config.linkedin_email,
        "linkedin_password": config.linkedin_password,
        "openrouter_api_key": config.openrouter_api_key,
        "whatsapp_phone": config.whatsapp_phone,
        "skills": config.skills,
        "locations": config.locations,
    }
    save_config(data)
    
    state = get_state()
    state["skills"] = config.skills
    save_state(state)
    
    return {"success": True, "message": "Configuration saved"}

@app.get("/api/config")
async def get_config_endpoint():
    config = get_config()
    config.pop("linkedin_password", None)
    config.pop("openrouter_api_key", None)
    return config

@app.post("/api/linkedin/post")
async def post_to_linkedin(data: PostRequest):
    try:
        from selenium import webdriver
        from selenium.webdriver.common.by import By
        from selenium.webdriver.support.ui import WebDriverWait
        from selenium.webdriver.support import expected_conditions as EC
        from selenium.webdriver.chrome.options import Options
        from selenium.webdriver.common.keys import Keys
        
        config = get_config()
        email = data.linkedin_email or config.get("linkedin_email", os.getenv("LINKEDIN_EMAIL", ""))
        password = data.linkedin_password or config.get("linkedin_password", os.getenv("LINKEDIN_PASSWORD", ""))
        
        if not email or not password:
            return {"success": False, "message": "LinkedIn credentials required"}
        
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
        email_field.send_keys(email)
        
        password_field = driver.find_element(By.ID, 'password')
        password_field.send_keys(password)
        
        login_btn = driver.find_element(By.XPATH, '//button[@type="submit"]')
        login_btn.click()
        time.sleep(5)
        
        if 'feed' not in driver.current_url and 'mynetwork' not in driver.current_url:
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
        
        state = get_state()
        state["post_count"] = state.get("post_count", 0) + 1
        state["last_post"] = datetime.now().isoformat()
        save_state(state)
        
        return {"success": True, "message": "Posted to LinkedIn successfully"}
        
    except Exception as e:
        if 'driver' in locals():
            driver.quit()
        return {"success": False, "message": str(e)}

@app.post("/api/certificate")
async def post_certificate(data: CertificateRequest):
    try:
        from selenium import webdriver
        from selenium.webdriver.common.by import By
        from selenium.webdriver.support.ui import WebDriverWait
        from selenium.webdriver.support import expected_conditions as EC
        from selenium.webdriver.chrome.options import Options
        from selenium.webdriver.common.keys import Keys
        
        config = get_config()
        email = data.linkedin_email or config.get("linkedin_email", os.getenv("LINKEDIN_EMAIL", ""))
        password = data.linkedin_password or config.get("linkedin_password", os.getenv("LINKEDIN_PASSWORD", ""))
        
        if not email or not password:
            return {"success": False, "message": "LinkedIn credentials required"}
        
        api_key = config.get("openrouter_api_key", os.getenv("OPENROUTER_API_KEY", ""))
        
        content = generate_cert_content(data.cert_name, data.issuing_org, data.skills, api_key)
        hashtags = generate_cert_hashtags(data.cert_name, data.skills, data.issuing_org)
        full_post = f"{content}\n\n{hashtags}"
        
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
        email_field.send_keys(email)
        
        password_field = driver.find_element(By.ID, 'password')
        password_field.send_keys(password)
        
        login_btn = driver.find_element(By.XPATH, '//button[@type="submit"]')
        login_btn.click()
        time.sleep(5)
        
        if 'feed' not in driver.current_url:
            driver.quit()
            return {"success": False, "message": "Login failed"}
        
        driver.get('https://www.linkedin.com/feed/')
        time.sleep(3)
        
        start_post = wait.until(EC.element_to_be_clickable((By.XPATH, '//button[contains(@aria-label, "Start a post")]')))
        start_post.click()
        time.sleep(2)
        
        text_area = wait.until(EC.presence_of_element_located((By.XPATH, '//div[@role="textbox"]')))
        text_area.click()
        time.sleep(1)
        
        for line in full_post.split('\n'):
            text_area.send_keys(line)
            text_area.send_keys(Keys.SHIFT + Keys.ENTER)
            time.sleep(0.2)
        
        time.sleep(2)
        post_btn = driver.find_element(By.XPATH, '//button[@type="submit" and contains(@class, "share-actions__primary-action")]')
        post_btn.click()
        time.sleep(3)
        
        driver.quit()
        
        state = get_state()
        state["cert_count"] = state.get("cert_count", 0) + 1
        
        if data.skills:
            existing = state.get("skills", [])
            for skill in data.skills:
                if skill not in existing:
                    existing.append(skill)
            state["skills"] = existing
            state["new_skills_added"] = data.skills
        
        state["last_certificate"] = datetime.now().isoformat()
        save_state(state)
        
        return {
            "success": True,
            "message": "Certificate posted to LinkedIn",
            "content": full_post,
            "skills_updated": state.get("skills", [])
        }
        
    except Exception as e:
        if 'driver' in locals():
            driver.quit()
        return {"success": False, "message": str(e)}

@app.post("/api/jobs/search")
async def search_jobs(data: JobSearchRequest):
    try:
        import requests as req
        from bs4 import BeautifulSoup
        
        jobs = []
        
        for skill in data.skills[:5]:
            for location in data.locations[:2]:
                try:
                    url = f"https://www.indeed.com/jobs?q={skill.replace(' ', '+')}&l={location.replace(' ', '+')}&sort=date"
                    headers = {'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36'}
                    resp = req.get(url, headers=headers, timeout=10)
                    
                    if resp.status_code == 200:
                        soup = BeautifulSoup(resp.text, 'html.parser')
                        cards = soup.find_all('div', class_='job_seen_beacon')[:3]
                        
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
                except:
                    pass
        
        return {"jobs": jobs[:15], "total": len(jobs)}
        
    except Exception as e:
        return {"jobs": [], "total": 0, "error": str(e)}

@app.post("/api/whatsapp/send")
async def send_whatsapp(data: WhatsAppRequest):
    try:
        import requests as req
        url = f"https://api.callmebot.com/whatsapp.php?phone={data.phone}&text={req.utils.quote(data.message)}&apikey="
        resp = req.get(url, timeout=10)
        return {"success": resp.status_code == 200, "message": "WhatsApp sent" if resp.status_code == 200 else "Failed"}
    except Exception as e:
        return {"success": False, "message": str(e)}

@app.post("/api/resume/parse")
async def parse_resume(data: ResumeParseRequest):
    try:
        common_skills = [
            'Python', 'JavaScript', 'TypeScript', 'Java', 'C++', 'C#', 'Go', 'Ruby', 'PHP',
            'React', 'Angular', 'Vue.js', 'Node.js', 'Express', 'Django', 'Flask',
            'SQL', 'MySQL', 'PostgreSQL', 'MongoDB', 'Redis',
            'AWS', 'Azure', 'GCP', 'Docker', 'Kubernetes', 'Git',
            'HTML', 'CSS', 'Machine Learning', 'Deep Learning', 'TensorFlow', 'PyTorch',
            'Data Analysis', 'Data Science', 'Pandas', 'NumPy',
            'REST API', 'GraphQL', 'Microservices',
            'Linux', 'Agile', 'Scrum', 'Testing',
            'React Native', 'Flutter', 'Android', 'iOS',
        ]
        
        found = []
        text_upper = data.resume_text.upper()
        for skill in common_skills:
            if skill.upper() in text_upper:
                found.append(skill)
        
        return {"skills": found, "total": len(found)}
        
    except Exception as e:
        return {"skills": [], "error": str(e)}

@app.post("/api/ai/generate")
async def ai_generate(data: dict):
    try:
        import requests as req
        
        api_key = data.get('api_key', '') or get_config().get('openrouter_api_key', '')
        
        resp = req.post(
            'https://openrouter.ai/api/v1/chat/completions',
            headers={
                'Authorization': f'Bearer {api_key}',
                'Content-Type': 'application/json',
            },
            json={
                'model': data.get('model', 'qwen/qwen-2.5-coder-32b-instruct'),
                'messages': [
                    {'role': 'system', 'content': data.get('system', 'You are a LinkedIn content creator.')},
                    {'role': 'user', 'content': data.get('prompt', '')}
                ],
                'max_tokens': data.get('max_tokens', 400),
                'temperature': data.get('temperature', 0.8),
            },
            timeout=30
        )
        
        if resp.status_code == 200:
            result = resp.json()
            return {"content": result['choices'][0]['message']['content']}
        else:
            return {"content": "", "error": f"API error: {resp.status_code}"}
            
    except Exception as e:
        return {"content": "", "error": str(e)}

@app.get("/api/state")
async def get_state_endpoint():
    return get_state()

@app.post("/api/auto-post")
async def auto_post():
    config = get_config()
    state = get_state()
    skills = state.get("skills", config.get("skills", []))
    
    if not skills:
        return {"success": False, "message": "No skills configured"}
    
    post_types = ['tech_tip', 'career_advice', 'project_idea', 'industry_insight', 'learning_journey', 'motivational']
    post_type = random.choice(post_types)
    
    content = generate_daily_post(skills, post_type, config.get('openrouter_api_key', ''))
    hashtags = generate_hashtags(post_type, skills)
    full_post = f"{content}\n\n{hashtags}"
    
    result = await post_to_linkedin(PostRequest(content=full_post))
    
    if result.get("success"):
        return {"success": True, "message": "Auto-post successful", "post_type": post_type}
    return result

def generate_daily_post(skills, post_type, api_key):
    prompts = {
        "tech_tip": f"Share a practical tech tip about: {', '.join(skills[:5])}. Make it actionable.",
        "career_advice": f"Share career advice for developers with skills in: {', '.join(skills[:5])}.",
        "project_idea": f"Describe an impressive project using: {', '.join(skills[:5])}.",
        "industry_insight": f"Share an insight about tech industry related to: {', '.join(skills[:5])}.",
        "learning_journey": f"Share a learning journey about: {', '.join(skills[:5])}.",
        "motivational": f"Write a motivational post about tech career growth.",
    }
    
    prompt = prompts.get(post_type, prompts["tech_tip"])
    
    if api_key:
        try:
            import requests as req
            resp = req.post(
                'https://openrouter.ai/api/v1/chat/completions',
                headers={'Authorization': f'Bearer {api_key}', 'Content-Type': 'application/json'},
                json={
                    'model': 'qwen/qwen-2.5-coder-32b-instruct',
                    'messages': [{'role': 'user', 'content': f"{prompt}\nProfessional LinkedIn post, under 200 words, 3-5 emojis, NO hashtags."}],
                    'max_tokens': 400, 'temperature': 0.8,
                },
                timeout=30
            )
            if resp.status_code == 200:
                return resp.json()['choices'][0]['message']['content'].strip()
        except:
            pass
    
    return f"Exciting developments in tech! I've been exploring {', '.join(skills[:3])} and learning continuously.\n\nWhat are you working on? Share below! "

def generate_hashtags(post_type, skills):
    tags = ['#LinkedIn', '#Professional', '#Growth', '#Learning', '#TechCommunity']
    if skills:
        for s in skills[:3]:
            tags.append(f'#{s.replace(" ", "")}')
    return ' '.join(tags[:12])

def generate_cert_content(cert_name, org, skills, api_key):
    skills_text = ', '.join(skills) if skills else 'Professional Development'
    
    if api_key:
        try:
            import requests as req
            resp = req.post(
                'https://openrouter.ai/api/v1/chat/completions',
                headers={'Authorization': f'Bearer {api_key}', 'Content-Type': 'application/json'},
                json={
                    'model': 'qwen/qwen-2.5-coder-32b-instruct',
                    'messages': [{'role': 'user', 'content': f"LinkedIn post for earning {cert_name} from {org}. Skills: {skills_text}. Professional, emojis, under 200 words, NO hashtags."}],
                    'max_tokens': 400, 'temperature': 0.8,
                },
                timeout=30
            )
            if resp.status_code == 200:
                return resp.json()['choices'][0]['message']['content'].strip()
        except:
            pass
    
    return f"Excited to share that I've earned {cert_name} from {org}!\n\nSkills: {skills_text}\n\nAlways learning and growing! "

def generate_cert_hashtags(cert_name, skills, org):
    tags = ['#Certification', '#ContinuousLearning', '#ProfessionalDevelopment', '#Achievement', '#CareerGrowth', '#Learning']
    if skills:
        for s in skills[:3]:
            tags.append(f'#{s.replace(" ", "")}')
    if org:
        tags.append(f'#{org.replace(" ", "")}')
    return ' '.join(tags[:15])

if __name__ == "__main__":
    import uvicorn
    port = int(os.getenv("PORT", 8000))
    uvicorn.run(app, host="0.0.0.0", port=port)
