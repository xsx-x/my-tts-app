import streamlit as st
import requests
import re
from google.cloud import texttospeech

# הגדרות עיצוב של הדף
st.set_page_config(page_title="הברה אשכנזית אוטומטית", page_icon="📜")

st.title("🎙️ מחולל דיבור בהברה אשכנזית")
st.markdown("מערכת המשלבת ניקוד אוטומטי של **דיקטא** עם מנוע הדיבור של **גוגל**.")

# --- פונקציית ניקוד אוטומטי (Dicta) ---
def get_vowelized_text(text):
    url = "https://nakdan-2-0.loadbalancer.dicta.org.il/api/api/v2/nakdan/predict"
    payload = {
        "text": text,
        "genre": "rabbinic", # מותאם לטקסטים תורניים
        "vowelization_mode": "full"
    }
    try:
        response = requests.post(url, json=payload)
        if response.status_code == 200:
            result_data = response.json()
            # חיבור המילים המנוקדות למחרוזת אחת
            vowelized_words = [word['options'][0] for word in result_data]
            return " ".join(vowelized_words)
    except Exception as e:
        st.error(f"שגיאה בחיבור לדיקטא: {e}")
        return text

# --- מנוע המרה להגייה אשכנזית (IPA) ---
def convert_to_ashkenazi(vowelized_text, dialect):
    # החלפת ת' רפויה ל-S (רק אם אין דגש)
    text = re.sub(r'ת(?!ּ)', 's', vowelized_text)
    
    # מיפוי בסיסי של ניקוד
    if dialect == "ליטאי":
        mappings = {
            'ָ': 'o',      # קמץ -> O
            'ֹ': 'oy',     # חולם -> OY
            'וֹ': 'oy',    # חולם מלא -> OY
            'ֵ': 'ey',     # צירי -> EY
        }
    else: # חסידי
        mappings = {
            'ָ': 'u',      # קמץ -> U
            'ֹ': 'ay',     # חולם -> AY
            'וֹ': 'ay',    # חולם מלא -> AY
            'ֵ': 'ey',     # צירי -> EY
        }
        
    # החלפת יתר התנועות לצלילים בסיסיים
    general_vowels = {
        'ַ': 'a', 'ֶ': 'e', 'ִ': 'i', 'ֻ': 'u', 'ּ': ''
    }
    
    # ביצוע ההחלפות
    for char, sound in {**mappings, **general_vowels}.items():
        text = text.replace(char, sound)
        
    # תיקון סיומות (קמץ-ה' בסוף מילה הופך ל-uh)
    text = re.sub(r'oה\b' if dialect == "ליטאי" else r'uה\b', 'uh', text)
    
    return text

# --- ממשק משתמש (Sidebar) ---
with st.sidebar:
    st.header("הגדרות")
    api_key = st.text_input("מפתח API של Google Cloud:", type="password")
    dialect = st.radio("סגנון הברה:", ("ליטאי", "חסידי"))
    speed = st.slider("מהירות דיבור:", 0.5, 1.2, 0.85)
    st.info("המפתח אינו נשמר בשרת ומשמש לריצה הנוכחית בלבד.")

# --- גוף האתר ---
user_text = st.text_area("הכנס טקסט בעברית:", placeholder="למשל: ברוך אתה ה' אלוקינו מלך העולם...")

if st.button("השמע בהברה אשכנזית"):
    if not api_key:
        st.warning("אנא הזן מפתח API של גוגל בתפריט הצד.")
    elif not user_text:
        st.warning("אנא הכנס טקסט כלשהו.")
    else:
        with st.spinner("מעבד טקסט (ניקוד + המרה)..."):
            # 1. ניקוד
            vowelized = get_vowelized_text(user_text)
            
            # 2. המרה פונטית
            phonetic = convert_to_ashkenazi(vowelized, dialect)
            
            # 3. יצירת קול דרך גוגל
            try:
                client = texttospeech.TextToSpeechClient(client_options={"api_key": api_key})
                
                # בניית SSML
                ssml_text = f"""
                <speak>
                    <prosody rate='{speed}' pitch='-10%'>
                        <phoneme alphabet='ipa' ph='{phonetic}'>{user_text}</phoneme>
                    </prosody>
                </speak>
                """
                
                synthesis_input = texttospeech.SynthesisInput(ssml=ssml_text)
                voice = texttospeech.VoiceSelectionParams(
                    language_code="he-IL", 
                    name="he-IL-Standard-A"
                )
                audio_config = texttospeech.AudioConfig(
                    audio_encoding=texttospeech.AudioEncoding.MP3
                )

                response = client.synthesize_speech(
                    input=synthesis_input, voice=voice, audio_config=audio_config
                )

                st.audio(response.audio_content, format="audio/mp3")
                st.success("ההגייה הופקה בהצלחה!")
                with st.expander("ראה פירוט טכני"):
                    st.write(f"**טקסט מנוקד:** {vowelized}")
                    st.write(f"**ייצוג פונטי:** {phonetic}")
                    
            except Exception as e:
                st.error(f"שגיאה מול גוגל: {e}")
