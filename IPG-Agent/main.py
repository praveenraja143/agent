import os
import sys
import json
import time
import logging
import argparse
import random
from datetime import datetime

from modules.linkedin import LinkedInBot
from modules.ai_content import AIContentGenerator
from modules.hashtag_engine import HashtagEngine
from modules.job_searcher import JobSearcher
from modules.whatsapp import WhatsAppNotifier
from modules.resume_parser import ResumeParser
from modules.scheduler import TaskScheduler

logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler('data/agent.log'),
        logging.StreamHandler()
    ]
)
logger = logging.getLogger(__name__)

class IPGAgent:
    def __init__(self, config_path='config.json', headless=True):
        self.config_path = config_path
        self.config = self._load_config(config_path)
        self.headless = headless
        self.linkedin = LinkedInBot(
            email=self.config['linkedin_email'],
            password=self.config['linkedin_password']
        )
        self.ai = AIContentGenerator(
            api_key=self.config['openrouter_api_key'],
            provider=self.config.get('ai_provider', 'openrouter')
        )
        self.hashtags = HashtagEngine()
        self.jobs = JobSearcher(
            skills=self.config['skills'],
            locations=self.config.get('locations', ['Remote', 'India'])
        )
        self.whatsapp = WhatsAppNotifier(phone_number=self.config.get('whatsapp_phone', ''))
        self.resume_parser = ResumeParser()
        self.scheduler = TaskScheduler()
        self.skills = list(self.config['skills'])
        self.post_count = 0
        self.cert_count = 0

    def _load_config(self, path):
        if os.path.exists(path):
            with open(path, 'r') as f:
                return json.load(f)
        logger.error(f"Config file not found: {path}")
        sys.exit(1)

    def _save_state(self):
        state = {
            'skills': self.skills,
            'post_count': self.post_count,
            'cert_count': self.cert_count,
            'last_run': datetime.now().isoformat(),
        }
        os.makedirs('data', exist_ok=True)
        with open('data/state.json', 'w') as f:
            json.dump(state, f, indent=2)

    def _load_state(self):
        if os.path.exists('data/state.json'):
            with open('data/state.json', 'r') as f:
                state = json.load(f)
                self.skills = state.get('skills', self.skills)
                self.post_count = state.get('post_count', 0)
                self.cert_count = state.get('cert_count', 0)

    def daily_post(self):
        logger.info("=" * 50)
        logger.info("Starting daily auto-post...")
        
        post_types = ['tech_tip', 'career_advice', 'project_idea', 'industry_insight', 'learning_journey', 'motivational']
        post_type = random.choice(post_types)
        
        logger.info(f"Post type: {post_type}")
        content = self.ai.generate_daily_post(self.skills, post_type)
        
        hashtags = self.hashtags.get_hashtags(post_type, self.skills)
        full_post = f"{content}\n\n{hashtags}"
        
        logger.info(f"Generated post ({len(full_post)} chars)")
        
        try:
            if not self.linkedin.driver:
                self.linkedin.setup_driver(headless=self.headless)
            
            if not self.linkedin.login():
                logger.error("LinkedIn login failed for daily post")
                return

            success = self.linkedin.post_text(full_post)
            
            if success:
                self.post_count += 1
                self._save_state()
                logger.info(f"Daily post #{self.post_count} published!")
                self.whatsapp.send_post_confirmation('daily')
            else:
                logger.error("Daily post failed")
                self.whatsapp.send_error("Daily LinkedIn post failed")
        except Exception as e:
            logger.error(f"Daily post error: {str(e)}")
            self.whatsapp.send_error(str(e))

    def post_certificate(self, cert_path=None, cert_name=None, issuing_org=None, skills=None):
        logger.info("=" * 50)
        logger.info("Starting certificate post...")
        
        if not cert_path:
            cert_folder = self.config.get('certificate_folder', 'certificates')
            if os.path.exists(cert_folder):
                files = [f for f in os.listdir(cert_folder) if f.lower().endswith(('.png', '.jpg', '.jpeg'))]
                if files:
                    cert_path = os.path.join(cert_folder, files[0])
                    cert_name = os.path.splitext(files[0])[0].replace('-', ' ').replace('_', ' ').title()
                else:
                    logger.warning("No certificate images found")
                    return False
            else:
                logger.warning("Certificate folder not found")
                return False
        
        if not cert_name:
            cert_name = "Professional Certification"
        if not issuing_org:
            issuing_org = "Professional Organization"
        if not skills:
            skills = []
        
        logger.info(f"Certificate: {cert_name} from {issuing_org}")
        
        content = self.ai.generate_certificate_post(cert_name, issuing_org, skills)
        hashtags = self.hashtags.get_certificate_hashtags(cert_name, skills, issuing_org)
        full_post = f"{content}\n\n{hashtags}"
        
        try:
            if not self.linkedin.driver:
                self.linkedin.setup_driver(headless=self.headless)
            
            if not self.linkedin.login():
                 logger.error("LinkedIn login failed for certificate post")
                 return False

            success = self.linkedin.post_with_image(full_post, cert_path)
            
            if success:
                self.cert_count += 1
                
                if skills:
                    self.skills, added = self.resume_parser.merge_skills(self.skills, skills)
                    if added:
                        logger.info(f"Resume updated with {len(added)} new skills: {', '.join(added)}")
                
                self._save_state()
                logger.info(f"Certificate #{self.cert_count} posted!")
                self.whatsapp.send_post_confirmation('certificate')
            else:
                logger.error("Certificate post failed")
        except Exception as e:
            logger.error(f"Certificate post error: {str(e)}")
            self.whatsapp.send_error(str(e))

    def search_and_notify_jobs(self):
        logger.info("=" * 50)
        logger.info("Searching for jobs...")
        
        all_jobs = self.jobs.search_all()
        
        if not all_jobs:
            logger.info("No jobs found")
            return
        
        high_match = self.jobs.get_high_match(all_jobs, min_score=60)
        
        if high_match:
            logger.info(f"Found {len(high_match)} high-match jobs")
            
            msg = self.ai.generate_job_alert_message(high_match)
            self.whatsapp.send_message(msg)
            
            for job in high_match[:5]:
                logger.info(f"  {job['title']} at {job['company']} - {job['match_score']}% match")
                logger.info(f"  Apply: {job['url']}")
        else:
            logger.info("No high-match jobs found")

    def engage(self):
        logger.info("Starting engagement activity...")
        try:
            if not self.linkedin.driver:
                self.linkedin.setup_driver(headless=self.headless)
            
            if not self.linkedin.login():
                logger.error("LinkedIn login failed for engagement")
                return

            self.linkedin.engage_with_feed(count=5)
            self.whatsapp.send_post_confirmation('engagement')
        except Exception as e:
            logger.error(f"Engage error: {str(e)}")

    def parse_resume(self, resume_path):
        logger.info(f"Parsing resume: {resume_path}")
        skills = self.resume_parser.parse_file(resume_path)
        if skills:
            self.skills, added = self.resume_parser.merge_skills(self.skills, skills)
            self._save_state()
            logger.info(f"Resume parsed: {len(self.skills)} total skills, {len(added)} new")
        return skills

    def run_once(self):
        logger.info("=" * 60)
        logger.info("IPG Agent - Starting full run")
        logger.info("=" * 60)
        
        self._load_state()
        
        try:
            if not self.linkedin.driver:
                self.linkedin.setup_driver(headless=self.headless)
                
            if not self.linkedin.login():
                logger.error("Login failed. Aborting.")
                self.whatsapp.send_error("LinkedIn login failed")
                return
            
            logger.info("Step 1: Daily auto-post")
            self.daily_post()
            time.sleep(5)
            
            logger.info("Step 2: Search jobs")
            self.search_and_notify_jobs()
            time.sleep(5)
            
            logger.info("Step 3: Engage with feed")
            self.engage()
            time.sleep(3)
            
            logger.info("Step 4: Check certificates")
            cert_folder = self.config.get('certificate_folder', 'certificates')
            if os.path.exists(cert_folder):
                files = [f for f in os.listdir(cert_folder) if f.lower().endswith(('.png', '.jpg', '.jpeg'))]
                if files:
                    logger.info(f"Found {len(files)} certificates to post")
                    for f in files[:1]:
                        self.post_certificate(cert_path=os.path.join(cert_folder, f))
                        time.sleep(5)
            
            self._save_state()
            logger.info("=" * 60)
            logger.info(f"IPG Agent run complete! Posts: {self.post_count}, Certs: {self.cert_count}")
            logger.info("=" * 60)
            
        except Exception as e:
            logger.error(f"Agent run error: {str(e)}")
            self.whatsapp.send_error(str(e))
        finally:
            self.linkedin.close()

    def setup_schedule(self):
        self.scheduler.clear()
        post_times = self.config.get('post_times', ['09:00', '12:30', '18:00'])
        job_times = self.config.get('job_search_times', ['10:00', '15:00'])
        
        self.scheduler.add_task(self.daily_post, post_times)
        self.scheduler.add_task(self.search_and_notify_jobs, job_times)
        self.scheduler.add_task(self.engage, ['11:00', '16:00'])
        logger.info(f"Scheduled tasks set for POSTs: {post_times}, JOB searches: {job_times}")

    def run_scheduled(self):
        logger.info("IPG Agent - Starting scheduled mode")
        self._load_state()
        
        last_config_mtime = os.path.getmtime(self.config_path) if os.path.exists(self.config_path) else 0
        
        self.setup_schedule()
        logger.info("Press Ctrl+C to stop")
        
        try:
            while True:
                current_mtime = os.path.getmtime(self.config_path) if os.path.exists(self.config_path) else 0
                if current_mtime > last_config_mtime:
                    logger.info("Config file changed, reloading schedule...")
                    self.config = self._load_config(self.config_path)
                    self.setup_schedule()
                    last_config_mtime = current_mtime

                self.scheduler.tick()
                time.sleep(60)
        except KeyboardInterrupt:
            logger.info("Agent stopped by user")
        finally:
            self.linkedin.close()

def main():
    parser = argparse.ArgumentParser(description='IPG - LinkedIn AI Agent')
    parser.add_argument('--once', action='store_true', help='Run once and exit')
    parser.add_argument('--daemon', action='store_true', help='Run scheduled mode')
    parser.add_argument('--post-cert', type=str, help='Post certificate image')
    parser.add_argument('--cert-name', type=str, help='Certificate name')
    parser.add_argument('--cert-org', type=str, help='Issuing organization')
    parser.add_argument('--cert-skills', type=str, help='Skills (comma separated)')
    parser.add_argument('--search-jobs', action='store_true', help='Search jobs only')
    parser.add_argument('--parse-resume', type=str, help='Parse resume file')
    parser.add_argument('--config', type=str, default='config.json', help='Config file path')
    parser.add_argument('--headful', action='store_true', help='Run in headful mode (browser visible)')
    args = parser.parse_args()
    
    agent = IPGAgent(config_path=args.config, headless=not args.headful)
    
    if args.parse_resume:
        skills = agent.parse_resume(args.parse_resume)
        print(f"Extracted skills: {', '.join(skills)}")
    elif args.post_cert:
        skills = args.cert_skills.split(',') if args.cert_skills else []
        agent.post_certificate(
            cert_path=args.post_cert,
            cert_name=args.cert_name,
            issuing_org=args.cert_org,
            skills=skills
        )
    elif args.search_jobs:
        agent.search_and_notify_jobs()
    elif args.once:
        agent.run_once()
    elif args.daemon:
        agent.run_scheduled()
    else:
        agent.run_once()

if __name__ == '__main__':
    main()
