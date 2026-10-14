import os
import json
import numpy as np
from sklearn.feature_extraction.text import TfidfVectorizer
from sklearn.naive_bayes import MultinomialNB
from sklearn.pipeline import Pipeline
from sklearn.model_selection import train_test_split
from sklearn.metrics import classification_report, accuracy_score
import joblib

MODEL_DIR = os.path.join(os.path.dirname(__file__), "models")
REPORT_DIR = os.path.join(os.path.dirname(__file__), "reports")
os.makedirs(MODEL_DIR, exist_ok=True)
os.makedirs(REPORT_DIR, exist_ok=True)

MODEL_PATH = os.path.join(MODEL_DIR, "complaint_model.joblib")
REPORT_PATH = os.path.join(REPORT_DIR, "complaint_classification_report.json")

SAMPLE_DATA = [
    # Driver Behavior
    ("Driver was driving rashly near Tindivanam toll and overtook dangerous trucks.", "Driver Behavior"),
    ("Bus driver refused to halt at designated stop for college students.", "Driver Behavior"),
    ("Driver was using mobile phone while steering on NH45.", "Driver Behavior"),
    ("Sudden harsh braking threw elderly passengers off their seats.", "Driver Behavior"),
    ("Driver was shouting and using rude language at passengers.", "Driver Behavior"),
    ("Driver skipped the bypass stop and dropped us 3km away.", "Driver Behavior"),
    ("Speeding above 90 kmh during heavy rain on highway.", "Driver Behavior"),

    # Cleanliness
    ("Seats were filthy and full of dust near rear row.", "Cleanliness"),
    ("Garbage and peanut shells littered throughout the bus floor.", "Cleanliness"),
    ("Terrible foul smell coming from the luggage rack.", "Cleanliness"),
    ("Window glasses were completely muddy and stained.", "Cleanliness"),
    ("Chewed betel leaves spit stains on bus wall.", "Cleanliness"),
    ("Seats cushion was torn and infested with bed bugs.", "Cleanliness"),

    # Punctuality
    ("Bus arrived 45 minutes late without any prior SMS alert.", "Punctuality"),
    ("Departure delayed by more than an hour at Koyambedu terminus.", "Punctuality"),
    ("Bus was standing idle for 30 minutes at tea stall causing missed train.", "Punctuality"),
    ("Late schedule caused heavy delay reaching office in Chennai.", "Punctuality"),
    ("Night sleeper departed 2 hours after scheduled time.", "Punctuality"),

    # Ticketing
    ("Conductor refused to return balance change of 20 rupees.", "Ticketing"),
    ("Electronic ticketing machine battery died and conductor charged cash twice.", "Ticketing"),
    ("Conductor demanded extra 50 rupees for small travel handbag.", "Ticketing"),
    ("Wrong stage fare calculated on ticket receipt.", "Ticketing"),
    ("Conductor did not scan online QR code and claimed server down.", "Ticketing"),

    # AC Malfunction
    ("Air conditioner was not cooling at all throughout 6 hour trip.", "AC Malfunction"),
    ("AC vents were blowing warm humid air and water was leaking on head.", "AC Malfunction"),
    ("Blower fan making loud screeching rattle noise in deluxe bus.", "AC Malfunction"),
    ("AC thermostat temperature set too high, suffocating passengers.", "AC Malfunction"),

    # Overcrowding
    ("Passengers were hanging dangerously from footboard at Guindy.", "Overcrowding"),
    ("Bus was packed with more than 90 people in a 50 seat bus.", "Overcrowding"),
    ("Could not board bus due to extreme overcrowding in peak hour.", "Overcrowding"),
    ("Total suffocating rush inside corridor with school children.", "Overcrowding")
]

def train_complaint_classifier():
    # Expand dataset with realistic variations
    texts, labels = [], []
    for text, label in SAMPLE_DATA:
        texts.append(text)
        labels.append(label)
        # Variations
        texts.append(f"Complaint: {text.lower()}")
        labels.append(label)
        texts.append(f"Regarding bus trip issue: {text}")
        labels.append(label)

    pipeline = Pipeline([
        ("tfidf", TfidfVectorizer(ngram_range=(1, 2), stop_words="english", min_df=1)),
        ("clf", MultinomialNB(alpha=0.5))
    ])

    X_train, X_test, y_train, y_test = train_test_split(texts, labels, test_size=0.25, random_state=42, stratify=labels)
    pipeline.fit(X_train, y_train)

    y_pred = pipeline.predict(X_test)
    acc = accuracy_score(y_test, y_pred)
    rep_dict = classification_report(y_test, y_pred, output_dict=True)

    joblib.dump(pipeline, MODEL_PATH)

    report = {
        "model_name": "Public Complaint Auto-Classification NLP Model",
        "algorithm": "TfidfVectorizer + MultinomialNB",
        "training_samples": len(X_train),
        "test_samples": len(X_test),
        "accuracy": round(float(acc), 4),
        "categories": list(set(labels)),
        "metrics": rep_dict
    }

    with open(REPORT_PATH, "w", encoding="utf-8") as f:
        json.dump(report, f, indent=2)

    print(f"[ML] Complaint classifier trained. Accuracy={acc:.4f}")
    return report

def classify_complaint_text(text: str) -> dict:
    if not os.path.exists(MODEL_PATH):
        train_complaint_classifier()
    pipeline = joblib.load(MODEL_PATH)
    pred_cat = str(pipeline.predict([text])[0])
    probs = pipeline.predict_proba([text])[0]
    classes = pipeline.classes_
    conf = float(np.max(probs))

    # Assigned department based on category
    dept_map = {
        "Driver Behavior": "Traffic & Driver Operations",
        "Cleanliness": "Depot Sanitation & Housekeeping",
        "Punctuality": "Fleet Scheduling & Dispatch",
        "Ticketing": "Commercial & Revenue Audit",
        "AC Malfunction": "Mechanical & Electrical Maintenance",
        "Overcrowding": "Traffic Frequency Planning"
    }

    return {
        "predicted_category": pred_cat,
        "confidence": round(conf, 3),
        "routed_department": dept_map.get(pred_cat, "General Administration"),
        "priority": "HIGH" if pred_cat in ["Driver Behavior", "AC Malfunction"] else "NORMAL"
    }

if __name__ == "__main__":
    train_complaint_classifier()
