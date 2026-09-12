import streamlit as st
import requests
from bs4 import BeautifulSoup
from google import genai

# 1. Page Configuration
st.set_page_config(page_title="AI Student Matchmaker", page_icon="🎓", layout="wide")

st.title("🎓 Autonomous Student Outreach Agent")
st.caption("Instantly find live LinkedIn opportunities and draft hyper-personalized outreach.")

# 2. Sidebar Configuration
with st.sidebar:
    st.header("Configuration")
    gemini_key = st.text_input("Enter Gemini API Key", type="password")
    st.markdown("[Get an API Key from Google AI Studio](https://google.com)")
    st.divider()
    st.info("💡 Tip: Set up your student profile on the right, then search for live jobs!")

# 3. Live LinkedIn Scraping Engine (No login required)
def fetch_live_linkedin_jobs(keyword, location):
    # Target LinkedIn's public guest job search endpoint
    url = f"https://linkedin.com{keyword}&location={location}"
    headers = {
        "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36"
    }
    
    try:
        response = requests.get(url, headers=headers, timeout=10)
        if response.status_code != 200:
            return []
            
        soup = BeautifulSoup(response.text, 'html.parser')
        job_listings = []
        
        # Scrape basic details from the public list cards
        cards = soup.find_all('div', class_='base-card')
        for card in cards[:3]:  # Limit to top 3 for speed
            try:
                title_tag = card.find('h3', class_='base-search-card__title')
                company_tag = card.find('h4', class_='base-search-card__subtitle')
                link_tag = card.find('a', class_='base-card__full-link')
                
                title = title_tag.text.strip() if title_tag else "Unknown Role"
                company = company_tag.text.strip() if company_tag else "Unknown Company"
                link = link_tag['href'].split('?')[0] if link_tag else "#"
                
                job_listings.append({"title": title, "company": company, "link": link})
            except Exception:
                continue
        return job_listings
    except Exception as e:
        st.sidebar.error(f"Scraping error: {e}")
        return []

# 4. App UI Layout
col1, col2 = st.columns([1, 1.2])

with col1:
    st.subheader("📝 Step 1: Student Profile")
    student_profile = st.text_area(
        "Paste Resume text, GitHub bio, or skills summary:",
        height=220,
        placeholder="e.g., Alex Rivera, CS Undergrad. Proficient in Python, SQL, and React. Built a deep learning model for crop classification during a recent hackathon..."
    )
    
    st.subheader("🔍 Step 2: Find Live Opportunities")
    search_keyword = st.text_input("Job Keyword / Tech Stack", placeholder="Python Developer Intern")
    search_location = st.text_input("Location", value="Canada")

with col2:
    st.subheader("🤖 Step 3: Match & Outreach Generation")
    
    if st.button("Find Jobs & Generate Cold Outreach", type="primary"):
        if not gemini_key:
            st.error("Please provide your Gemini API Key in the sidebar.")
        elif not student_profile or not search_keyword:
            st.error("Please fill out the Student Profile and provide a search keyword.")
        else:
            # Phase A: Pull live data
            with st.spinner("Searching live LinkedIn feeds (bypassing restrictions)..."):
                jobs = fetch_live_linkedin_jobs(search_keyword, search_location)
            
            if not jobs:
                st.warning("Could not pull live listings directly from LinkedIn right now. Generating a tailored mock role based on your query instead so you can see the engine work!")
                # Fallback dataset so the app never crashes or gives an empty screen during a pitch
                jobs = [{"title": f"Junior {search_keyword}", "company": "Innovate Analytics", "link": "https://linkedin.com"}]
            
            # Phase B: Run match engine & output text
            for idx, job in enumerate(jobs):
                st.markdown(f"### Match #{idx+1}: {job['title']} at **{job['company']}**")
                st.caption(f"[View Posting on LinkedIn]({job['link']})")
                
                with st.spinner(f"Analyzing alignment for {job['title']}..."):
                    try:
                        client = genai.Client(api_key=gemini_key)
                        
                        prompt = f"""
                        You are an elite, highly empathetic talent scout matching university students to roles.
                        
                        STUDENT DATA:
                        {student_profile}
                        
                        TARGET OPPORTUNITY:
                        Role: {job['title']}
                        Company: {job['company']}
                        
                        Please review the alignment and provide your analysis in this exact markdown layout:
                        
                        #### **📊 Match Analysis**
                        * **Match Score:** [Score]/100
                        * **The Fit:** [A single short, sharp punchy sentence stating exactly why they match or what gap exists]
                        
                        #### **✉️ Dynamic Outreach Copy**
                        Write a short, engaging, 3-sentence email/message to the student explaining why they should apply to this specific role. Mention at least one specific piece of raw technical potential from their profile. Do NOT use placeholder tags like [Insert Name Here]; dynamically output their name if known, or write universally. Keep it sounding human and fresh, not corporate.
                        """
                        
                        response = client.models.generate_content(
                            model='gemini-3.6-flash',
                            contents=prompt,
                        )
                        
                        st.markdown(response.text)
                        st.divider()
                        
                    except Exception as e:
                        st.error(f"LLM Error: {e}")