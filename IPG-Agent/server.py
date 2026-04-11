from flask import Flask, request, jsonify, render_template, send_from_directory, session, redirect
import os
import json
import time
import logging
import random
import requests
from datetime import datetime
from modules.linkedin_api import LinkedInAPI
from modules.ai_content import AIContentGenerator
from modules.hashtag_engine import HashtagEngine
from modules.resume_parser import ResumeParser
import threading

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# ── Database Setup (Persistent storage for Render) ──
DATABASE_URL = os.getenv("DATABASE_URL")

try:
    from sqlalchemy import create_engine, Column, String, JSON
    from sqlalchemy.orm import declarative_base, sessionmaker as sa_sessionmaker

    Base = declarative_base()

    class ConfigStore(Base):
        __tablename__ = "config_store"
        key = Column(String(50), primary_key=True)
        value = Column(JSON)

    if DATABASE_URL:
        if DATABASE_URL.startswith("postgres://"):
            DATABASE_URL = DATABASE_URL.replace("postgres://", "postgresql://", 1)
        engine = create_engine(DATABASE_URL)
        SessionLocal = sa_sessionmaker(bind=engine)
        Base.metadata.create_all(engine)
        logger.info("Connected to persistent database.")
    else:
        DATABASE_URL = None
except Exception as e:
    logger.error(f"DB setup skipped: {str(e)}")
    DATABASE_URL = None

# ── Flask App ──
app = Flask(__name__, template_folder='templates')
app.secret_key = os.getenv("SECRET_KEY", "ipg-agent-stable-key-007")
app.config['SESSION_PERMANENT'] = True
app.config['PERMANENT_SESSION_LIFETIME'] = 604800  # 7 days

CONFIG_FILE = "config.json"
STATE_FILE = "data/state.json"

# ── Helper Functions ──
def get_config():
    if DATABASE_URL:
        db = SessionLocal()
        item = db.query(ConfigStore).filter(ConfigStore.key == "config").first()
        db.close()
        if item:
            return item.value

    if os.path.exists(CONFIG_FILE):
        with open(CONFIG_FILE, 'r') as f:
            return json.load(f)
    return {
        "linkedin_client_id": os.getenv("LINKEDIN_CLIENT_ID", "86bc4xt6m1p06h"),
        "linkedin_client_secret": os.getenv("LINKEDIN_CLIENT_SECRET", ""),
        "linkedin_access_token": os.getenv("LINKEDIN_ACCESS_TOKEN", ""),
        "linkedin_person_id": os.getenv("LINKEDIN_PERSON_ID", ""),
        "linkedin_user_name": "",
        "groq_api_key": os.getenv("GROQ_API_KEY", ""),
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
        if item:
            return item.value
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

def get_linkedin_api():
    """Create a LinkedInAPI instance with stored credentials."""
    config = get_config()
    base_url = os.getenv("RENDER_EXTERNAL_URL", request.host_url.rstrip("/"))
    redirect_uri = f"{base_url}/api/linkedin/callback"

    api = LinkedInAPI(
        client_id=config.get("linkedin_client_id", ""),
        client_secret=config.get("linkedin_client_secret", ""),
        redirect_uri=redirect_uri
    )

    # Load stored token
    token = config.get("linkedin_access_token", "")
    person_id = config.get("linkedin_person_id", "")
    user_name = config.get("linkedin_user_name", "")
    if token and person_id:
        api.set_token(token, person_id, user_name)
    return api

# ── Auth Middleware ──
@app.before_request
def check_auth():
    public_paths = ['/login', '/api/login', '/manifest.json', '/sw.js',
                    '/api/linkedin/callback', '/health']
    if request.path in public_paths or request.path.startswith('/static'):
        return None
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
        session.permanent = True
        return jsonify({"success": True})
    return jsonify({"success": False, "message": "Invalid password"})

# ── Pages ──
@app.route('/')
def index():
    return render_template('index.html')

@app.route("/health")
def health():
    return jsonify({"status": "healthy", "time": datetime.now().isoformat()})

@app.route('/manifest.json')
def serve_manifest():
    return send_from_directory('templates', 'manifest.json')

@app.route('/sw.js')
def serve_sw():
    return send_from_directory('templates', 'sw.js')

# ── Config Endpoints ──
@app.route("/api/config", methods=["POST"])
def save_config_endpoint():
    data = request.json
    config = get_config()
    config.update(data)
    save_config(config)
    state = get_state()
    state["skills"] = data.get("skills", state.get("skills", []))
    save_state(state)
    return jsonify({"success": True, "message": "Configuration saved"})

@app.route("/api/config", methods=["GET"])
def get_config_endpoint():
    config = get_config()
    # Hide secrets
    safe = {k: v for k, v in config.items()
            if k not in ["linkedin_client_secret", "groq_api_key", "linkedin_access_token"]}
    safe["has_token"] = bool(config.get("linkedin_access_token"))
    safe["has_groq_key"] = bool(config.get("groq_api_key"))
    return jsonify(safe)

@app.route("/api/state", methods=["GET"])
def get_state_endpoint():
    return jsonify(get_state())

# ── LinkedIn OAuth Flow ──
@app.route("/api/linkedin/auth")
def linkedin_auth():
    """Start the LinkedIn OAuth flow — redirects user to LinkedIn."""
    config = get_config()
    client_id = config.get("linkedin_client_id", "")
    client_secret = config.get("linkedin_client_secret", "")

    if not client_id or not client_secret:
        return jsonify({"success": False, "message": "Set Client ID & Secret in Settings first."})

    api = get_linkedin_api()
    auth_url = api.get_auth_url()
    return redirect(auth_url)

@app.route("/api/linkedin/callback")
def linkedin_callback():
    """Handle the OAuth callback from LinkedIn."""
    code = request.args.get("code")
    error = request.args.get("error")

    if error:
        return f"<h2>LinkedIn denied access: {error}</h2><a href='/'>Go back</a>"

    if not code:
        return "<h2>No authorization code received.</h2><a href='/'>Go back</a>"

    api = get_linkedin_api()
    success = api.exchange_code_for_token(code)

    if success:
        # Save token permanently
        config = get_config()
        config["linkedin_access_token"] = api.access_token
        config["linkedin_person_id"] = api.person_id
        config["linkedin_user_name"] = api.user_name or "LinkedIn User"
        save_config(config)

        state = get_state()
        state["user_fullname"] = api.user_name or "LinkedIn User"
        save_state(state)

        return redirect("/")
    else:
        return "<h2>Token exchange failed. Please try again.</h2><a href='/'>Go back</a>"

@app.route("/api/linkedin/status")
def linkedin_status():
    """Check if LinkedIn is connected."""
    config = get_config()
    token = config.get("linkedin_access_token", "")
    name = config.get("linkedin_user_name", "")

    if token:
        api = get_linkedin_api()
        valid = api.verify_token()
        return jsonify({
            "connected": valid,
            "user": name if valid else "",
            "message": "Connected" if valid else "Token expired. Reconnect."
        })
    return jsonify({"connected": False, "user": "", "message": "Not connected"})

# ── Post to LinkedIn (API — No Browser!) ──
@app.route("/api/linkedin/post", methods=["POST"])
def post_to_linkedin():
    try:
        data = request.json
        content = data.get("content", "")

        if not content:
            return jsonify({"success": False, "message": "Content is empty."})

        api = get_linkedin_api()
        if not api.is_authenticated():
            return jsonify({"success": False, "message": "LinkedIn not connected. Go to Settings and click 'Connect LinkedIn'."})

        success, message = api.post_text(content)

        if success:
            state = get_state()
            state["post_count"] = state.get("post_count", 0) + 1
            state["last_post"] = datetime.now().isoformat()
            save_state(state)
            return jsonify({"success": True, "message": "🎉 Posted to LinkedIn!"})
        else:
            return jsonify({"success": False, "message": message})

    except Exception as e:
        return jsonify({"success": False, "message": f"Error: {str(e)}"})

# ── AI Content Generation ──
@app.route("/api/ai/generate", methods=["POST"])
def ai_generate():
    try:
        data = request.json
        config = get_config()
        api_key = data.get("api_key", "") or config.get("groq_api_key", "")

        if not api_key:
            return jsonify({"content": "", "error": "Groq API Key missing. Add it in Settings."})

        ai = AIContentGenerator(api_key)
        prompt = data.get("prompt", "")
        content = ai.generate_custom_post(prompt)
        return jsonify({"content": content})

    except Exception as e:
        return jsonify({"content": "", "error": str(e)})

# ── Certificate Posting ──
@app.route("/api/certificate", methods=["POST"])
def post_certificate():
    try:
        if request.content_type and "multipart/form-data" in request.content_type:
            data = request.form
        else:
            data = request.json

        config = get_config()
        cert_name = data.get("cert_name", "Professional Certification")
        issuing_org = data.get("issuing_org", "Professional Organization")
        skills = data.get("skills", "").split(",") if isinstance(data.get("skills"), str) else data.get("skills", [])

        api_key = config.get("groq_api_key", "")
        if not api_key:
            return jsonify({"success": False, "message": "Groq API Key missing."})

        ai = AIContentGenerator(api_key)
        hashtags_engine = HashtagEngine()

        content = ai.generate_certificate_post(cert_name, issuing_org, skills)
        hashtags = hashtags_engine.get_certificate_hashtags(cert_name, skills, issuing_org)
        full_post = f"{content}\n\n{hashtags}"

        api = get_linkedin_api()
        if not api.is_authenticated():
            return jsonify({"success": False, "message": "LinkedIn not connected."})

        success, message = api.post_text(full_post)

        if success:
            state = get_state()
            state["cert_count"] = state.get("cert_count", 0) + 1
            existing = state.get("skills", [])
            for s in skills:
                if s and s not in existing:
                    existing.append(s)
            state["skills"] = existing
            save_state(state)
            return jsonify({"success": True, "message": "🎓 Achievement posted!"})
        else:
            return jsonify({"success": False, "message": message})

    except Exception as e:
        return jsonify({"success": False, "message": str(e)})

# ── Job Search (Web Scraping — no browser needed) ──
@app.route("/api/jobs/search", methods=["POST"])
def search_jobs():
    try:
        data = request.json
        skills = data.get("skills", [])
        locations = data.get("locations", ["Remote"])
        jobs = []

        from bs4 import BeautifulSoup
        for skill in skills[:5]:
            for location in locations[:2]:
                try:
                    url = f"https://www.indeed.com/jobs?q={skill.replace(' ', '+')}&l={location.replace(' ', '+')}&sort=date"
                    headers = {"User-Agent": "Mozilla/5.0"}
                    resp = requests.get(url, headers=headers, timeout=10)
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

# ── Resume Upload ──
@app.route("/api/resume/upload", methods=["POST"])
def upload_resume():
    try:
        if 'resume' not in request.files:
            return jsonify({"success": False, "message": "No file"})

        file = request.files['resume']
        if not file.filename:
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
            return jsonify({
                "success": True,
                "skills": state["skills"],
                "added": added,
                "message": f"Extracted {len(added)} new skills!"
            })
        else:
            return jsonify({"success": False, "message": "No skills could be extracted."})
    except Exception as e:
        return jsonify({"success": False, "message": str(e)})

# ── Auto Post Preview ──
@app.route("/api/auto-post/preview", methods=["POST"])
def auto_post_preview():
    config = get_config()
    state = get_state()
    skills = state.get("skills", config.get("skills", []))

    if not skills:
        return jsonify({"success": False, "message": "No skills configured."})

    post_types = ["tech_tip", "career_advice", "project_idea",
                  "industry_insight", "learning_journey", "motivational"]
    post_type = random.choice(post_types)

    api_key = config.get("groq_api_key", "")
    if not api_key:
        return jsonify({"success": False, "message": "Groq API Key missing."})

    ai = AIContentGenerator(api_key)
    hashtags_engine = HashtagEngine()

    content = ai.generate_daily_post(skills, post_type)
    hashtags = hashtags_engine.get_hashtags(post_type, skills)
    full_post = f"{content}\n\n{hashtags}"

    return jsonify({"success": True, "content": full_post, "post_type": post_type})

# ── WhatsApp ──
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

if __name__ == "__main__":
    port = int(os.getenv("PORT", 8000))
    app.run(host="0.0.0.0", port=port)
