import requests
from bs4 import BeautifulSoup
import time
import random
import logging
import re
import os
import platform
from selenium import webdriver
from selenium.webdriver.chrome.service import Service
from selenium.webdriver.chrome.options import Options
from webdriver_manager.chrome import ChromeDriverManager
from utils import get_random_user_agent, extract_indian_phone_numbers, clean_phone_number

logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

class ExperienceScraper:
    def __init__(self):
        self.session = requests.Session()
        self.session.headers.update({"User-Agent": get_random_user_agent()})
        self.driver = None

    def _init_driver(self):
        if not self.driver:
            chrome_options = Options()
            chrome_options.add_argument("--headless")
            chrome_options.add_argument("--no-sandbox")
            chrome_options.add_argument("--disable-dev-shm-usage")
            chrome_options.add_argument("--disable-gpu")
            chrome_options.add_argument("--disable-blink-features=AutomationControlled")
            chrome_options.add_experimental_option("excludeSwitches", ["enable-automation"])
            chrome_options.add_experimental_option('useAutomationExtension', False)
            chrome_options.add_argument(f"user-agent={get_random_user_agent()}")
            
            # Detect environment: Streamlit Cloud (Linux) vs Local (Mac/Windows)
            if platform.system() == "Linux":
                # Paths for chromium on Streamlit Cloud (via packages.txt)
                chrome_options.binary_location = "/usr/bin/chromium"
                service = Service("/usr/bin/chromedriver")
            else:
                # Local development
                service = Service(ChromeDriverManager().install())
                
            self.driver = webdriver.Chrome(service=service, options=chrome_options)
            self.driver.execute_cdp_cmd("Page.addScriptToEvaluateOnNewDocument", {
                "source": "Object.defineProperty(navigator, 'webdriver', {get: () => undefined})"
            })

    def _get_request(self, url, timeout=15):
        try:
            self.session.headers.update({"User-Agent": get_random_user_agent()})
            response = self.session.get(url, timeout=timeout)
            response.raise_for_status()
            return response.text
        except: return None

    def _perform_search(self, query, city, biz_name):
        self._init_driver()
        search_url = f"https://www.google.com/search?q={query.replace(' ', '+')}"
        logger.info(f"Searching: {search_url}")
        
        try:
            self.driver.get(search_url)
            time.sleep(random.uniform(3, 5))
            
            soup = BeautifulSoup(self.driver.page_source, "html.parser")
            
            # Extract URLs
            links = []
            for g in soup.find_all('div', class_='g'):
                a = g.find('a')
                if a and a.get('href', '').startswith('http'):
                    links.append(a['href'])
            
            # Extract text for snippet validation
            page_text = soup.get_text()
            numbers = extract_indian_phone_numbers(page_text, city=city, biz_name=biz_name)
            
            return links, numbers
        except Exception as e:
            logger.error(f"Search error: {e}")
            return [], []

    def scrape_business_data(self, name, city):
        # Generic precise query
        query = f"'{name}' {city} official contact phone number"
        logger.info(f"Targeting: {name} in {city}")
        
        result = {
            "Contact Number": "",
            "Source URL": "",
            "Confidence Score": "Low"
        }
        
        links, found_numbers = self._perform_search(query, city, name)
        
        # If we found validated numbers in snippets, use the best one
        if found_numbers:
            result["Contact Number"] = found_numbers[0]
            result["Confidence Score"] = "High"
            if links: result["Source URL"] = links[0]
            return result

        # Fallback: Scrape top links
        if links:
            for url in links[:3]:
                # Skip known aggregate sites
                if any(bad in url.lower() for bad in ["makemytrip", "booking.com", "justdial", "indiamart"]):
                    continue
                    
                logger.info(f"Validating link: {url}")
                content = self._get_request(url)
                if content:
                    numbers = extract_indian_phone_numbers(content, city=city, biz_name=name)
                    if numbers:
                        result["Contact Number"] = numbers[0]
                        result["Confidence Score"] = "Medium"
                        result["Source URL"] = url
                        return result
                            
        logger.warning(f"No validated data found for {name}. Leaving blank.")
        return result

    def batch_process(self, df, progress_callback=None):
        enriched_data = []
        try:
            for index, row in df.iterrows():
                # Detect columns
                name = str(row.get("Name", row.get("Hotel Name", row.get("Establishment Name", ""))))
                city = str(row.get("City", ""))
                if not name: continue
                
                data = self.scrape_business_data(name, city)
                enriched_data.append({
                    "Name": name, "City": city,
                    "Contact Number": data["Contact Number"], 
                    "Source URL": data["Source URL"],
                    "Confidence Score": data["Confidence Score"]
                })
                if progress_callback: progress_callback(index + 1, len(df))
                time.sleep(random.uniform(2, 4))
        finally:
            if self.driver: self.driver.quit()
        return enriched_data
