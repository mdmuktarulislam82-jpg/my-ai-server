from flask import Flask, request, send_file
import speech_recognition as sr
import wave
import io
import requests
import asyncio
import edge_tts

app = Flask(__name__)

API_KEYS = [
    "AIzaSyD0euwkB-sCAfuMO98lr9GHQUk0lYXbKeg",
    "AIzaSyDDECR93ev7BoAb9nspyZJXt09ofLeagzk",
    "AIzaSyAO7a66Zy6I20M-MK4WGi7NogD8jG5ySAE",
    "AIzaSyBIUZuCiFN3ZswDhvc2igMwhgsxoctBWzI",
    "AIzaSyBHpdEPIMIG3yBXp3j4YfYRexHj7GNCkq8",
    "AIzaSyAMuxtCxzdg7bQB_bKm7MSiCrvmArxq8fw",
    "AIzaSyCA1WdPrxHohU7yJlRCo0moaSYqN-qrXzk",
    "AIzaSyD9fcVXSpBt6BJ5XXnPY6jN-Xb16RpwfNo",
    "AIzaSyB-hcRIB5WfWO5PJaVs53DWE1k3fTrMXkg"
]
current_key_index = 0

def get_ai_response(prompt):
    global current_key_index
    attempts = 0
    while attempts < len(API_KEYS):
        api_key = API_KEYS[current_key_index]
        url = f"https://generativelanguage.googleapis.com/v1beta/models/gemini-2.5-flash:generateContent?key={api_key}"
        payload = {"contents": [{"parts": [{"text": prompt}]}]}
        try:
            response = requests.post(url, json=payload, headers={"Content-Type": "application/json"})
            if response.status_code == 200:
                return response.json()['candidates'][0]['content']['parts'][0]['text'].strip()
            current_key_index = (current_key_index + 1) % len(API_KEYS)
            attempts += 1
        except Exception as e:
            print(f"⚠️ API Error: {e}")
            current_key_index = (current_key_index + 1) % len(API_KEYS)
            attempts += 1
    return "দুঃখিত, আমি কথা বলতে পারছি না।"

@app.route('/audio.mp3')
def serve_audio():
    return send_file("reply.mp3", mimetype="audio/mpeg")

@app.route('/upload_audio', methods=['POST'])
def receive_audio():
    raw_audio = request.data
    wav_io = io.BytesIO()
    with wave.open(wav_io, 'wb') as wav_file:
        wav_file.setnchannels(1)
        wav_file.setsampwidth(2)
        wav_file.setframerate(16000)
        wav_file.writeframes(raw_audio)
    
    wav_io.seek(0)
    recognizer = sr.Recognizer()
    
    try:
        with sr.AudioFile(wav_io) as source:
            audio_data = recognizer.record(source)
            
            try:
                text = recognizer.recognize_google(audio_data, language="bn-BD")
                print(f"\n🗣️ You said: '{text}'")
            except sr.UnknownValueError:
                print("⚠️ কথা বোঝা যায়নি বা নয়েজ ছিল।")
                return "IGNORE", 200

            if "সামনে" in text: return "CMD:FRONT", 200
            if "পেছনে" in text or "পিছনে" in text: return "CMD:BACK", 200
            if "ডানে" in text or "ডান দিকে" in text: return "CMD:RIGHT", 200
            if "বামে" in text or "বাম দিকে" in text: return "CMD:LEFT", 200
            if "থামো" in text or "দাঁড়াও" in text or "স্টপ" in text: return "CMD:STOP", 200
            if "ঘুরে" in text or "সারা রুম" in text: return "CMD:WANDER", 200

            print("🧠 Generating AI Response...")
            prompt = (f"The user said in Bengali: '{text}'. "
          "CRITICAL RULE: If the user asks you to move, you MUST reply ONLY with the exact command code. No extra words! "
          "1. If user asks to walk (e.g. 'হাঁটো') -> reply ONLY 'CMD:WALK' "
          "2. If user asks to raise right hand (e.g. 'ডান হাত') -> reply ONLY 'CMD:RIGHT_HAND' "
          "3. If user asks to raise left hand (e.g. 'বাম হাত') -> reply ONLY 'CMD:LEFT_HAND' "
          "4. If user asks to raise both hands (e.g. 'দুই হাত') -> reply ONLY 'CMD:BOTH_HANDS' "
          "Do NOT write things like 'এই তো হাত তুললাম'. Just the CMD code. "
          "5. For regular questions (e.g. 'কেমন আছো?'), answer normally in 2-3 playful Bengali sentences.")
            
            ai_reply = get_ai_response(prompt)
            print(f"🤖 AI says: {ai_reply}")
            
            if "CMD:" in ai_reply:
                return ai_reply, 200
            else:
                # -------- নতুন যোগ করা ছেলের কণ্ঠের লজিক --------
                async def generate_male_voice():
                    # 'bn-BD-PradeepNeural' হলো বাংলাদেশি ছেলের কণ্ঠ
                    communicate = edge_tts.Communicate(ai_reply, "bn-BD-PradeepNeural")
                    await communicate.save("reply.mp3")
                
                asyncio.run(generate_male_voice())
                return "PLAY", 200
                # -----------------------------------------------
            
    except Exception as e:
        print(f"❌ Server Error: {e}")
        return "IGNORE", 200

if __name__ == '__main__':
    print("🚀 Server is running on port 5000...")
    app.run(host='0.0.0.0', port=5000)
