from flask import Flask, request, jsonify, render_template
import os
import json
import time
import logging
import random
import requests as req
from datetime import datetime
from bs4 import BeautifulSoup

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

app = Flask(__name__, template_folder='templates')

@app.route('/')
def index():
    return render_template('index.html')

CONFIG_FILE = "data/config.json"
STATE_FILE = "data/state.json"

def get_config():
    if os.path.exists(CONFIG_FILE):
        with open(CONFIG_FILE, 'r') as f:
            return json.load(f)
    return {
        "linkedin_email": os.getenv("LINKEDIN_EMAIL", ""),
        "linkedin_password": os.getenv("LINKEDIN_PASSWORD", ""),
        "openrouter_api_key": os.getenv("OPENROUTER_API_KEY", ""),
        "whatsapp_phone": os.getenv("WHATSAPP_PHONE", ""),
        "skills": os.getenv("SKILLS", "Python,JavaScript").split(","),
        "locations": os.getenv("LOCATIONS", "Remote,India").split(","),
    }

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

@app.route("/")
def root():
    return jsonify({
        "name": "IPG Agent API",
        "status": "running",
        "version": "1.0.0",
        "endpoints": {
            "POST /api/config": "Save configuration",
            "GET /api/config": "Get configuration",
            "POST /api/linkedin/post": "Post to LinkedIn",
            "POST /api/certificate": "Post certificate",
            "POST /api/jobs/search": "Search jobs",
            "POST /api/whatsapp/send": "Send WhatsApp",
            "POST /api/resume/parse": "Parse resume",
            "POST /api/ai/generate": "Generate AI content",
            "GET /api/state": "Get agent state",
            "GET /health": "Health check",
        }
    })

@app.route("/health")
def health():
    return jsonify({"status": "healthy", "time": datetime.now().isoformat()})

@app.route("/api/config", methods=["POST"])
def save_config_endpoint():
    data = request.json
    save_config(data)
    state = get_state()
    state["skills"] = data.get("skills", [])
    save_state(state)
    return jsonify({"success": True, "message": "Configuration saved"})

@app.route("/api/config", methods=["GET"])
def get_config_endpoint():
    config = get_config()
    config.pop("linkedin_password", None)
    config.pop("openrouter_api_key", None)
    return jsonify(config)

@app.route("/api/linkedin/post", methods=["POST"])
def post_to_linkedin():
    try:
        from selenium import webdriver
        from selenium.webdriver.common.by import By
        from selenium.webdriver.support.ui import WebDriverWait
        from selenium.webdriver.support import expected_conditions as EC
        from selenium.webdriver.chrome.options import Options
        from selenium.webdriver.common.keys import Keys
        
        data = request.json
        config = get_config()
        email = data.get("linkedin_email") or config.get("linkedin_email", "")
        password = data.get("linkedin_password") or config.get("linkedin_password", "")
        content = data.get("content", "")
        
        if not email or not password:
            return jsonify({"success": False, "message": "LinkedIn credentials required"})
        
        chrome_options = Options()
        chrome_options.add_argument("--headless")
        chrome_options.add_argument("--no-sandbox")
        chrome_options.add_argument("--disable-dev-shm-usage")
        chrome_options.add_argument("--disable-blink-features=AutomationControlled")
        chrome_options.add_argument("--user-agent=Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36")
        
        driver = webdriver.Chrome(options=chrome_options)
        wait = WebDriverWait(driver, 20)
        
        driver.get("https://www.linkedin.com/login")
        time.sleep(2)
        
        email_field = wait.until(EC.presence_of_element_located((By.ID, "username")))
        email_field.send_keys(email)
        password_field = driver.find_element(By.ID, "password")
        password_field.send_keys(password)
        driver.find_element(By.XPATH, "//button[@type='submit']").click()
        time.sleep(5)
        
        if "feed" not in driver.current_url and "mynetwork" not in driver.current_url:
            driver.quit()
            return jsonify({"success": False, "message": "Login failed"})
        
        driver.get("https://www.linkedin.com/feed/")
        time.sleep(3)
        
        start_post = wait.until(EC.element_to_be_clickable((By.XPATH, "//button[contains(@aria-label, 'Start a post')]")))
        start_post.click()
        time.sleep(2)
        
        text_area = wait.until(EC.presence_of_element_located((By.XPATH, "//div[@role='textbox']")))
        text_area.click()
        time.sleep(1)
        
        for line in content.split("\n"):
            text_area.send_keys(line)
            text_area.send_keys(Keys.SHIFT + Keys.ENTER)
            time.sleep(0.2)
        
        time.sleep(2)
        driver.find_element(By.XPATH, "//button[@type='submit' and contains(@class, 'share-actions__primary-action')]").click()
        time.sleep(3)
        driver.quit()
        
        state = get_state()
        state["post_count"] = state.get("post_count", 0) + 1
        state["last_post"] = datetime.now().isoformat()
        save_state(state)
        
        return jsonify({"success": True, "message": "Posted to LinkedIn"})
        
    except Exception as e:
        if "driver" in locals():
            driver.quit()
        return jsonify({"success": False, "message": str(e)})

@app.route("/api/certificate", methods=["POST"])
def post_certificate():
    try:
        from selenium import webdriver
        from selenium.webdriver.common.by import By
        from selenium.webdriver.support.ui import WebDriverWait
        from selenium.webdriver.support import expected_conditions as EC
        from selenium.webdriver.chrome.options import Options
        from selenium.webdriver.common.keys import Keys
        
        data = request.json
        config = get_config()
        email = data.get("linkedin_email") or config.get("linkedin_email", "")
        password = data.get("linkedin_password") or config.get("linkedin_password", "")
        cert_name = data.get("cert_name", "Certificate")
        issuing_org = data.get("issuing_org", "Organization")
        skills = data.get("skills", [])
        
        if not email or not password:
            return jsonify({"success": False, "message": "LinkedIn credentials required"})
        
        api_key = config.get("openrouter_api_key", "")
        
        content = generate_cert_content(cert_name, issuing_org, skills, api_key)
        hashtags = generate_cert_hashtags(cert_name, skills, issuing_org)
        full_post = f"{content}\n\n{hashtags}"
        
        chrome_options = Options()
        chrome_options.add_argument("--headless")
        chrome_options.add_argument("--no-sandbox")
        chrome_options.add_argument("--disable-dev-shm-usage")
        chrome_options.add_argument("--disable-blink-features=AutomationControlled")
        chrome_options.add_argument("--user-agent=Mozilla/5.0")
        
        driver = webdriver.Chrome(options=chrome_options)
        wait = WebDriverWait(driver, 20)
        
        driver.get("https://www.linkedin.com/login")
        time.sleep(2)
        wait.until(EC.presence_of_element_located((By.ID, "username"))).send_keys(email)
        driver.find_element(By.ID, "password").send_keys(password)
        driver.find_element(By.XPATH, "//button[@type='submit']").click()
        time.sleep(5)
        
        if "feed" not in driver.current_url:
            driver.quit()
            return jsonify({"success": False, "message": "Login failed"})
        
        driver.get("https://www.linkedin.com/feed/")
        time.sleep(3)
        
        wait.until(EC.element_to_be_clickable((By.XPATH, "//button[contains(@aria-label, 'Start a post')]"))).click()
        time.sleep(2)
        
        text_area = wait.until(EC.presence_of_element_located((By.XPATH, "//div[@role='textbox']")))
        text_area.click()
        time.sleep(1)
        
        for line in full_post.split("\n"):
            text_area.send_keys(line)
            text_area.send_keys(Keys.SHIFT + Keys.ENTER)
            time.sleep(0.2)
        
        time.sleep(2)
        driver.find_element(By.XPATH, "//button[@type='submit' and contains(@class, 'share-actions__primary-action')]").click()
        time.sleep(3)
        driver.quit()
        
        state = get_state()
        state["cert_count"] = state.get("cert_count", 0) + 1
        if skills:
            existing = state.get("skills", [])
            for s in skills:
                if s not in existing:
                    existing.append(s)
            state["skills"] = existing
        state["last_certificate"] = datetime.now().isoformat()
        save_state(state)
        
        return jsonify({"success": True, "message": "Certificate posted", "content": full_post, "skills_updated": state.get("skills", [])})
        
    except Exception as e:
        if "driver" in locals():
            driver.quit()
        return jsonify({"success": False, "message": str(e)})

@app.route("/api/jobs/search", methods=["POST"])
def search_jobs():
    try:
        data = request.json
        skills = data.get("skills", [])
        locations = data.get("locations", ["Remote"])
        
        jobs = []
        for skill in skills[:5]:
            for location in locations[:2]:
                try:
                    url = f"https://www.indeed.com/jobs?q={skill.replace(' ', '+')}&l={location.replace(' ', '+')}&sort=date"
                    headers = {"User-Agent": "Mozilla/5.0"}
                    resp = req.get(url, headers=headers, timeout=10)
                    if resp.status_code == 200:
                        soup = BeautifulSoup(resp.text, "html.parser")
                        for card in soup.find_all("div", class_="job_seen_beacon")[:3]:
                            title_tag = card.find("h2", class_="jobTitle")
                            company_tag = card.find("span", class_="companyName")
                            location_tag = card.find("div", class_="companyLocation")
                            link_tag = title_tag.find("a") if title_tag else None
                            if title_tag and link_tag:
                                jobs.append({
                                    "title": title_tag.get_text(strip=True),
                                    "company": company_tag.get_text(strip=True) if company_tag else "N/A",
                                    "location": location_tag.get_text(strip=True) if location_tag else "N/A",
                                    "url": f"https://www.indeed.com{link_tag.get('href')}",
                                    "skill": skill,
                                    "match_score": 70,
                                })
                except:
                    pass
        
        return jsonify({"jobs": jobs[:15], "total": len(jobs)})
        
    except Exception as e:
        return jsonify({"jobs": [], "total": 0, "error": str(e)})

@app.route("/api/whatsapp/send", methods=["POST"])
def send_whatsapp():
    try:
        data = request.json
        phone = data.get("phone", "")
        message = data.get("message", "")
        if not phone:
            return jsonify({"success": False, "message": "Phone number required"})
        
        url = f"https://api.callmebot.com/whatsapp.php?phone={phone}&text={req.utils.quote(message)}&apikey="
        resp = req.get(url, timeout=10)
        return jsonify({"success": resp.status_code == 200})
    except Exception as e:
        return jsonify({"success": False, "message": str(e)})

@app.route("/api/resume/parse", methods=["POST"])
def parse_resume():
    try:
        data = request.json
        text = data.get("resume_text", "")
        
        common_skills = [
            "Python", "JavaScript", "TypeScript", "Java", "C++", "C#", "Go", "Ruby", "PHP",
            "React", "Angular", "Vue.js", "Node.js", "Express", "Django", "Flask",
            "SQL", "MySQL", "PostgreSQL", "MongoDB", "Redis",
            "AWS", "Azure", "GCP", "Docker", "Kubernetes", "Git",
            "HTML", "CSS", "Machine Learning", "Deep Learning", "TensorFlow", "PyTorch",
            "Data Analysis", "Data Science", "Pandas", "NumPy",
            "REST API", "GraphQL", "Microservices",
            "Linux", "Agile", "Scrum", "Testing",
            "React Native", "Flutter", "Android", "iOS",
        ]
        
        found = []
        text_upper = text.upper()
        for skill in common_skills:
            if skill.upper() in text_upper:
                found.append(skill)
        
        return jsonify({"skills": found, "total": len(found)})
        
    except Exception as e:
        return jsonify({"skills": [], "error": str(e)})

@app.route("/api/ai/generate", methods=["POST"])
def ai_generate():
    try:
        data = request.json
        api_key = data.get("api_key", "") or get_config().get("openrouter_api_key", "")
        
        resp = req.post(
            "https://openrouter.ai/api/v1/chat/completions",
            headers={"Authorization": f"Bearer {api_key}", "Content-Type": "application/json"},
            json={
                "model": data.get("model", "qwen/qwen-2.5-coder-32b-instruct"),
                "messages": [
                    {"role": "system", "content": data.get("system", "You are a LinkedIn content creator.")},
                    {"role": "user", "content": data.get("prompt", "")}
                ],
                "max_tokens": data.get("max_tokens", 400),
                "temperature": data.get("temperature", 0.8),
            },
            timeout=30
        )
        
        if resp.status_code == 200:
            return jsonify({"content": resp.json()["choices"][0]["message"]["content"]})
        return jsonify({"content": "", "error": f"API error: {resp.status_code}"})
        
    except Exception as e:
        return jsonify({"content": "", "error": str(e)})

@app.route("/api/state", methods=["GET"])
def get_state_endpoint():
    return jsonify(get_state())

@app.route("/api/auto-post", methods=["POST"])
def auto_post():
    config = get_config()
    state = get_state()
    skills = state.get("skills", config.get("skills", []))
    
    if not skills:
        return jsonify({"success": False, "message": "No skills configured"})
    
    post_types = ["tech_tip", "career_advice", "project_idea", "industry_insight", "learning_journey", "motivational"]
    post_type = random.choice(post_types)
    
    api_key = config.get("openrouter_api_key", "")
    content = generate_daily_post(skills, post_type, api_key)
    hashtags = generate_hashtags(post_type, skills)
    full_post = f"{content}\n\n{hashtags}"
    
    from selenium import webdriver
    from selenium.webdriver.common.by import By
    from selenium.webdriver.support.ui import WebDriverWait
    from selenium.webdriver.support import expected_conditions as EC
    from selenium.webdriver.chrome.options import Options
    from selenium.webdriver.common.keys import Keys
    
    email = config.get("linkedin_email", "")
    password = config.get("linkedin_password", "")
    
    if not email or not password:
        return jsonify({"success": False, "message": "LinkedIn credentials required"})
    
    try:
        chrome_options = Options()
        chrome_options.add_argument("--headless")
        chrome_options.add_argument("--no-sandbox")
        chrome_options.add_argument("--disable-dev-shm-usage")
        chrome_options.add_argument("--disable-blink-features=AutomationControlled")
        chrome_options.add_argument("--user-agent=Mozilla/5.0")
        
        driver = webdriver.Chrome(options=chrome_options)
        wait = WebDriverWait(driver, 20)
        
        driver.get("https://www.linkedin.com/login")
        time.sleep(2)
        wait.until(EC.presence_of_element_located((By.ID, "username"))).send_keys(email)
        driver.find_element(By.ID, "password").send_keys(password)
        driver.find_element(By.XPATH, "//button[@type='submit']").click()
        time.sleep(5)
        
        if "feed" not in driver.current_url:
            driver.quit()
            return jsonify({"success": False, "message": "Login failed"})
        
        driver.get("https://www.linkedin.com/feed/")
        time.sleep(3)
        wait.until(EC.element_to_be_clickable((By.XPATH, "//button[contains(@aria-label, 'Start a post')]"))).click()
        time.sleep(2)
        text_area = wait.until(EC.presence_of_element_located((By.XPATH, "//div[@role='textbox']")))
        text_area.click()
        time.sleep(1)
        for line in full_post.split("\n"):
            text_area.send_keys(line)
            text_area.send_keys(Keys.SHIFT + Keys.ENTER)
            time.sleep(0.2)
        time.sleep(2)
        driver.find_element(By.XPATH, "//button[@type='submit' and contains(@class, 'share-actions__primary-action')]").click()
        time.sleep(3)
        driver.quit()
        
        state["post_count"] = state.get("post_count", 0) + 1
        state["last_post"] = datetime.now().isoformat()
        save_state(state)
        
        return jsonify({"success": True, "message": "Auto-post successful", "post_type": post_type})
        
    except Exception as e:
        if "driver" in locals():
            driver.quit()
        return jsonify({"success": False, "message": str(e)})

def generate_daily_post(skills, post_type, api_key):
    prompts = {
        "tech_tip": f"Share a practical tech tip about: {', '.join(skills[:5])}.",
        "career_advice": f"Share career advice for developers with skills in: {', '.join(skills[:5])}.",
        "project_idea": f"Describe an impressive project using: {', '.join(skills[:5])}.",
        "industry_insight": f"Share an insight about tech industry related to: {', '.join(skills[:5])}.",
        "learning_journey": f"Share a learning journey about: {', '.join(skills[:5])}.",
        "motivational": "Write a motivational post about tech career growth.",
    }
    
    prompt = f"{prompts.get(post_type, prompts['tech_tip'])}\nProfessional LinkedIn post, under 200 words, 3-5 emojis, NO hashtags."
    
    if api_key:
        try:
            resp = req.post(
                "https://openrouter.ai/api/v1/chat/completions",
                headers={"Authorization": f"Bearer {api_key}", "Content-Type": "application/json"},
                json={"model": "qwen/qwen-2.5-coder-32b-instruct", "messages": [{"role": "user", "content": prompt}], "max_tokens": 400, "temperature": 0.8},
                timeout=30
            )
            if resp.status_code == 200:
                return resp.json()["choices"][0]["message"]["content"].strip()
        except:
            pass
    
    return f"Exciting developments in tech! I've been exploring {', '.join(skills[:3])} and learning continuously.\n\nWhat are you working on? Share below! "

def generate_hashtags(post_type, skills):
    tags = ["#LinkedIn", "#Professional", "#Growth", "#Learning", "#TechCommunity"]
    for s in skills[:3]:
        tags.append(f"#{s.replace(' ', '')}")
    return " ".join(tags[:12])

def generate_cert_content(cert_name, org, skills, api_key):
    skills_text = ", ".join(skills) if skills else "Professional Development"
    prompt = f"LinkedIn post for earning {cert_name} from {org}. Skills: {skills_text}. Professional, emojis, under 200 words, NO hashtags."
    
    if api_key:
        try:
            resp = req.post(
                "https://openrouter.ai/api/v1/chat/completions",
                headers={"Authorization": f"Bearer {api_key}", "Content-Type": "application/json"},
                json={"model": "qwen/qwen-2.5-coder-32b-instruct", "messages": [{"role": "user", "content": prompt}], "max_tokens": 400, "temperature": 0.8},
                timeout=30
            )
            if resp.status_code == 200:
                return resp.json()["choices"][0]["message"]["content"].strip()
        except:
            pass
    
    return f"Excited to share that I've earned {cert_name} from {org}!\n\nSkills: {skills_text}\n\nAlways learning and growing! "

def generate_cert_hashtags(cert_name, skills, org):
    tags = ["#Certification", "#ContinuousLearning", "#ProfessionalDevelopment", "#Achievement", "#CareerGrowth", "#Learning"]
    for s in skills[:3]:
        tags.append(f"#{s.replace(' ', '')}")
    if org:
        tags.append(f"#{org.replace(' ', '')}")
    return " ".join(tags[:15])

if __name__ == "__main__":
    port = int(os.getenv("PORT", 8000))
    app.run(host="0.0.0.0", port=port)
