# 🤖 Samaniya Data Automate

A premium, automated data enrichment suite built with Streamlit and Selenium. This tool helps you fetch and verify contact details (phone numbers) for various experiences like Hotels, Salons, Spas, and Wellness centers based on their Name and City.

## ✨ Features
- **Multi-Category Support**: Works for Hotels, Grooming, Wellness, and any other business category.
- **Automated Scraping**: Uses Selenium to find the most accurate official contact numbers.
- **Real-time Progress**: Shows percentage completion and estimated time remaining.
- **Auto-Download**: Automatically downloads the enriched Excel file once processing is complete.
- **Premium UI**: Sleek dark mode interface with Havells-inspired red accents.
- **Smart Column Detection**: Automatically identifies name and city columns from your uploaded Excel.

## 🚀 How to Run Locally

### 1. Clone the repository
```bash
git clone https://github.com/rishabhsamaniya/samaniya-data-automate.git
cd samaniya-data-automate
```

### 2. Set up a virtual environment (Recommended)
```bash
python3 -m venv venv
source venv/bin/activate
```

### 3. Install dependencies
```bash
pip install -r requirements.txt
```

### 4. Run the app
```bash
streamlit run app.py
```

## 📋 Requirements
- Python 3.9+
- Chrome Browser (for Selenium)
- Dependencies: `streamlit`, `pandas`, `selenium`, `webdriver-manager`, `openpyxl`, `beautifulsoup4`, `requests`

## 🛠 Usage
1. Prepare an Excel file with columns like **Name** and **City**.
2. Upload the file to the dashboard.
3. Click **"Start Data Enrichment"**.
4. Once complete, your enriched file will download automatically!

---
Developed by [Rishabh Samaniya](https://github.com/rishabhsamaniya)
