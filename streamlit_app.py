import streamlit as st
import requests

st.set_page_config(page_title="AI Job Hunter", layout="wide")

st.title("🚀 Resume Analyzer & Tech job hunter")
st.write("Upload your resume to get real-time 2026 job matches for tech jobs.")

uploaded_file = st.file_uploader("Upload Resume (PDF)", type="pdf")

if uploaded_file and st.button("Start Analysis"):
    with st.spinner("Searching the live market and analyzing..."):
        files = {"file": (uploaded_file.name, uploaded_file.getvalue(), "application/pdf")}
        response = requests.post("http://localhost:8000/analyze", files=files)
        
        if response.status_code == 200:
            res = response.json()["analysis"]
            
            # Show Score
            st.metric("Resume Score", f"{res['resume_score']}%")
            
            # Show Improvement Points
            st.subheader("🛠️ Improvement Points")
            for point in res["improvement_points"]:
                st.write(f"- {point}")
            
            # Show Real Job Links
            st.subheader("📍 Real-Time Job Matches")
            for job in res["job_recommendations"]:
                with st.expander(f"{job['title']}"):
                    st.link_button("View & Apply", job["link"])
        else:
            st.error("Error connecting to backend server.")