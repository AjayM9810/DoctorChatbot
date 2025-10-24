import base64
import streamlit as st
from bot_test import chatbot_reply

st.set_page_config(page_title="Doctor Finder Chatbot")

if "history" not in st.session_state:
    st.session_state.history = []
if "input_counter" not in st.session_state:
    st.session_state.input_counter = 0 
if "specialty_counts" not in st.session_state:
    st.session_state.specialty_counts = {} 

def get_base64_of_bin_file(bin_file):
    with open(bin_file, "rb") as f:
        data = f.read()
    return base64.b64encode(data).decode()
img_path = "bgimg.jpg"  # make sure this file is in the same folder
img_base64 = get_base64_of_bin_file(img_path)

page_bg = f"""
<style>
[data-testid="stAppViewContainer"] {{
    background-image:linear-gradient(rgba(255,255,255,0.75), rgba(240,248,255,0.6)),url("data:image/jpg;base64,{img_base64}");
    background-size: cover;
    background-position: center;
    background-repeat: no-repeat;
    background-attachment: fixed;
}}
</style>
"""
st.markdown(page_bg, unsafe_allow_html=True)

st.markdown("""
    <style>
        .stApp {
            background: linear-gradient(to right,135deg, #e6e6fa, #ffffff );
        }
        .user-msg {
            background-color: #d1e7dd;
            padding: 10px;
            border-radius: 10px;
            margin: 5px 0;
        }
        .bot-msg {
            background-color: #f8f9fa;
            padding: 10px;
            border-radius: 10px;
            margin: 5px 0;
            border: 1px solid #ddd;
        }
        .info-box {
            background-color: #f0f8ff;
            padding: 12px;
            border-radius: 8px;
            margin-bottom: 15px;
        }
    </style>
""", unsafe_allow_html=True)
st.title("👨‍⚕️ Find My Doctor 👩‍⚕️")

st.markdown("""
<div class="info-box">
💡 Tip: Enter your query below. Use the navigation buttons to explore results.
</div>
""", unsafe_allow_html=True)

import re

# --- Sticky Sidebar Styling ---
st.markdown("""
    <style>
    [data-testid="stSidebar"] {
        position: fixed;
        top: 0;
        left: 0;
        height: 100%;
        overflow-y: auto;
    }
    </style>
""", unsafe_allow_html=True)

# --- Initialize specialty counts in session state ---
if "specialty_counts" not in st.session_state:
    st.session_state.specialty_counts = {}

# --- Update counts whenever a bot reply mentions doctors ---
for speaker, msg in reversed(st.session_state.history):
    if speaker == "Bot" and "I found" in msg:
        # Example reply: "I found 17 ENT doctors"
        match = re.search(r"I found (\d+)\s+(\w+)", msg, re.IGNORECASE)
        if match:
            count = int(match.group(1))
            specialty = match.group(2).capitalize()
            st.session_state.specialty_counts[specialty] = count
        break

# --- Sidebar (Sticky + Dynamic) ---
with st.sidebar:
    st.title("✨ Start Your Health Journey")

    menu = st.radio("One click to explore trusted specialists near you.", 
                    ["About", "Doctors & Specialities", "Select Specialty"])

    if menu == "About":
        st.markdown("""
        <div style="background-color:#f0f8ff;
                    padding:12px;
                    border-radius:8px;
                    border:1px solid #d0e0f0;">
        <h4>ℹ️ About Doctor Finder</h4>
        <p>Learn how we connect patients with the right specialists.</p>
        <ul>
            <li>🔎 Search doctors by specialty</li>
            <li>📅 View availability & timings</li>
            <li>💰 Check consultation fees</li>
            <li>📍 Get hospital/clinic addresses</li>
            <li>📞 Access contact numbers</li>
        </ul>
        </div>
        """, unsafe_allow_html=True)

    elif menu == "Doctors & Specialities":
    # Define your speciality counts (can later be loaded from a dataframe)
        st.markdown(
            """
    <div style="background-color:#f9fcff;
                    padding:14px;
                    border-radius:10px;
                    border:1px solid #d0e0f0;
                    font-size:15px;">
        <ul style="list-style-type:none; padding-left:0; line-height:1.6;">
            <li>🩺 Total <b>846</b> Doctors Available</li>
            <li>📚 <b>29</b> Speciality Groups</li>
        </ul>
        <hr style="border:1px solid #d0e0f0; margin:8px 0;">
        <h4>🔍 Speciality-wise Doctors:</h4>
        <ul style="list-style-type:none; padding-left:0; line-height:1.6;">
            <li>⚕️ General Medicine — <b>180</b></li>
            <li>🦷 Dentistry — <b>132</b></li>
            <li>👶 Pediatrics — <b>66</b></li>
            <li>🌿 Ayush — <b>51</b></li>
            <li>🤰 Gynecology & Obstetrics — <b>33</b></li>
            <li>❤️ Cardiology — <b>28</b></li>
            <li>🦴 Orthopedics & Physiotherapy — <b>26</b></li>
            <li>🧠 Neurology & Neurosciences — <b>26</b></li>
            <li>🏡 Homeo — <b>23</b></li>
            <li>💤 Anesthesiology — <b>23</b></li>
            <li>💆 Dermatology & Cosmetology — <b>23</b></li>
            <li>🧘 Psychiatry & Psychology — <b>21</b></li>
            <li>🚑 Emergency & Critical Care — <b>19</b></li>
            <li>🍽️ Gastroenterology & Hepatology — <b>19</b></li>
            <li>🧪 Pathology & Lab Medicine — <b>19</b></li>
            <li>🔪 General & Surgical Specialities — <b>17</b></li>
            <li>👂 ENT — <b>17</b></li>
            <li>🎗️ Oncology & Hematology — <b>17</b></li>
            <li>👁️ Ophthalmology — <b>17</b></li>
            <li>🩻 Radiology & Imaging — <b>15</b></li>
            <li>🌬️ Pulmonology & Respiratory Medicine — <b>12</b></li>
            <li>🧑‍⚕️ Plastic & Reconstructive Surgery — <b>11</b></li>
            <li>💧 Urology — <b>9</b></li>
            <li>🫘 Nephrology — <b>8</b></li>
            <li>💑 Sexology & Fertility — <b>5</b></li>
            <li>🧎 Rehabilitation & Wellness — <b>5</b></li>
            <li>🥗 Dietetics — <b>5</b></li>
            <li>🩸 Endocrinology & Diabetes — <b>4</b></li>
            <li>🦠 Infectious Diseases — <b>3</b></li>
            <li>🛡️ Preventive & Public Health — <b>3</b></li>
            <li>🦵 Rheumatology — <b>3</b></li>
            <li>🧬 Nuclear Medicine & Genetics — <b>2</b></li>
            <li>🌅 Pain & Palliative Care — <b>2</b></li>
            <li>👴 Geriatrics — <b>1</b></li>
            <li>🏃 Sports Medicine — <b>1</b></li>
        </ul>
    </div>
            """, 
            unsafe_allow_html=True
        )
    elif menu == "Select Specialty":
        specialty = st.selectbox("Choose a specialty", 
                                 ["ENT", "Cardiologist", "Dermatologist", "Pediatrician", "Orthopedic"])
        # fee_range = st.slider(
        #     "Select consultation fee range (₹)", 
        #     min_value=0, 
        #     max_value=5000, 
        #     value=(0, 2000),  # default range
        #     step=100
        # )
        sort_option = st.radio(
            "Sort consultation fee",
            ["Low to High", "High to Low"],
            horizontal=True
        )
        
        if st.button("🩺 Find Doctor"):
            if sort_option == "Low to High":
                query = f"Find {specialty} low to high"
            else:
                query = f"Find {specialty} high to low"
            intent, reply = chatbot_reply(query)
            st.session_state.history.append(("You", query))            
            # intent, reply = chatbot_reply(f"Find {specialty} with fee between {fee_range[0]} and {fee_range[1]}")
            # st.session_state.history.append(("You", f"Find {specialty} with fee between {fee_range[0]} and {fee_range[1]}"))
            st.session_state.history.append(("Bot", reply))
            st.rerun()


# --- Containers for layout ---
chat_container = st.container()  # Conversation displayed here
input_container = st.container()  # Input box at bottom

# --- Display conversation history at the top ---
with chat_container:
    for speaker, message in st.session_state.history:
        if speaker == "You":
            # st.markdown(f"**{speaker}:** {message}")
            st.markdown(f"<div class='user-msg'><strong>{speaker}:</strong> {message}</div>", unsafe_allow_html=True)
        else:
            # st.markdown(
            #     f"<div style='background:#f0f0f0;padding:8px;border-radius:5px'>{speaker}: {message}</div>",
            #     unsafe_allow_html=True,)
            st.markdown(f"<div class='bot-msg'><strong>{speaker}:</strong> {message}</div>", unsafe_allow_html=True)


# --- Input box + Send button at the bottom ---
with input_container:
    input_key = f"user_input_{st.session_state.input_counter}"
    user_text = st.text_input("Enter your query:", key=input_key, placeholder= "Enter your query here...")

    col1, col2, col3 = st.columns([3,1,1])  # Send, Previous, Next buttons
    with col1:
        if st.button("🚀 Enter"):
            text = st.session_state.get(input_key, "").strip()
            if text:
                intent, reply = chatbot_reply(text)
                st.session_state.history.append(("You", text))
                st.session_state.history.append(("Bot", reply))
                st.session_state.input_counter += 1  # new key to clear input
                st.rerun()
    with col2:
        if st.button("⏮️ Prev"):
            intent, reply = chatbot_reply("previous")
            st.session_state.history.append(("You", "Previous"))
            st.session_state.history.append(("Bot", reply))
            st.rerun()
    with col3:
        if st.button("⏭️ Next"):
            intent, reply = chatbot_reply("next")
            st.session_state.history.append(("You", "Next"))
            st.session_state.history.append(("Bot", reply))
            st.rerun()
