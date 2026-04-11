"""
LinkedIn REST API Client - No Selenium, No Browser, No CAPTCHA!
Uses OAuth 2.0 + Official LinkedIn API for reliable posting.
"""
import requests
import logging
import urllib.parse

logger = logging.getLogger(__name__)


class LinkedInAPI:
    AUTH_URL = "https://www.linkedin.com/oauth/v2/authorization"
    TOKEN_URL = "https://www.linkedin.com/oauth/v2/accessToken"
    USERINFO_URL = "https://api.linkedin.com/v2/userinfo"
    POST_URL = "https://api.linkedin.com/v2/ugcPosts"

    def __init__(self, client_id, client_secret, redirect_uri):
        self.client_id = client_id
        self.client_secret = client_secret
        self.redirect_uri = redirect_uri
        self.access_token = None
        self.person_id = None
        self.user_name = None

    def get_auth_url(self):
        """Generate the OAuth authorization URL for the user to visit."""
        params = {
            "response_type": "code",
            "client_id": self.client_id,
            "redirect_uri": self.redirect_uri,
            "scope": "openid profile w_member_social",
            "state": "ipg-agent-auth"
        }
        return f"{self.AUTH_URL}?{urllib.parse.urlencode(params)}"

    def exchange_code_for_token(self, code):
        """Exchange the authorization code for an access token."""
        try:
            data = {
                "grant_type": "authorization_code",
                "code": code,
                "redirect_uri": self.redirect_uri,
                "client_id": self.client_id,
                "client_secret": self.client_secret
            }
            resp = requests.post(self.TOKEN_URL, data=data, timeout=15)
            if resp.status_code == 200:
                token_data = resp.json()
                self.access_token = token_data.get("access_token")
                logger.info("LinkedIn access token obtained successfully.")
                self._fetch_profile()
                return True
            else:
                logger.error(f"Token exchange failed: {resp.status_code} - {resp.text}")
                return False
        except Exception as e:
            logger.error(f"Token exchange error: {str(e)}")
            return False

    def set_token(self, token, person_id=None, user_name=None):
        """Set an existing token (loaded from DB/config)."""
        self.access_token = token
        self.person_id = person_id
        self.user_name = user_name

    def _fetch_profile(self):
        """Fetch the authenticated user's profile info."""
        try:
            headers = {"Authorization": f"Bearer {self.access_token}"}
            resp = requests.get(self.USERINFO_URL, headers=headers, timeout=10)
            if resp.status_code == 200:
                data = resp.json()
                self.person_id = data.get("sub")
                self.user_name = data.get("name", "LinkedIn User")
                logger.info(f"Profile fetched: {self.user_name} (ID: {self.person_id})")
            else:
                logger.error(f"Profile fetch failed: {resp.status_code} - {resp.text}")
        except Exception as e:
            logger.error(f"Profile fetch error: {str(e)}")

    def is_authenticated(self):
        """Check if we have a valid token and person ID."""
        return bool(self.access_token and self.person_id)

    def post_text(self, content):
        """Post text content to LinkedIn via the official API."""
        if not self.is_authenticated():
            return False, "Not authenticated. Please connect LinkedIn first."

        try:
            headers = {
                "Authorization": f"Bearer {self.access_token}",
                "Content-Type": "application/json",
                "X-Restli-Protocol-Version": "2.0.0"
            }

            payload = {
                "author": f"urn:li:person:{self.person_id}",
                "lifecycleState": "PUBLISHED",
                "specificContent": {
                    "com.linkedin.ugc.ShareContent": {
                        "shareCommentary": {"text": content},
                        "shareMediaCategory": "NONE"
                    }
                },
                "visibility": {
                    "com.linkedin.ugc.MemberNetworkVisibility": "PUBLIC"
                }
            }

            resp = requests.post(self.POST_URL, json=payload, headers=headers, timeout=30)

            if resp.status_code in [200, 201]:
                logger.info("Post published successfully via LinkedIn API!")
                return True, "Post published successfully!"
            elif resp.status_code == 401:
                logger.error("LinkedIn token expired. Re-authentication needed.")
                return False, "Token expired. Please reconnect LinkedIn."
            else:
                error_msg = resp.text[:200]
                logger.error(f"LinkedIn post error: {resp.status_code} - {error_msg}")
                return False, f"LinkedIn Error ({resp.status_code}): {error_msg}"

        except Exception as e:
            logger.error(f"Post error: {str(e)}")
            return False, f"Error: {str(e)}"

    def verify_token(self):
        """Verify if the current token is still valid."""
        if not self.access_token:
            return False
        try:
            headers = {"Authorization": f"Bearer {self.access_token}"}
            resp = requests.get(self.USERINFO_URL, headers=headers, timeout=10)
            return resp.status_code == 200
        except:
            return False
