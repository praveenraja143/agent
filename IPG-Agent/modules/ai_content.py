import requests
import os
import logging

logger = logging.getLogger(__name__)

class AIContentGenerator:
    def __init__(self, api_key, provider="groq"):
        self.api_key = api_key
        self.base_url = "https://api.groq.com/openai/v1/chat/completions"
        self.model = "llama-3.3-70b-versatile"
        self.headers = {
            "Authorization": f"Bearer {self.api_key}",
            "Content-Type": "application/json",
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

    def generate_custom_post(self, user_prompt):
        if not user_prompt:
            return "Please provide a prompt for the AI."
            
        full_prompt = f"""Write a LinkedIn post based on this request: {user_prompt}
        
Requirements:
- Professional LinkedIn format
- Engaging hook
- Valuable content
- Line breaks for readability
- 3-5 emojis
- NO hashtags (added separately)"""

        return self._call_api(full_prompt, fallback_on_error=False)

    def _call_api(self, prompt, max_retries=2, fallback_on_error=True):
        if not self.api_key:
            return "Error: API Key missing. Please set your API Key in Settings." if not fallback_on_error else self._fallback_post(prompt)

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
            "max_tokens": 1000,
            "temperature": 0.7,
        }

        last_error = "Unknown error"
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
                    last_error = f"API Error {response.status_code}: {response.text}"
                    logger.warning(last_error)

            except Exception as e:
                last_error = str(e)
                logger.error(f"API attempt {attempt + 1} failed: {last_error}")

        if fallback_on_error:
            return self._fallback_post(prompt)
        return f"Error: {last_error}"

    def _fallback_post(self, prompt):
        return """🚀 Exciting developments in tech!
        
I've been exploring new technologies and learning continuously. The tech industry is evolving fast and it's important to stay updated.

What are you learning these days? Share in the comments! 👇

#TechCommunity #Learning #Professional #Growth #Innovation"""
