import streamlit as st
import pandas as pd
import io
import time
import base64
from datetime import datetime
from scraper import ExperienceScraper
from utils import parse_hotel_query

# Page Configuration
st.set_page_config(
    page_title="Samaniya Data Automate",
    page_icon="🤖",
    layout="wide"
)

# Custom CSS for Premium Dark Samaniya Theme
st.markdown("""
<style>
    /* Main Background */
    .stApp {
        background: #0E1117;
        color: #FFFFFF;
    }
    
    /* Headers */
    h1, h2, h3 {
        color: #FF4B4B !important;
        font-family: 'Inter', sans-serif;
    }
    
    /* Text Color */
    .stMarkdown, p, span, label {
        color: #E0E0E0 !important;
    }

    /* Buttons */
    .stButton>button { 
        background-color: #FF4B4B; 
        color: #FFFFFF !important; 
        border-radius: 10px; 
        border: none; 
        padding: 12px 28px; 
        font-weight: 700;
        letter-spacing: 0.5px;
        transition: all 0.3s ease;
        box-shadow: 0 4px 15px rgba(255, 75, 75, 0.2);
    }
    
    .stButton>button:hover { 
        background-color: #FF1F1F; 
        color: #FFFFFF !important;
        transform: translateY(-3px);
        box-shadow: 0 8px 25px rgba(255, 75, 75, 0.4);
    }

    /* File Uploader */
    .stFileUploader {
        background-color: #1E2129;
        border: 2px dashed #FF4B4B;
        border-radius: 15px;
        padding: 30px;
        color: #FFFFFF !important;
    }

    /* Dataframe Styling */
    .stDataFrame {
        background-color: #1E2129;
        border-radius: 10px;
    }

    /* Progress Bar */
    .stProgress > div > div > div {
        background-color: #FF4B4B;
    }

    /* Status Messages */
    .stAlert {
        background-color: #1E2129;
        color: #FFFFFF;
        border-left-color: #FF4B4B;
    }
</style>
""", unsafe_allow_html=True)

def experience_enrichment_tab():
    st.header("✨ Experience Data Enrichment")
    st.markdown("Enrich your experiences (Hotels, Grooming, Wellness, etc.) with local contact details.")
    
    uploaded_file = st.file_uploader("Upload Excel (Columns: Name, City)", type=["xlsx"], key="experience_upload")
    
    if uploaded_file:
        df = pd.read_excel(uploaded_file)
        
        # Column Normalization
        name_col = next((c for c in df.columns if any(kw in c.lower() for kw in ["name", "establishment", "hotel", "product"])), None)
        city_col = next((c for c in df.columns if "city" in c.lower()), None)
        
        if not name_col or not city_col:
            st.error("Excel must have columns for 'Name' and 'City'")
            return

        st.info(f"Using columns: **{name_col}** and **{city_col}**")
        st.dataframe(df.head())
        
        if st.button("🚀 Start Data Enrichment"):
            scraper = ExperienceScraper()
            progress_bar = st.progress(0)
            status_text = st.empty()
            timer_text = st.empty()
            results = []
            
            total_rows = len(df)
            start_time = time.time()
            
            try:
                for i, row in df.iterrows():
                    name, city = str(row.get(name_col, "")), str(row.get(city_col, ""))
                    if not name: continue
                    
                    # Status Update
                    completed = i + 1
                    percent = int((completed / total_rows) * 100)
                    
                    # Time Estimation
                    elapsed = time.time() - start_time
                    avg_time_per_row = elapsed / completed if completed > 0 else 0
                    remaining_rows = total_rows - completed
                    est_remaining = avg_time_per_row * remaining_rows
                    
                    # Format time string
                    if est_remaining >= 60:
                        time_str = f"{int(est_remaining // 60)} min {int(est_remaining % 60)} sec"
                    else:
                        time_str = f"{int(est_remaining)} sec"
    
                    status_text.markdown(f"🔍 Processing: **{name}** in **{city}** ({completed}/{total_rows})")
                    timer_text.markdown(f"📊 **Progress: {percent}%** | ⏳ **Estimated Time Remaining: {time_str}**")
                    
                    res = scraper.scrape_business_data(name, city)
                    
                    # Create a dictionary from the original row to preserve all columns (like ID)
                    row_data = row.to_dict()
                    
                    # Add our new scraped data
                    row_data["Contact Number"] = res["Contact Number"]
                    row_data["Source URL"] = res["Source URL"]
                    row_data["Confidence"] = res["Confidence Score"]
                    
                    results.append(row_data)
                    
                    # Auto-save every 20 records to prevent data loss
                    if completed % 20 == 0:
                        pd.DataFrame(results).to_csv("auto_save_backup.csv", index=False)
                        
                    progress_bar.progress(completed / total_rows)
                    time.sleep(1)
            except Exception as e:
                st.error(f"⚠️ An unexpected error occurred: {e}")
            finally:
                scraper.cleanup()
                # Always save whatever we have gathered so far
                if results:
                    pd.DataFrame(results).to_csv("auto_save_backup.csv", index=False)
            
            res_df = pd.DataFrame(results)
            st.success("✅ Enrichment Complete!")
            st.dataframe(res_df)
            
            # Prepare file for download
            buffer = io.BytesIO()
            with pd.ExcelWriter(buffer, engine='openpyxl') as writer:
                res_df.to_excel(writer, index=False)
            
            filename = f"samaniya_data_{datetime.now().strftime('%Y%m%d_%H%M%S')}.xlsx"
            file_data = buffer.getvalue()
            
            # 1. Manual Download Button (Backup)
            st.download_button("📥 Download Results Manually", file_data, filename)
            
            # 2. Automated Download (JS Hack)
            b64 = base64.b64encode(file_data).decode()
            dl_link = f"""
                <script>
                    var a = document.createElement('a');
                    a.href = 'data:application/vnd.openxmlformats-officedocument.spreadsheetml.sheet;base64,{b64}';
                    a.download = '{filename}';
                    document.body.appendChild(a);
                    a.click();
                    document.body.removeChild(a);
                </script>
            """
            st.markdown(dl_link, unsafe_allow_html=True)

def main():
    st.title("🔴 Samaniya Data Automate")
    experience_enrichment_tab()

if __name__ == "__main__":
    main()
