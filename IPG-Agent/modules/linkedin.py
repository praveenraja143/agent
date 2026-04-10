from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium.webdriver.common.keys import Keys
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.chrome.service import Service
from webdriver_manager.chrome import ChromeDriverManager
import time
import logging
import os

logger = logging.getLogger(__name__)

class LinkedInBot:
    def __init__(self, email, password, user_data_dir='data/chrome_profile'):
        self.email = email
        self.password = password
        self.user_data_dir = os.path.abspath(user_data_dir)
        self.driver = None
        self.wait = None

    def setup_driver(self, headless=False):
        chrome_options = Options()
        if headless:
            chrome_options.add_argument('--headless')
        
        chrome_options.add_argument(f'--user-data-dir={self.user_data_dir}')
        chrome_options.add_argument('--disable-blink-features=AutomationControlled')
        chrome_options.add_argument('--start-maximized')
        chrome_options.add_experimental_option('excludeSwitches', ['enable-automation'])
        chrome_options.add_experimental_option('useAutomationExtension', False)
        
        service = Service(ChromeDriverManager().install())
        self.driver = webdriver.Chrome(service=service, options=chrome_options)
        self.wait = WebDriverWait(self.driver, 20)
        
        self.driver.execute_cdp_cmd('Page.addScriptToEvaluateOnNewDocument', {
            'source': 'Object.defineProperty(navigator, "webdriver", {get: () => undefined})'
        })
        logger.info(f"Chrome driver setup complete (Profile: {self.user_data_dir})")

    def login(self):
        try:
            if not self.driver:
                self.setup_driver()
            
            self.driver.get('https://www.linkedin.com/feed/')
            time.sleep(5)
            
            # Check if we are already logged in via cookies/profile
            if 'feed' in self.driver.current_url or 'mynetwork' in self.driver.current_url:
                logger.info("Already logged in via persistent profile.")
                return True
            
            # Navigate to login if not
            self.driver.get('https://www.linkedin.com/login')
            time.sleep(3)
            
            try:
                email_field = self.wait.until(
                    EC.presence_of_element_located((By.ID, 'username'))
                )
                email_field.clear()
                email_field.send_keys(self.email)
                
                password_field = self.driver.find_element(By.ID, 'password')
                password_field.clear()
                password_field.send_keys(self.password)
                
                login_btn = self.driver.find_element(By.XPATH, '//button[@type="submit"]')
                login_btn.click()
                time.sleep(5)
            except Exception as e:
                logger.warning(f"Login elements not found or already logged in: {str(e)}")
            
            # Double check
            if 'feed' in self.driver.current_url or 'mynetwork' in self.driver.current_url:
                logger.info("Login successful!")
                return True
            else:
                logger.warning("Login verification required. Current URL: " + self.driver.current_url)
                # If we are stuck at a challenge/otp, we might need manual intervention
                return False
                
        except Exception as e:
            logger.error(f"Login error: {str(e)}")
            return False

    def post_text(self, content):
        try:
            self.driver.get('https://www.linkedin.com/feed/')
            time.sleep(3)
            
            start_post = self.wait.until(
                EC.element_to_be_clickable((By.XPATH, '//button[contains(@aria-label, "Start a post")]'))
            )
            start_post.click()
            time.sleep(2)
            
            text_area = self.wait.until(
                EC.presence_of_element_located((By.XPATH, '//div[@role="textbox"]'))
            )
            text_area.click()
            time.sleep(1)
            
            for line in content.split('\n'):
                text_area.send_keys(line)
                text_area.send_keys(Keys.SHIFT + Keys.ENTER)
                time.sleep(0.3)
            
            time.sleep(2)
            
            post_btn = self.driver.find_element(
                By.XPATH, '//button[@type="submit" and contains(@class, "share-actions__primary-action")]'
            )
            post_btn.click()
            time.sleep(3)
            
            logger.info("Post published successfully!")
            return True
            
        except Exception as e:
            logger.error(f"Post error: {str(e)}")
            return False

    def post_with_image(self, content, image_path):
        try:
            self.driver.get('https://www.linkedin.com/feed/')
            time.sleep(3)
            
            start_post = self.wait.until(
                EC.element_to_be_clickable((By.XPATH, '//button[contains(@aria-label, "Start a post")]'))
            )
            start_post.click()
            time.sleep(2)
            
            text_area = self.wait.until(
                EC.presence_of_element_located((By.XPATH, '//div[@role="textbox"]'))
            )
            text_area.click()
            time.sleep(1)
            
            for line in content.split('\n'):
                text_area.send_keys(line)
                text_area.send_keys(Keys.SHIFT + Keys.ENTER)
                time.sleep(0.3)
            
            media_btn = self.driver.find_element(
                By.XPATH, '//button[contains(@aria-label, "Add media")]'
            )
            media_btn.click()
            time.sleep(1)
            
            import os
            file_input = self.driver.find_element(By.XPATH, '//input[@type="file"]')
            file_input.send_keys(os.path.abspath(image_path))
            time.sleep(3)
            
            time.sleep(2)
            
            post_btn = self.driver.find_element(
                By.XPATH, '//button[@type="submit" and contains(@class, "share-actions__primary-action")]'
            )
            post_btn.click()
            time.sleep(3)
            
            logger.info("Post with image published successfully!")
            return True
            
        except Exception as e:
            logger.error(f"Post with image error: {str(e)}")
            return False

    def engage_with_feed(self, count=5):
        try:
            self.driver.get('https://www.linkedin.com/feed/')
            time.sleep(3)
            
            posts = self.driver.find_elements(
                By.XPATH, '//div[contains(@class, "feed-shared-update-v2")]'
            )[:count]
            
            for post in posts:
                try:
                    like_btn = post.find_element(
                        By.XPATH, './/button[contains(@aria-label, "Like")]'
                    )
                    like_btn.click()
                    time.sleep(1)
                except:
                    pass
                time.sleep(2)
            
            logger.info(f"Engaged with {count} posts")
        except Exception as e:
            logger.error(f"Engage error: {str(e)}")

    def close(self):
        if self.driver:
            self.driver.quit()
            logger.info("Browser closed")
