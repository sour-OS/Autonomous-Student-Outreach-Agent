import os
import streamlit as st
import requests
from google import genai

# 1. Page Configuration
st.set_page_config(page_title="AI Student Matchmaker", page_icon="🎓", layout="wide")

st.title("🎓 Autonomous Student Outreach Agent")
st.caption("Find matching opportunities and draft hyper-personalized outreach — ready to copy and send.")

# 2. Server-side key — the PERSON RUNNING THIS APP sets this once, so visitors never
# need their own API key. Two ways to set it (pick whichever fits your deploy target):
#   a) Local / Codespaces: create .streamlit/secrets.toml with:
#        GEMINI_API_KEY = "your-key-here"
#      (add .streamlit/secrets.toml to .gitignore — never commit it)
#   b) Streamlit Community Cloud: paste the same into the app's "Secrets" settings panel.
# Falls back to an environment variable so `export GEMINI_API_KEY=...` also works.
GEMINI_API_KEY = st.secrets.get("GEMINI_API_KEY", os.environ.get("GEMINI_API_KEY", ""))
MODEL_NAME = "gemini-3.6-flash"

# 2b. Sidebar — informational only, no key entry required from visitors
with st.sidebar:
    st.header("About")
    st.info(
        "💡 Live LinkedIn scraping is blocked by their bot protection and isn't reliable "
        "for a demo, so this app pulls from the free Remotive jobs API instead (falls back "
        "to a sample role if that's unreachable too)."
    )
    if not GEMINI_API_KEY:
        st.warning(
            "No Gemini API key configured on the server yet — see the comment at the "
            "top of app.py for how to add one via Streamlit secrets."
        )

# 3. Stable job-search engine (Remotive public API — no key, no scraping, no ToS issues)
def fetch_jobs(keyword, location, limit=3):
    try:
        resp = requests.get(
            "https://remotive.com/api/remote-jobs",
            params={"search": keyword, "limit": limit},
            timeout=10,
        )
        resp.raise_for_status()
        data = resp.json().get("jobs", [])
        jobs = []
        for j in data[:limit]:
            jobs.append(
                {
                    "title": j.get("title", "Unknown Role"),
                    "company": j.get("company_name", "Unknown Company"),
                    "link": j.get("url", "#"),
                }
            )
        return jobs
    except Exception as e:
        st.sidebar.warning(f"Jobs API unreachable ({e}); using a sample role instead.")
        return []


def suggest_keyword_from_profile(client, profile):
    """Derive a short job-search term straight from the resume, so the search
    actually changes when the resume does — instead of relying on whatever
    was last typed into the keyword box. Returns (term, error) — error is
    None on success, or a short message so failures aren't hidden."""
    try:
        resp = client.models.generate_content(
            model=MODEL_NAME,
            contents=(
                "Read this student profile and output ONLY a 2-4 word job title "
                "or tech-stack search term that best fits them — no punctuation, "
                "no explanation, just the term.\n\nPROFILE:\n" + profile
            ),
        )
        term = resp.text.strip().strip('"').split("\n")[0]
        return (term or _fallback_keyword(profile)), None
    except Exception as e:
        return _fallback_keyword(profile), str(e)


def _fallback_keyword(profile):
    """Used only if the Gemini call itself fails. A crude keyword guess so
    different resumes still don't all collapse onto the same search term."""
    import re
    hits = re.findall(
        r"\b(Python|Java|React|SQL|JavaScript|C\+\+|Machine Learning|Data Science|"
        r"Marketing|Finance|Design|Research|Robotics|Biology|Nursing|Sales)\b",
        profile,
        re.IGNORECASE,
    )
    return f"{hits[0]} intern" if hits else "internship"


# 4. App UI Layout
col1, col2 = st.columns([1, 1.2])

with col1:
    st.subheader("📝 Step 1: Student Profile")
    student_name = st.text_input("Student name (optional)", placeholder="Alex Rivera")
    student_profile = st.text_area(
        "Paste resume text, GitHub bio, or skills summary:",
        height=220,
        placeholder="e.g., CS undergrad. Proficient in Python, SQL, and React. Built a deep "
        "learning model for crop classification during a recent hackathon...",
    )

    st.subheader("🔍 Step 2: Find Opportunities")
    search_keyword = st.text_input(
        "Job Keyword / Tech Stack (optional)",
        placeholder="Leave blank to auto-detect from the profile above",
    )
    search_location = st.text_input("Location (for display only)", value="Canada")

with col2:
    st.subheader("🤖 Step 3: Match & Outreach Generation")

    if st.button("Find Jobs & Generate Outreach", type="primary"):
        if not GEMINI_API_KEY:
            st.error(
                "This app isn't configured with an API key yet. If you're the "
                "developer, add GEMINI_API_KEY to .streamlit/secrets.toml (see the "
                "comment near the top of app.py)."
            )
        elif not student_profile:
            st.error("Please fill out the Student Profile first.")
        else:
            try:
                client = genai.Client(api_key=GEMINI_API_KEY)
            except Exception as e:
                st.error(f"Could not initialize Gemini client: {e}")
                st.stop()

            effective_keyword = search_keyword.strip()
            if not effective_keyword:
                with st.spinner("Reading the profile to figure out what to search for..."):
                    effective_keyword, kw_error = suggest_keyword_from_profile(client, student_profile)
                if kw_error:
                    st.warning(
                        f"Keyword auto-detection call failed ({kw_error}) — using a "
                        f"rough fallback guess instead: **{effective_keyword}**"
                    )
                else:
                    st.caption(f"🔎 Auto-detected search term: **{effective_keyword}**")

            with st.spinner(f"Searching for '{effective_keyword}' roles..."):
                jobs = fetch_jobs(effective_keyword, search_location)

            if not jobs:
                st.warning(
                    "No live listings found — generating a tailored sample role instead "
                    "so you can see the engine work."
                )
                jobs = [
                    {
                        "title": f"Junior {effective_keyword}",
                        "company": "Innovate Analytics",
                        "link": "#",
                    }
                ]

            for idx, job in enumerate(jobs):
                st.markdown(f"### Match #{idx + 1}: {job['title']} at **{job['company']}**")
                if job["link"] != "#":
                    st.caption(f"[View Posting]({job['link']})")

                with st.spinner(f"Analyzing alignment for {job['title']}..."):
                    prompt = f"""
                    You are an elite, highly empathetic talent scout matching university students to roles.

                    STUDENT DATA:
                    Name: {student_name or "Not provided"}
                    Profile: {student_profile}

                    TARGET OPPORTUNITY:
                    Role: {job['title']}
                    Company: {job['company']}

                    Respond in exactly this markdown layout:

                    #### 📊 Match Analysis
                    * **Match Score:** [Score]/100
                    * **The Fit:** [one short, sharp sentence on why they match or what gap exists]

                    #### ✉️ Dynamic Outreach Copy
                    Write a short, engaging, 3-sentence message to the student explaining why they
                    should apply to this specific role. Mention at least one specific piece of raw
                    technical potential from their profile. Use their name if provided, otherwise
                    write it so it works without a name. Sound human and fresh, not corporate.
                    """

                    try:
                        response = client.models.generate_content(
                            model=MODEL_NAME,
                            contents=prompt,
                        )
                        result_text = response.text
                        st.markdown(result_text)

                        # Extract just the outreach message for copy/send actions
                        outreach_msg = result_text.split("Dynamic Outreach Copy")[-1]
                        outreach_msg = outreach_msg.replace("#", "").strip()

                        st.text_area(
                            "Copy this message:",
                            value=outreach_msg,
                            height=100,
                            key=f"copy_{idx}",
                        )
                        mailto = (
                            f"mailto:?subject=Opportunity: {job['title']} at {job['company']}"
                            f"&body={requests.utils.quote(outreach_msg)}"
                        )
                        st.link_button("✉️ Open in email draft", mailto)
                        st.caption(
                            "Manual send only — sending unsolicited automated DMs on LinkedIn/"
                            "Instagram violates their terms and risks account bans, so this "
                            "app prepares the message rather than sending it for you."
                        )
                        st.divider()

                    except Exception as e:
                        st.error(f"LLM Error: {e}")