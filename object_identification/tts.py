import sys
import requests # https://docs.python-requests.org/en/latest/user/quickstart/
from base64 import b64encode, b64decode

class TextToSpeechAPI():
    uri = ""
    speaker = "MK" # NG male voice, MK female voice
    
    def __init__(self, tts_uri):
        self.uri = tts_uri


    def check_connection(self):
        # Checking if the URI is available
        r = requests.head(tts_uri)
        if (r.status_code == 200):
            return True
        else:
            return False
    
    def synthesize_text_to_wav(self, text):
        print(f"Synthesizing text: {text}")
        payload = {"speaker" : self.speaker, "q" : text}
        
        # Sending the get request
        r = requests.get(self.uri, params=payload)
        
        # Was that successful?
        print(f"Response STATUS CODE: {r.status_code}")
        
        if (r.status_code == requests.codes.ok):
        
            # Getting rid of non alphanumeric chars - in order to create manageable file names
            #import re, string
            #re_pattern = re.compile("[\W_]+", re.UNICODE)
            #wav_f_name = re_pattern.sub("", sys.argv[1]) + ".wav"
            wav_f_name = "mistynek.wav"
           
            # Writing the response to file
            with open(wav_f_name, "wb") as wav_f:
                wav_f.write(r.content)
        
            # THIS PART CAN BE OMITTED!
            # Source: https://stackoverflow.com/questions/17657103/how-to-play-wav-file-in-python      
            # Play the file just to test it immediately
            #import playsound
            #playsound.playsound(wav_f_name)


def synthesize_text_to_robot(misty, text, file_name):

    result = requests.get("https://chatbot-rgai3.inf.u-szeged.hu/flask/tts", {"q": text})

    base64_str = str(b64encode(result.content), 'ascii', 'ignore')

    print(misty.SaveAudio(file_name, base64_str, True, True))


if __name__ == "__main__":
    if(len(sys.argv) > 2):
        tts_uri = sys.argv[1]
        text = sys.argv[2]
        
        tts_api = TextToSpeechAPI(tts_uri)
        if tts_api.check_connection:    
            tts_api.synthesize_text_to_wav(text)
        else:
            print("Error! Unable to connect to the TTS server!")
        
