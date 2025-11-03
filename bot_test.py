from transformers import DistilBertForSequenceClassification, DistilBertTokenizerFast
from rapidfuzz import process
from datetime import time, datetime, timedelta
import joblib
from rapidfuzz import process
import re
import gdown, os
import pandas as pd
from datetime import datetime, timedelta

save_dir = "bert-finetuned-final"

url = "https://drive.google.com/uc?id=1Cotxm7qcgRvioWO832GFcZmVsBBD1xBf"
output = f"{save_dir}/model.safetensors"

if not os.path.exists(output):
    gdown.download(url, output, quiet=False, fuzzy=True)

# Reload model + tokenizer
model = DistilBertForSequenceClassification.from_pretrained(save_dir)
tokenizer = DistilBertTokenizerFast.from_pretrained(save_dir)

# Reload label encoder
le = joblib.load(f"{save_dir}/label_encoder.pkl")


intent_map = {
    "find_doctor_by_speciality": {"type": "speciality"},
    "consultation_fee": {"type": "column", "value": "Consultation Fee"},
    "doctor_availability": {"type": "column", "value": "Timings"},
    "doctor_experience": {"type": "column", "value": "Experience"},
    "doctor_expertise": {"type": "column", "value": "Expertise"},
    "doctor_qualification": {"type": "column", "value": "Qualification"},
    "doctor_address": {"type": "column", "value": "Hospital Address"},
    "doctor_contact": {"type": "column", "value": "Hospital Phone"},
    "hospital_info": {"type": "column", "value": "Hospital Address"},
    "language_support": {"type": "column", "value": "Languages"},
    "doctor_description": {"type": "description"},
    "symptom_to_speciality": {"type": "symptom"}}

speciality_aliases = {
    "dentist": "Dentistry", "dental": "Dentistry",
    "cardiologist": "Cardiology", "cardiology": "Cardiology",
    "pediatrician": "Pediatrics", "paediatrician": "Pediatrics", "kids doctor": "Pediatrics",
    "gynecologist": "Gynecology & Obstetrics", "gynaecologist": "Gynecology & Obstetrics",
    "dermatologist": "Dermatology & Cosmetology", "skin": "Dermatology & Cosmetology",
    "ent": "ENT", "ear nose throat": "ENT",
    "endocrinologist": "Endocrinology & Diabetes", "diabetes": "Endocrinology & Diabetes",
    "psychiatrist": "Psychiatry & Psychology", "psychologist": "Psychiatry & Psychology",
    "neurologist": "Neurology & Neurosciences", "neuro": "Neurology & Neurosciences",
    "orthopedic": "Orthopedics & Physiotherapy", "ortho": "Orthopedics & Physiotherapy",
    "oncologist": "Oncology & Hematology", "cancer": "Oncology & Hematology"}

def find_speciality_group(text, doctors_df):
    t = str(text).lower()
    # Alias check
    for alias, group in speciality_aliases.items():
        if alias in t:
            return group
    cleaned = re.sub(r"\b(find|a|doctor|specialist|near|me|consultation|fee|availability)\b", "", t).strip()
    groups = doctors_df["Speciality Group"].astype(str).str.strip().str.title().unique().tolist()
    match, score, _ = process.extractOne(cleaned, groups)
    if score >= 70:
        return match
    return None

def normalize_name(name: str) -> str:
    # return re.sub(r"[^a-z ]", "", name.lower()).strip()
    name = name.lower()
    name = re.sub(r"[^a-z ]", " ", name)   # keep only letters and spaces
    name = re.sub(r"\s+", " ", name).strip()
    return name

def find_doctor_by_name(query, doctors_df):
    q = query.lower()
    q = re.sub(r"(what is|availability|timings|consultation fee|fee|experience|qualification|contact|address)", "", q)
    q = normalize_name(q)
    names = doctors_df["Name"].astype(str).apply(normalize_name).tolist()
    match, score, _ = process.extractOne(q, names)
    if score >= 80:
        # Find the original row by index
        idx = names.index(match)
        return doctors_df.iloc[idx]
    return None

def extract_day_from_query(query):
    q = query.lower()
    days = ["monday","tuesday","wednesday","thursday","friday","saturday","sunday"]
    for d in days:
        if d in q:
            return d
    if "tomorrow" in q:
        tomorrow = (datetime.now() + timedelta(days=1)).strftime("%A").lower()
        return tomorrow
    return None

def extract_time_from_query(query):
    match = re.search(r'(\d{1,2})(?::(\d{2}))?\s*(am|pm)?', query.lower())
    if not match:
        return None
    
    hour = int(match.group(1))
    minute = int(match.group(2) or 0)
    meridian = match.group(3)
    if meridian == "pm" and hour != 12:
        hour += 12
    if meridian == "am" and hour == 12:
        hour = 0
    if 0<=hour<23 and 0<=minute<59:
        return time(hour, minute)
    return None

def format_doctor_row(row, highlight_time=None):
    availability_note = ""
    if highlight_time:
        try:
            for slot in str(row["Timings"]).split(","):
                if "-" in slot:
                    start, end = [t.strip() for t in slot.split("-")]
                    start_dt = datetime.strptime(start, "%H:%M").time()
                    end_dt = datetime.strptime(end, "%H:%M").time()
                    if start_dt <= highlight_time <= end_dt:
                        availability_note = " ✅ Available at requested time"
                        break
        except:
            pass
    return (
        f"{row['Name']} ({row['Speciality Group']})\n"
        f"   • {row['Experience']} years experience\n"
        f"   • Consultation Fee: ₹{row['Consultation Fee']}\n"
        f"   • Available: {row['Timings']}{availability_note}\n"
        f"   • Contact: {row['Hospital Phone']}\n"
        f"   • Address: {row['Hospital Address']}")

def get_doctors_list(doctors, page=1, page_size=5, highlight_time=None):
    start = (page - 1) * page_size
    end = start + page_size
    subset = doctors.iloc[start:end]
    reply_lines = [format_doctor_row(row, highlight_time) for _, row in subset.iterrows()]
    return "\n\n".join(reply_lines), len(doctors)

def apply_constraints(query, doctors):
    q = query.lower()
    # Language filter
    if "Languages" in doctors.columns:
        for lang in ["hindi", "english", "malayalam", "tamil", "telugu", "kannada"]:
            if lang in q:
                doctors = doctors[doctors["Languages"].str.contains(lang, case=False, na=False)]
    # Experience filter
    exp_match = re.search(r"(\d+)\+?\s*years?", q)
    if exp_match:
        min_exp = int(exp_match.group(1))
        doctors = doctors[pd.to_numeric(doctors["Experience"], errors="coerce") >= min_exp]
    # Fee filter
    # fee_match = re.search(r"fee between (\d+)\s*and\s*(\d+)", q)
    # if fee_match:
    #     min_fee, max_fee = map(int, fee_match.groups())
    #     doctors = doctors[
    #         (doctors["Consultation Fee"] >= min_fee) &
    #         (doctors["Consultation Fee"] <= max_fee)
    #     ]
    #     doctors = doctors.sort_values(by="Consultation Fee", ascending=True)
# Day filter using Not_Available_Days
    target_day = extract_day_from_query(query)
    if target_day:
        doctors = doctors[~doctors["Not_Available_Days"].str.contains(target_day, case=False, na=False)]    

    # Timings filter
    target_time = extract_time_from_query(query)
    if target_time:
        def is_available(row):
            timings = str(row["Timings"])
            # Expect format like "09:00 - 18:00"
            for slot in timings.split(","):
                if "-" in slot:
                    start, end = [t.strip() for t in slot.split("-")]
                    try:
                        start_dt = datetime.strptime(start, "%H:%M").time()
                        end_dt = datetime.strptime(end, "%H:%M").time()
                        if start_dt <= target_time <= end_dt:
                            return True
                    except:
                        continue
            return False
        doctors = doctors[doctors.apply(is_available, axis=1)]
    return doctors
doctors_df = pd.read_csv("final_doctors.csv",dtype={"Hospital Phone": str})
doctors_df["Consultation Fee"] = doctors_df["Consultation Fee"].astype(str).str.extract(r"(\d+(?:\.\d+)?)").astype(float)
doctors_df["Speciality Group"] = doctors_df["Speciality Group"].astype(str).str.strip().str.title()

def chatbot_reply(text1):
    global last_query, last_doctors, page
    # Predict intent
    inputs = tokenizer(text1, return_tensors="pt", truncation=True, padding=True)
    outputs = model(**inputs)
    pred = outputs.logits.argmax().item()
    intent = le.inverse_transform([pred])[0]

    if text1.lower().strip() == "next" and last_doctors is not None:
        total_pages = (len(last_doctors) - 1) // 5 + 1
        if page < total_pages:
            page += 1
        reply, total = get_doctors_list(last_doctors, page=page, page_size=5)
        return "pagination", f"Showing page {page} of {total_pages}:\n\n{reply}"
    if text1.lower().strip() == "previous" and last_doctors is not None:
        if page > 1:
            page -= 1
        reply, total = get_doctors_list(last_doctors, page=page, page_size=5)
        total_pages = (len(last_doctors) - 1) // 5 + 1
        return "pagination", f"Showing page {page} of {total_pages}:\n\n{reply}"

    # Keyword overrides
    if "availability" in text1.lower():
        intent = "doctor_availability"
    if "fee" in text1.lower():
        if find_doctor_by_name(text1, doctors_df) is not None:
            intent = "consultation_fee"
    if "expertise" in text1.lower():
        intent = "doctor_expertise"
    if "experience" in text1.lower():
        intent = "doctor_experience"
    if "description" in text1.lower() or "describe" in text1.lower():
        intent = "doctor_description"
    if "address" in text1.lower() or "location" in text1.lower():
        intent = "doctor_address"
    if "contact" in text1.lower() or "phone" in text1.lower() or "number" in text1.lower():
        intent = "doctor_contact"
    # INTENT HANDLING
    if intent == "find_doctor_by_speciality":
        group = find_speciality_group(text1, doctors_df)
        if group:
            doctors = doctors_df[doctors_df["Speciality Group"].str.title() == group.title()]
            doctors = apply_constraints(text1, doctors)
            #  Extract fee range if present            
            fee_match = re.search(r"fee between (\d+)\s*and\s*(\d+)", text1.lower())
            # if fee_match:
            #     pass          
            # elif "fee" in text1.lower():
            #     doctors = doctors.sort_values(by="Consultation Fee", ascending=True)
            if "low to high" in text1.lower() or "ascending" in text1.lower():
                doctors = doctors.sort_values(by="Consultation Fee", ascending=True)
            elif "high to low" in text1.lower() or "descending" in text1.lower():
                doctors = doctors.sort_values(by="Consultation Fee", ascending=False)
            elif "experience" in text1.lower():
                doctors = doctors.sort_values(by="Experience", ascending=False)
            # if doctors.empty:
            #     return intent, f"No {group} doctors found with those constraints."
            else:
                doctors = doctors.sample(frac=1).reset_index(drop=True)
            if doctors.empty:
                return intent, f"Sorry, no {group} doctors match those constraints."
            last_query = text1
            last_doctors = doctors
            page = 1
            reply, total = get_doctors_list(doctors, page=page, page_size=5)
            total_pages = (len(doctors) - 1) // 5 + 1
            return intent, (
                f"I found {total} {group} doctors. Showing page {page} of {total_pages}:\n\n"
                f"{reply}\n\nType 'next' or 'previous' to navigate.")
            # reply, total = get_doctors_list(doctors, page=1, page_size=5)
            # return intent, f"I found {total} {group} doctors. Showing 1–5:\n\n{reply}\n\nType 'next' to see more."    

    if intent == "doctor_experience":
        doc = find_doctor_by_name(text1, doctors_df)
        if doc is not None:
            return intent, f"{doc['Name']} → Experience: {doc['Experience']} yrs"
        group = find_speciality_group(text1, doctors_df)
        if group:
            # doctors = doctors_df[doctors_df["Speciality Group"].str.title() == group.title()]
            doctors = doctors_df[doctors_df["Speciality Group"].str.lower() == group.lower()]
            doctors = doctors.sort_values(by="Experience", ascending=False)
            doctors = apply_constraints(text1, doctors)
            if doctors.empty:
                return intent, f"No {group} doctors found with those constraints."
            last_query = text1
            last_doctors = doctors
            page = 1
            reply, total = get_doctors_list(doctors, page=page, page_size=5)
            total_pages = (len(doctors) - 1) // 5 + 1
            return intent, (
                f"I found {total} {group} doctors sorted by experience. "
                f"Showing page {page} of {total_pages}:\n\n{reply}\n\n"
                "Type 'next' or 'previous' to navigate.")
            # reply, total = get_doctors_list(doctors, page=1, page_size=5)
            # return intent, f"I found {total} {group} doctors. Showing 1–5:\n\n{reply}\n\nType 'next' to see more."

    if intent == "doctor_availability":
        doc = find_doctor_by_name(text1, doctors_df)
        if doc is not None:
            return intent, f"{doc['Name']} → Timings: {doc['Timings']}"
        group = find_speciality_group(text1, doctors_df)
        if group:
            doctors = doctors_df[doctors_df["Speciality Group"].str.title() == group.title()]
            doctors = apply_constraints(text1, doctors)
            # reply, total = get_doctors_list(doctors, page=1, page_size=5)
            # return intent, f"I found {total} {group} doctors. Showing 1–5:\n\n{reply}\n\nType 'next' to see more."
        if doctors.empty:
            return intent, f"Sorry, no {group} doctors match those constraints. Would you like me to show the nearest alternatives?"
        last_query = text1
        last_doctors = doctors
        page = 1
        reply, total = get_doctors_list(doctors, page=page, page_size=5)
        total_pages = (len(doctors) - 1) // 5 + 1
        return intent, (
            f"I found {total} {group} doctors matching your availability constraints. "
            f"Showing page {page} of {total_pages}:\n\n{reply}\n\n"
            "Type 'next' or 'previous' to navigate.")

    if intent in ["consultation_fee", "doctor_expertise", "doctor_qualification",
                  "doctor_contact", "doctor_address", "hospital_info", "language_support"]:
        doc = find_doctor_by_name(text1, doctors_df)
        if doc is None:
            return intent, "Sorry, I couldn’t find that doctor."
        col = intent_map[intent]["value"]
        return intent, f"{doc['Name']} → {col}: {doc[col]}"

    if intent == "doctor_description":
        doc = find_doctor_by_name(text1, doctors_df)
        if doc is None:
            return intent, "Sorry, I couldn’t find that doctor."
        return intent, f"{doc['Name']} → Description: {doc['Description']}"

    return intent, "Sorry, I couldn’t map that symptom."


# queries = [
#     "Find a cardiology doctor",
#     "Next",
#     "Next",
#     "Next",
#     "Previous",
#     "Previous"]
# for q in queries:
#     intent, reply = chatbot_reply(q)
#     print(f"Query: {q}")
#     print(f"Predicted intent: {intent}")
#     print(f"Chatbot reply:\n{reply}")

#     print("-" * 80)



