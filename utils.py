import re
import random

USER_AGENTS = [
    "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/119.0.0.0 Safari/537.36",
    "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/118.0.0.0 Safari/537.36",
    "Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/119.0.0.0 Safari/537.36",
]

# Common Indian STD Codes for validation
STD_CODES = {
    "delhi": "011", "mumbai": "022", "kolkata": "033", "chennai": "044",
    "bangalore": "080", "hyderabad": "040", "pune": "020", "ahmedabad": "079",
    "jaipur": "0141", "lucknow": "0522", "chandigarh": "0172", "srinagar": "0194",
    "jammu": "0191", "shimla": "0177", "dehradun": "0135", "gurgaon": "0124",
    "noida": "0120", "agra": "0562", "varanasi": "0542", "amritsar": "0183",
    "bhopal": "0755", "indore": "0731", "nagpur": "0712", "kochi": "0484"
}

def get_random_user_agent():
    """Returns a random user agent from the list."""
    return random.choice(USER_AGENTS)

def clean_phone_number(phone_str):
    if not phone_str: return ""
    cleaned = re.sub(r'[^\d]', '', phone_str)
    # Standardize to 10-12 digits
    if cleaned.startswith('91') and len(cleaned) == 12: cleaned = cleaned[2:]
    return cleaned

def extract_indian_phone_numbers(text, city="", biz_name=""):
    """
    Extremely strict extraction logic to ensure data accuracy.
    """
    if not text: return []
    
    city = city.lower().strip()
    biz_name = biz_name.lower().strip()
    
    # Regex for mobile and landlines
    pattern = r'(?:\+91|0)?[6-9]\d{9}|0\d{2,4}-?\d{6,8}'
    matches = list(re.finditer(pattern, text))
    
    valid_numbers = []
    
    for match in matches:
        num = match.group()
        cleaned = clean_phone_number(num)
        
        # 1. Block National/Toll-free numbers
        if cleaned.startswith(('1800', '1860', '011')) and "delhi" not in city:
            if cleaned.startswith('011'): continue 
            if cleaned.startswith(('1800', '1860')): continue 
            
        # 2. Area Code Validation for Landlines
        if cleaned.startswith('0') and len(cleaned) > 10:
            expected_code = STD_CODES.get(city)
            if expected_code and not cleaned.startswith(expected_code):
                continue 
        
        # 3. Contextual Validation (Proximity check)
        start = max(0, match.start() - 60)
        end = min(len(text), match.end() + 60)
        context = text[start:end].lower()
        
        is_relevant = False
        if biz_name and biz_name in context: is_relevant = True
        
        # Expanded keywords for Hotels, Grooming, Wellness, and Spas
        keywords = [
            "reception", "front desk", "desk", "call", "contact", 
            "property", "salon", "spa", "wellness", "appointment", 
            "booking", "enquiry", "manager", "support"
        ]
        
        if any(kw in context for kw in keywords):
            is_relevant = True
            
        if is_relevant:
            valid_numbers.append(cleaned)
            
    return list(dict.fromkeys(valid_numbers))

def parse_hotel_query(raw_string):
    if not raw_string: return "", ""
    for delimiter in [' - ', ' – ', ',', '|', ':']:
        if delimiter in raw_string:
            parts = raw_string.split(delimiter, 1)
            return parts[0].strip(), parts[1].strip()
    return raw_string.strip(), ""
