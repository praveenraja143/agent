import os
import time
from modules.linkedin import LinkedInBot
import json

def main():
    # Load config
    if os.path.exists('config.json'):
        with open('config.json', 'r') as f:
            config = json.load(f)
    else:
        print("Error: config.json not found")
        return

    bot = LinkedInBot(
        email=config['linkedin_email'],
        password=config['linkedin_password'],
        user_data_dir='data/chrome_profile'
    )

    print("Opening browser for manual login verification...")
    print("If you see a Captcha or OTP request, please solve it manually in the browser window.")
    print("Once you see your LinkedIn Feed, you can close this window or wait 60 seconds.")
    
    # Headless = False to allow user interaction
    bot.setup_driver(headless=False)
    
    try:
        bot.login()
        print("\nChecking login status...")
        time.sleep(5)
        
        if 'feed' in bot.driver.current_url or 'mynetwork' in bot.driver.current_url:
            print("\nSUCCESS: You are logged in!")
            print("Session saved to data/chrome_profile")
        else:
            print("\nSTILL NEED LOGIN: Please complete the login process in the browser window.")
            print("Waiting for 60 seconds so you can finish...")
            time.sleep(60)
            
            if 'feed' in bot.driver.current_url or 'mynetwork' in bot.driver.current_url:
                print("\nSUCCESS: Login completed!")
            else:
                print("\nFAILED: Login not completed. Please try again.")
    finally:
        bot.close()
        print("Browser closed. Your session is now preserved.")

if __name__ == "__main__":
    main()
