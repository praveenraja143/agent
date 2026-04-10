import requests
import os
import logging

logger = logging.getLogger(__name__)

class AIContentGenerator:
    def __init__(self, api_key, provider="openrouter"):
        self.api_key = api_key
        self.provider = provider.lower()
        
        if self.provider == "groq":
            self.base_url = "https://api.groq.com/openai/v1/chat/completions"
            self.model = "llama-3.1-70b-versatile" # High quality free model on Groq
            self.headers = {
                "Authorization": f"Bearer {self.api_key}",
                "Content-Type": "application/json",
            }
        else:
            self.base_url = "https://openrouter.ai/api/v1/chat/completions"
            self.model = "qwen/qwen-2.5-coder-32b-instruct"
            self.headers = {
                "Authorization": f"Bearer {self.api_key}",
                "Content-Type": "application/json",
                "HTTP-Referer": "https://ipg-agent.local",
                "X-Title": "IPG Agent",
            }

    def generate_daily_post(self, skills, post_type="general"):
        prompts = {
            "tech_tip": f"Share a practical tech tip about one of these skills: {', '.join(skills[:5])}. Make it actionable.",
            "career_advice": f"Share career advice for developers with skills in: {', '.join(skills[:5])}. Be motivational.",
            "project_idea": f"Describe an impressive project idea using: {', '.join(skills[:5])}. Make it exciting.",
            "industry_insight": f"Share an insight about the tech industry related to: {', '.join(skills[:5])}.",
            "learning_journey": f"Share a learning journey about mastering: {', '.join(skills[:5])}. Be inspiring.",
            "motivational": f"Write a motivational post about tech career growth for skills: {', '.join(skills[:5])}.",
        }
        
        prompt = prompts.get(post_type, prompts["tech_tip"])
        
        full_prompt = f"""{prompt}

Requirements:
- Professional LinkedIn post format
- Start with an attention-grabbing hook
- Provide real value
- End with an engagement question
- Use 3-5 emojis max
- Under 250 words
- Use line breaks for readability
- NO hashtags (added separately)"""

        return self._call_api(full_prompt)

    def generate_certificate_post(self, cert_name, issuing_org, skills):
        skills_text = ', '.join(skills) if isinstance(skills, list) else skills
        
        prompt = f"""Create a professional LinkedIn post for earning a certificate.

Certificate: {cert_name}
Issued by: {issuing_org}
Skills: {skills_text}

Requirements:
- Professional and enthusiastic tone
- Include relevant emojis (3-5 max)
- Under 200 words
- Make it engaging and shareable
- Include a call-to-action
- NO hashtags (added separately)"""

        return self._call_api(prompt)

    def generate_job_alert_message(self, jobs):
        message = "🚀 *Daily Job Alerts*\n\n"
        for i, job in enumerate(jobs[:5], 1):
            message += f"*{i}. {job.get('title', 'N/A')}*\n"
            message += f"   🏢 {job.get('company', 'N/A')}\n"
            message += f"   📍 {job.get('location', 'N/A')}\n"
            message += f"   🎯 {job.get('match_score', 0)}% match\n"
            message += f"   🔗 {job.get('url', '')}\n\n"
        message += "_Click links to apply directly!_"
        return message

    def _call_api(self, prompt, max_retries=2):
        payload = {
            "model": self.model,
            "messages": [
                {
                    "role": "system",
                    "content": "You are a professional LinkedIn content creator. Write engaging, professional posts."
                },
                {
                    "role": "user",
                    "content": prompt
                }
            ],
            "max_tokens": 500,
            "temperature": 0.8,
        }

        for attempt in range(max_retries):
            try:
                response = requests.post(
                    self.base_url,
                    headers=self.headers,
                    json=payload,
                    timeout=30
                )

                if response.status_code == 200:
                    data = response.json()
                    return data['choices'][0]['message']['content'].strip()
                else:
                    logger.warning(f"API error: {response.status_code}")

            except Exception as e:
                logger.error(f"API call attempt {attempt + 1} failed: {str(e)}")

        return self._fallback_post(prompt)

    def _fallback_post(self, prompt):
        return """🚀 Exciting developments in tech!

I've been exploring new technologies and learning continuously. The tech industry is evolving fast and it's important to stay updated.

What are you learning these days? Share in the comments! 👇

#TechCommunity #Learning #Professional #Growth #Innovation"""
