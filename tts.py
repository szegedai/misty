import sys
import wave
import requests  # https://docs.python-requests.org/en/latest/user/quickstart/
import contextlib
from base64 import b64encode, b64decode

from mistyPy.Robot import Robot


class TextToSpeechAPI:
    # NG male voice, MK female voice

    def __init__(self, tts_uri, speaker="MK"):
        self.uri = tts_uri
        self.speaker = speaker

    def check_connection(self):
        # Checking if the URI is available
        r = requests.head(self.uri)
        if r.status_code == 200:
            return True
        else:
            return False

    def length_audio(self, fname="response.wav"):

        with contextlib.closing(wave.open(fname, 'r')) as f:
            frames = f.getnframes()
            rate = f.getframerate()
            duration = frames / float(rate)
            print(duration)
            return duration

    def synthesize_text_to_wav(self, text, misty, fname="response.wav"):
        print(f"Synthesizing text: {text}")
        payload = {"speaker": self.speaker, "q": text}
        # Sending the get request
        result = requests.get(self.uri, params=payload)

        # Was that successful?
        print(f"Response STATUS CODE: {result.status_code}")

        if result.status_code == requests.codes.ok:

            base64_str = str(b64encode(result.content), 'ascii', 'ignore')

            with open(fname, "wb") as wav_f:
                wav_f.write(result.content)

            with contextlib.closing(wave.open(fname, 'r')) as f:
                frames = f.getnframes()
                rate = f.getframerate()
                duration = frames / float(rate)

            misty.SaveAudio(fname, base64_str, True, True)
            return duration
            # THIS PART CAN BE OMITTED!
            # Source: https://stackoverflow.com/questions/17657103/how-to-play-wav-file-in-python
            # Play the file just to test it immediately
            # import playsound
            # playsound.playsound(fname)



if __name__ == "__main__":
    # if len(sys.argv) > 2:
    #     tts_uri = sys.argv[1]
    #     text = sys.argv[2]
    #
    #     tts_api = TextToSpeechAPI(tts_uri)
    #     if tts_api.check_connection:
    #         tts_api.synthesize_text_to_wav(text)
    #     else:
    #         print("Error! Unable to connect to the TTS server!")
    misty = Robot('192.168.0.53')
    # tts = TextToSpeechAPI("http://szeged:s23936@cyrus.tmit.bme.hu/hmmtts2/synth_hmm_wav.php", "MK")
    tts = TextToSpeechAPI("https://chatbot-rgai3.inf.u-szeged.hu/flask/tts", "MK")

    t = tts.synthesize_text_to_wav("Hello, Éva vagyok", misty, 'response.wav')
    print(t)
