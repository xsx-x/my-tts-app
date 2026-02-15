import streamlit as st
from google.cloud import texttospeech

st.set_page_config(page_title="הברה אשכנזית", layout="centered")

st.title("ממיר טקסט להברה אשכנזית")
st.write("הכנס מפתח API וטקסט כדי לשמוע את התוצאה.")

# תיבת קלט למפתח (נמחק ברגע שסוגרים את הדפדפן)
api_key = st.text_input("מפתח API של גוגל:", type="password")

# תיבת טקסט לקלט המשתמש
text_input = st.text_area("טקסט בעברית:", "בָּרוּךְ אַתָּה ה' אֱלֹהֵינוּ מֶלֶךְ הָעוֹלָם")

def convert_to_phonetic(text):
    # כאן אנחנו "מרמים" את המנוע של גוגל
    # מחליפים קמץ (ָ) ב-O, ת' רפויה ב-S וכו'
    text = text.replace("ת", "s")
    text = text.replace("ָ", "o")
    return text

if st.button("השמע"):
    if not api_key:
        st.error("אנא הכנס מפתח API")
    else:
        try:
            client = texttospeech.TextToSpeechClient(client_options={"api_key": api_key})
            phonetic_text = convert_to_phonetic(text_input)
            
            # בניית הבקשה לגוגל
            ssml = f"<speak><phoneme alphabet='ipa' ph='{phonetic_text}'>{text_input}</phoneme></speak>"
            synthesis_input = texttospeech.SynthesisInput(ssml=ssml)
            
            voice = texttospeech.VoiceSelectionParams(language_code="he-IL", name="he-IL-Standard-A")
            audio_config = texttospeech.AudioConfig(audio_encoding=texttospeech.AudioEncoding.MP3, pitch=-1.5)

            response = client.synthesize_speech(input=synthesis_input, voice=voice, audio_config=audio_config)
            
            st.audio(response.audio_content, format="audio/mp3")
        except Exception as e:
            st.error(f"שגיאה: {e}")
