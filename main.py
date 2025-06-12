import speech_recognition as sr
import pyttsx3 
import pyaudio
import numpy as np
import chatgpt
import gui_manager as gm
import time
import csv
import threading 
import db
import server

#Set values for audio detection
CHUNK = 1024
RATE = 44100
THRESHOLD = 18000

#Current time
seconds = time.time()
CURRENT_TIME = time.ctime(seconds)

#Initialize audio detector
p = pyaudio.PyAudio()

stream = p.open(
    format=pyaudio.paInt16,
    channels=1,
    rate=RATE,
    input=True,
    frames_per_buffer=CHUNK
)

# Initialize the recognizer 
r = sr.Recognizer() 
r.pause_threshold = 1.2

def SpeakText(command):
    """Enhanced TTS function that returns duration info"""
    engine = pyttsx3.init()
    
    # Get speech rate to estimate duration more accurately
    rate = engine.getProperty('rate')
    words = len(command.split())
    # Estimate duration: rate is usually words per minute
    estimated_duration = (words / (rate / 60)) if rate > 0 else len(command) * 0.1  #not sure this needs to exists
    
    engine.say(command) 
    engine.runAndWait()
    
    return estimated_duration

def check_event():
    with open('reminders.csv', 'r', newline='') as csvfile:
        reader = csv.reader(csvfile)
        
        for row in reader:
            if row[1] in CURRENT_TIME:
                return row[0]
        
def get_audio():    
    try:
        with sr.Microphone() as source2:
            r.adjust_for_ambient_noise(source2, duration=0.1)
            audio2 = r.listen(source2)
            MyText = r.recognize_google(audio2)
            MyText = MyText.lower()
            
            if MyText.split(" ")[0] == "alexa":
                return MyText
            
    except sr.RequestError as e:
        print("Could not request results".format(e))
        
    except sr.UnknownValueError:
        pass

def audio_loop():
    count = 0
    try:
        while True:
            count += 1
            
            data = np.frombuffer(
                stream.read(CHUNK, exception_on_overflow=False),
                dtype=np.int16
            )
            
            volume = np.linalg.norm(data)
            print(volume)
            
            if volume > THRESHOLD and count > 10:
                # Regular animation for "Listening..."
                g.update("Listening...", sync_with_speech=False)
                print("Detected loud noise")
                
                while(1):
                    prompt = get_audio()

                    if prompt == "alexa stop":
                        count = 0
                        break

                    if not prompt == None and prompt.split()[0] == "alexa":
                        # Show the prompt without speech sync
                        g.update(prompt, sync_with_speech=False)
                        
                        # Show "Thinking..." without speech sync
                        g.update("Thinking...", sync_with_speech=False)

                        response = chatgpt.chat_with_deepseek(prompt)  #can change to chat gpt
                        
                        # Animate response synchronized with speech
                        # Use word_mode=True for word-by-word animation
                        g.update(response, sync_with_speech=True, word_mode=False)
                        
                        # Speak the text
                        SpeakText(response)
                        break
                    
    except KeyboardInterrupt:
        pass
    finally:
        stream.start_stream()
        stream.close()
        p.terminate()

if __name__ == "__main__":
    #Database and fast api server
    db.init_db()
    server.run_api()
    #GUI manager
    g = gm.GUIService()
    threading.Thread(target=audio_loop, args=(), daemon=True).start()
    g.start()
