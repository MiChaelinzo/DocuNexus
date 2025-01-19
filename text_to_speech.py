import pyttsx3

def text_to_speech(text, language):
    engine = pyttsx3.init()
    engine.setProperty('voice', language)
    engine.say(text)
    engine.runAndWait()
