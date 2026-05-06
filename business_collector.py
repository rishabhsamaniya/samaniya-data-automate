import time
import random
import logging
import re
import pandas as pd
from datetime import datetime
from bs4 import BeautifulSoup
from selenium import webdriver
from selenium.webdriver.chrome.service import Service
from selenium.webdriver.chrome.options import Options
from webdriver_manager.chrome import ChromeDriverManager
from utils import get_random_user_agent, clean_phone_number

# namespace: business_data_collector_v1
logger = logging.getLogger("business_data_collector_v1")

class BusinessCollectorV1:
    def __init__(self):
        self.driver = None
        self.processed_data = []
        self.seen_entries = set()

    def _init_driver(self):
        if not self.driver:
            chrome_options = Options()
            chrome_options.add_argument("--headless")
            chrome_options.add_argument("--no-sandbox")
            chrome_options.add_argument("--disable-dev-shm-usage")
            chrome_options.add_argument("--disable-blink-features=AutomationControlled")
            chrome_options.add_experimental_option("excludeSwitches", ["enable-automation"])
            chrome_options.add_experimental_option('useAutomationExtension', False)
            chrome_options.add_argument(f"user-agent={get_random_user_agent()}")
            service = Service(ChromeDriverManager().install())
            self.driver = webdriver.Chrome(service=service, options=chrome_options)
            self.driver.execute_cdp_cmd("Page.addScriptToEvaluateOnNewDocument", {
                "source": "Object.defineProperty(navigator, 'webdriver', {get: () => undefined})"
            })

    def _extract_star_rating(self, text):
        # Look for patterns like "4.5" or "4.5 out of 5"
        match = re.search(r'(\d\.\d)(?:\s*stars|\s*★|\s*out of 5)', text, re.IGNORECASE)
        if match: return float(match.group(1))
        return 0.0

    def collect_city_data(self, category, city):
        self._init_driver()
        
        # Broader query to catch more results
        if "Din-Out" in category:
            query = f"top 3 star 5 star hotel restaurants {city} with buffet phone number"
        else:
            query = f"{category} in {city} with contact number 3 stars and above"
            
        search_url = f"https://www.google.com/search?q={query.replace(' ', '+')}"
        logger.info(f"Searching: {query}")
        
        try:
            self.driver.get(search_url)
            time.sleep(random.uniform(5, 8))
            
            # Scroll down to load more results if they are in the Local Pack
            self.driver.execute_script("window.scrollTo(0, 1000);")
            time.sleep(2)
            
            soup = BeautifulSoup(self.driver.page_source, "html.parser")
            
            # 1. Look for 'Local Pack' / Google Places results (They have different classes)
            # These are usually in divs with specific attributes or inside a 'tF23ub' class
            place_listings = soup.select('div[data-attrid="pc-list-item"], div.VkpSyc, div.u3M7rc')
            
            # 2. General results
            general_listings = soup.find_all('div', class_='g')
            
            combined_listings = place_listings + general_listings
            logger.info(f"Analyzing {len(combined_listings)} potential results...")

            for list_item in combined_listings:
                text = list_item.get_text(separator=' ')
                
                # Filter for Rating
                rating = self._extract_star_rating(text)
                # If rating is 0, we check if text mentions "3 star" or "5 star" hotel
                if rating == 0:
                    if re.search(r'[3-5]\s*star', text, re.IGNORECASE):
                        rating = 4.0 # Default to 4 if it's a star hotel
                
                if rating < 3.0: continue
                
                # Get Name
                name_tag = list_item.find(['h3', 'div'], role='heading')
                if not name_tag: 
                    name_tag = list_item.select_one('div.rllt__details span, h3')
                
                if not name_tag: continue
                name = name_tag.get_text().strip()
                
                # Get Phone Number
                phone_pattern = r'(?:\+91|0)?[6-9]\d{9}|0\d{2,4}-?\d{6,8}'
                phone_matches = re.findall(phone_pattern, text)
                
                if not phone_matches:
                    # Sometimes phone is in a data attribute
                    phone_data = list_item.get('data-phone-number', '')
                    if phone_data: phone_matches = [phone_data]

                if not phone_matches: continue
                
                for p in phone_matches:
                    phone = clean_phone_number(p)
                    if not phone: continue
                    
                    unique_key = f"{name.lower()}_{phone}"
                    if unique_key in self.seen_entries: continue
                    
                    self.processed_data.append({
                        "Serial Number": len(self.processed_data) + 1,
                        "Category": category,
                        "Name": name,
                        "Contact Name": "",
                        "Contact Number": phone
                    })
                    self.seen_entries.add(unique_key)
                    break # One number per business
                
        except Exception as e:
            logger.error(f"Error in city {city}: {e}")

    def export(self, category):
        if not self.processed_data: return None
        df = pd.DataFrame(self.processed_data)
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        filename = f"business_data_{category.replace(' ', '_')}_{timestamp}.xlsx"
        return df, filename

    def close(self):
        if self.driver:
            self.driver.quit()
            self.driver = None
