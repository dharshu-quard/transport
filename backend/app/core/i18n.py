TRANSLATIONS = {
    "welcome": {
        "en": "Welcome to TamilNadu Transit 360 AI",
        "ta": "தமிழ்நாடு டிரான்சிட் 360 AI-க்கு வரவேற்கிறோம்"
    },
    "booking_confirmed": {
        "en": "Ticket booking confirmed successfully.",
        "ta": "உங்கள் பயணச்சீட்டு முன்பதிவு வெற்றிகரமாக முடிந்தது."
    },
    "destination_approaching": {
        "en": "Attention! Your destination stop is approaching within 500 meters.",
        "ta": "கவனம்! உங்கள் இலக்கு பேருந்து நிறுத்தம் 500 மீட்டருக்குள் வரவுள்ளது."
    },
    "destination_missed": {
        "en": "Alert! You have missed your destination stop!",
        "ta": "எச்சரிக்கை! நீங்கள் உங்கள் இறங்கும் நிறுத்தத்தைத் தாண்டிவிட்டீர்கள்!"
    },
    "wrong_bus_warning": {
        "en": "Warning: You are boarding a bus with an unassigned route!",
        "ta": "எச்சரிக்கை: நீங்கள் தவறான வழித்தடப் பேருந்தில் ஏறுகிறீர்கள்!"
    },
    "duty_assigned": {
        "en": "New duty assigned for today.",
        "ta": "இன்றைய புதிய பணி ஒதுக்கீடு செய்யப்பட்டுள்ளது."
    },
    "drowsiness_detected": {
        "en": "Driver Drowsiness Alert! Stay alert or request relief.",
        "ta": "ஓட்டுநர் சோர்வு எச்சரிக்கை! கவனமாக ஓட்டவும் அல்லது ஓய்வெடுக்கவும்."
    },
    "pass_approved": {
        "en": "Your employee/family transit pass has been approved.",
        "ta": "உங்கள் ஊழியர்/குடும்பப் பயண அட்டை அங்கீகரிக்கப்பட்டுள்ளது."
    },
    "autopilot_booking_executed": {
        "en": "Journey Autopilot booked your regular commute ticket.",
        "ta": "தானியங்கி பயண முன்பதிவு வெற்றிகரமாக முடிந்தது."
    }
}

def get_text(key: str, lang: str = "en") -> str:
    lang = lang.lower() if lang else "en"
    if lang not in ["en", "ta"]:
        lang = "en"
    entry = TRANSLATIONS.get(key)
    if not entry:
        return key
    return entry.get(lang, entry.get("en", key))
