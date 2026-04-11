from flask import Flask, request, jsonify, render_template, send_from_directory, session, redirect, url_for
import os
import json
import time
import logging
import random
import requests
from datetime import datetime
from bs4 import BeautifulSoup
from modules.linkedin import LinkedInBot
from modules.ai_content import AIContentGenerator
from modules.hashtag_engine import HashtagEngine
from modules.scheduler import TaskScheduler
from modules.resume_parser import ResumeParser
import threading
from sqlalchemy import create_engine, Column, String, Text, JSON
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import sessionmaker

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Database Setup (Persistent storage for Render)
DATABASE_URL = os.getenv("DATABASE_URL")
from sqlalchemy.orm import declarative_base
Base = declarative_base()

class ConfigStore(Base):
    __tablename__ = "config_store"
    key = Column(String(50), primary_key=True)
    value = Column(JSON)

if DATABASE_URL:
    try:
        if DATABASE_URL.startswith("postgres://"):
            DATABASE_URL = DATABASE_URL.replace("postgres://", "postgresql://", 1)
        engine = create_engine(DATABASE_URL)
        SessionLocal = sessionmaker(bind=engine)
        Base.metadata.create_all(engine)
        logger.info("Connected to persistent database.")
    except Exception as e:
        logger.error(f"DB Connection failed: {str(e)}")
        DATABASE_URL = None

app = Flask(__name__, template_folder='templates')
app.secret_key = os.getenv("SECRET_KEY", "ipg-agent-stable-key-007")
app.config['SESSION_PERMANENT'] = True
app.config['PERMANENT_SESSION_LIFETIME'] = 604800 # 7 days

@app.before_request
def check_auth():
    # Public routes
    public_paths = ['/login', '/api/login', '/manifest.json', '/sw.js']
    if request.path in public_paths or request.path.startswith('/static'):
        return None
    
    # Require login for everything else
    if not session.get('logged_in'):
        if request.path.startswith('/api'):
            return jsonify({"success": False, "message": "Unauthorized"}), 401
        return render_template('login.html')

@app.route('/api/login', methods=['POST'])
def api_login():
    data = request.json
    password = data.get('password')
    admin_pass = os.getenv("AGENT_PASSWORD", "admin123")
    if password == admin_pass:
        session['logged_in'] = True
        return jsonify({"success": True})
    return jsonify({"success": False, "message": "Invalid password"})

@app.route('/')
def index():
    return render_template('index.html')

CONFIG_FILE = "config.json"
STATE_FILE = "data/state.json"

# Global registry for pending login sessions
global_bots = {}

def get_config():
    if DATABASE_URL:
        db = SessionLocal()
        item = db.query(ConfigStore).filter(ConfigStore.key == "config").first()
        db.close()
        if item: return item.value

    if os.path.exists(CONFIG_FILE):
        with open(CONFIG_FILE, 'r') as f:
            return json.load(f)
    return {
        "linkedin_email": os.getenv("LINKEDIN_EMAIL", ""),
        "linkedin_password": os.getenv("LINKEDIN_PASSWORD", ""),
        "openrouter_api_key": os.getenv("GROQ_API_KEY") or os.getenv("OPENROUTER_API_KEY", ""),
        "ai_provider": os.getenv("AI_PROVIDER", "groq"),
        "whatsapp_phone": os.getenv("WHATSAPP_PHONE", ""),
        "skills": os.getenv("SKILLS", "Python,JavaScript").split(","),
        "locations": os.getenv("LOCATIONS", "Remote,India").split(","),
    }

def save_config(config):
    if DATABASE_URL:
        db = SessionLocal()
        item = db.query(ConfigStore).filter(ConfigStore.key == "config").first()
        if item:
            item.value = config
        else:
            db.add(ConfigStore(key="config", value=config))
        db.commit()
        db.close()
        return

    os.makedirs("data", exist_ok=True)
    with open(CONFIG_FILE, 'w') as f:
        json.dump(config, f, indent=2)

def get_state():
    if DATABASE_URL:
        db = SessionLocal()
        item = db.query(ConfigStore).filter(ConfigStore.key == "state").first()
        db.close()
        if item: return item.value

    if os.path.exists(STATE_FILE):
        with open(STATE_FILE, 'r') as f:
            return json.load(f)
    return {"post_count": 0, "cert_count": 0, "skills": [], "user_fullname": "LinkedIn User"}

def save_state(state):
    if DATABASE_URL:
        db = SessionLocal()
        item = db.query(ConfigStore).filter(ConfigStore.key == "state").first()
        if item:
            item.value = state
        else:
            db.add(ConfigStore(key="state", value=state))
        db.commit()
        db.close()
        return

    os.makedirs("data", exist_ok=True)
    with open(STATE_FILE, 'w') as f:
        json.dump(state, f, indent=2)


@app.route("/health")
def health():
    return jsonify({"status": "healthy", "time": datetime.now().isoformat()})

@app.route('/manifest.json')
def serve_manifest():
    return send_from_directory('templates', 'manifest.json')

@app.route('/sw.js')
def serve_sw():
    return send_from_directory('templates', 'sw.js')

@app.route("/api/config", methods=["POST"])
def save_config_endpoint():
    data = request.json
    config = get_config()
    
    # Trim API key if present
    if "openrouter_api_key" in data:
        data["openrouter_api_key"] = data["openrouter_api_key"].strip()
        
    config.update(data)
    save_config(config)
    state = get_state()
    state["skills"] = data.get("skills", state.get("skills", []))
    save_state(state)
    return jsonify({"success": True, "message": "Configuration saved"})

@app.route("/api/config", methods=["GET"])
def get_config_endpoint():
    config = get_config()
    config.pop("linkedin_password", None)
    config.pop("openrouter_api_key", None)
    return jsonify(config)
# Global status for tracking automation steps
agent_status = "Ready"

@app.route("/api/status")
def get_bot_status():
    global agent_status
    return jsonify({"status": agent_status})

@app.route("/api/linkedin/post", methods=["POST"])
def post_to_linkedin():
    global agent_status
    def set_status(msg):
        global agent_status
        agent_status = msg

    try:
        set_status("Initializing...")
        data = request.json
        config = get_config()
        email = data.get("linkedin_email") or config.get("linkedin_email", "")
        password = data.get("linkedin_password") or config.get("linkedin_password", "")
        content = data.get("content", "")
        
        if not email or not password:
            return jsonify({"success": False, "message": "LinkedIn credentials required"})
        
        bot = LinkedInBot(email, password)
        set_status("Setting up browser...")
        bot.setup_driver(headless=True)
        
        set_status("Authorizing on LinkedIn...")
        login_res = bot.login()
        if login_res != "SUCCESS" and login_res is not True:
            bot.close()
            set_status("Login Failed")
            return jsonify({"success": False, "message": "Login failed. Check Credentials."})
            
        success = bot.post_text(content, status_callback=set_status)
        bot.close()
        
        if success:
            state = get_state()
            state["post_count"] = state.get("post_count", 0) + 1
            state["last_post"] = datetime.now().isoformat()
            save_state(state)
            return jsonify({"success": True, "message": "Posted to LinkedIn"})
        else:
            return jsonify({"success": False, "message": "Failed to publish post"})
        
    except Exception as e:
        return jsonify({"success": False, "message": "Error: " + str(e)})

@app.route("/api/test/linkedin", methods=["POST"])
def api_test_linkedin():
    global global_bots
    try:
        config = get_config()
        email = config.get("linkedin_email")
        password = config.get("linkedin_password")
        
        # Log for debugging (remove in production if sensitive)
        logger.info(f"Direct post attempt with email: {email}")
        
        if not email or not password:
            return jsonify({"success": False, "message": "LinkedIn credentials missing. Please go to Settings and hit 'Sync Config' first."})
            
        # Clean up any old bot for this user to save memory
        if email in global_bots:
            try: global_bots[email].close()
            except: pass
            
        bot = LinkedInBot(email, password)
        bot.setup_driver(headless=True)
        login_status = bot.login()
        
        if login_status == "OTP_REQUIRED":
            global_bots[email] = bot
            return jsonify({"success": True, "status": "OTP_REQUIRED", "message": "LinkedIn sent a code to your Mail. Enter it below."})
            
        if login_status == "SUCCESS" or login_status is True:
            # Discovery process...
            name = "LinkedIn User"
            try:
                bot.driver.get("https://www.linkedin.com/in/me/")
                time.sleep(3)
                name_el = bot.driver.find_element(By.TAG_NAME, "h1")
                name = name_el.text.strip().split("\n")[0]
            except: pass
            
            bot.close()
            state = get_state()
            state["user_fullname"] = name
            save_state(state)
            return jsonify({"success": True, "status": "COMPLETED", "message": f"Successfully connected as {name}", "user": name})
        
        bot.close()
        return jsonify({"success": False, "message": "Credentials failed or System Busy. Try again."})
            
    except Exception as e:
        logger.error(f"Overall test error: {str(e)}")
        return jsonify({"success": False, "message": f"Connection Busy: {str(e)}"})

@app.route("/api/test/linkedin/otp", methods=["POST"])
def api_linkedin_otp():
    global global_bots
    try:
        data = request.json
        otp = data.get("otp")
        config = get_config()
        email = config.get("linkedin_email")
        
        if email not in global_bots:
            return jsonify({"success": False, "message": "Session expired or browser closed. Please try Connecting again."})
        
        # Pull the existing bot that is already waiting on the OTP screen
        bot = global_bots.pop(email)
        success = bot.login(otp_code=otp)
        
        if success:
            try:
                bot.driver.get("https://www.linkedin.com/in/me/")
                time.sleep(3)
                name_el = bot.driver.find_element(By.TAG_NAME, "h1")
                name = name_el.text.strip().split("\n")[0]
            except:
                name = "LinkedIn User"

            bot.close()
            state = get_state()
            state["user_fullname"] = name
            save_state(state)
            return jsonify({"success": True, "message": f"Welcome, {name}!", "user": name})
        
        bot.close()
        return jsonify({"success": False, "message": "OTP verification failed. Check your code."})
    except Exception as e:
        return jsonify({"success": False, "message": f"Error: {str(e)}"})

@app.route("/api/certificate", methods=["POST"])
def post_certificate():
    try:
        # Check if it is a multi-part form for file uploads or JSON
        if request.content_type and "multipart/form-data" in request.content_type:
             data = request.form
             files = request.files.getlist("images")
        else:
             data = request.json
             files = []
             
        config = get_config()
        email = config.get("linkedin_email", "")
        password = config.get("linkedin_password", "")
        
        cert_name = data.get("cert_name", "Professional Certification")
        issuing_org = data.get("issuing_org", "Professional Organization")
        skills = data.get("skills", "").split(",") if isinstance(data.get("skills"), str) else data.get("skills", [])
        
        if not email or not password:
            return jsonify({"success": False, "message": "LinkedIn credentials required"})
        
        api_key = config.get("groq_api_key") or config.get("openrouter_api_key", "")
        provider = config.get("ai_provider", "openrouter")
        ai = AIContentGenerator(api_key, provider)
        hashtags_engine = HashtagEngine()
        
        content = ai.generate_certificate_post(cert_name, issuing_org, skills)
        hashtags = hashtags_engine.get_certificate_hashtags(cert_name, skills, issuing_org)
        full_post = f"{content}\n\n{hashtags}"
        
        # Process uploaded images
        temp_paths = []
        if files:
            os.makedirs("data/uploads", exist_ok=True)
            for file in files:
                if file.filename:
                    path = os.path.join("data/uploads", file.filename)
                    file.save(path)
                    temp_paths.append(path)
        
        bot = LinkedInBot(email, password)
        # Use headless if running on Render or if requested
        bot.setup_driver(headless=True if os.getenv("RENDER") else False)
        
        if not bot.login():
            bot.close()
            return jsonify({"success": False, "message": "LinkedIn login failed"})
            
        if temp_paths:
            success = bot.post_with_images(full_post, temp_paths)
        else:
            success = bot.post_text(full_post)
            
        bot.close()
        
        # Cleanup
        for p in temp_paths:
            try: os.remove(p)
            except: pass
            
        if success:
            state = get_state()
            state["cert_count"] = state.get("cert_count", 0) + 1
            if skills:
                existing = state.get("skills", [])
                for s in skills:
                    if s not in existing: existing.append(s)
                state["skills"] = existing
            save_state(state)
            return jsonify({"success": True, "message": "Achievement posted successfully!"})
        else:
            return jsonify({"success": False, "message": "Failed to publish achievement to LinkedIn"})
            
    except Exception as e:
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

@app.route("/api/resume/upload", methods=["POST"])
def upload_resume():
    try:
        if 'resume' not in request.files:
            return jsonify({"success": False, "message": "No file part"})
        
        file = request.files['resume']
        if file.filename == '':
            return jsonify({"success": False, "message": "No selected file"})
        
        os.makedirs("data/resumes", exist_ok=True)
        path = os.path.join("data/resumes", file.filename)
        file.save(path)
        
        parser = ResumeParser()
        skills = parser.parse_file(path)
        
        if skills:
            state = get_state()
            existing = state.get("skills", [])
            state["skills"], added = parser.merge_skills(existing, skills)
            save_state(state)
            
            # Trigger a fresh job search with new skills
            threading.Thread(target=run_job_search_bg, args=(state["skills"],)).start()
            
            return jsonify({
                "success": True, 
                "skills": state["skills"], 
                "added": added,
                "message": f"Extracted {len(added)} new skills from resume!"
            })
        else:
            return jsonify({"success": False, "message": "No skills could be extracted from this resume."})
            
    except Exception as e:
        return jsonify({"success": False, "message": str(e)})

def run_job_search_bg(skills):
    # Simulated background search that might send WhatsApp later
    logger.info(f"Background job search triggered for skills: {skills}")

@app.route("/api/whatsapp/send", methods=["POST"])
def send_whatsapp():
    try:
        data = request.json
        phone = data.get("phone", "")
        message = data.get("message", "")
        if not phone:
            return jsonify({"success": False, "message": "Phone number required"})
        
        url = f"https://api.callmebot.com/whatsapp.php?phone={phone}&text={requests.utils.quote(message)}&apikey="
        resp = requests.get(url, timeout=10)
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
        config = get_config()
        api_key = data.get("api_key", "") or config.get("openrouter_api_key", "")
        provider = data.get("provider", "") or config.get("ai_provider", "openrouter")
        
        ai = AIContentGenerator(api_key, provider)
        prompt = data.get("prompt", "")
        
        # Enhanced custom generation
        content = ai.generate_custom_post(prompt)
        
        return jsonify({"content": content})
        
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

@app.route("/api/auto-post/preview", methods=["POST"])
def auto_post_preview():
    config = get_config()
    state = get_state()
    skills = state.get("skills", config.get("skills", []))
    
    if not skills:
        return jsonify({"success": False, "message": "No skills configured. Please add some first."})
        
    post_types = ["tech_tip", "career_advice", "project_idea", "industry_insight", "learning_journey", "motivational"]
    post_type = random.choice(post_types)
    
    api_key = config.get("openrouter_api_key", "")
    provider = config.get("ai_provider", "openrouter")
    ai = AIContentGenerator(api_key, provider)
    hashtags_engine = HashtagEngine()
    
    content = ai.generate_daily_post(skills, post_type)
    hashtags = hashtags_engine.get_hashtags(post_type, skills)
    full_post = f"{content}\n\n{hashtags}"
    
    return jsonify({"success": True, "content": full_post, "post_type": post_type})

    return f"Excited to share that I've earned {cert_name} from {org}!\n\nSkills: {skills_text}\n\nAlways learning and growing! "

def generate_cert_hashtags(cert_name, skills, org):
    tags = ["#Certification", "#ContinuousLearning", "#ProfessionalDevelopment", "#Achievement", "#CareerGrowth", "#Learning"]
    for s in skills[:3]:
        tags.append(f"#{s.replace(' ', '')}")
    if org:
        tags.append(f"#{org.replace(' ', '')}")
    return " ".join(tags[:15])

def run_scheduler_bg():
    from main import IPGAgent
    agent = IPGAgent()
    agent.setup_schedule()
    logger.info("Background scheduler started")
    while True:
        agent.scheduler.tick()
        time.sleep(60)

if __name__ == "__main__":
    # Start scheduler thread
    threading.Thread(target=run_scheduler_bg, daemon=True).start()
    
    port = int(os.getenv("PORT", 8000))
    app.run(host="0.0.0.0", port=port)
