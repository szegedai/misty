import cv2
from PIL import Image
from huclip_the_text.model.clip import KeywordCLIP
from stt import SpeechToTextAPI
import tts
import stt
import signal
import asyncio
import time

from mistyPy.Robot import Robot
from mistyPy.Events import Events


model = KeywordCLIP()
url = 'http://10.2.8.5'  # TODO URL
question = 'Ember vagy alma van a képen?'
again = 'Ha szeretnél új kérdést feltenni akkor simogasd meg újra a fejem. Ha nem szeretnél tovább játszani érj az államhoz.'


def default_image_classification_algorithm(image, misty, message):
    #cv2.imshow('CAPTURED FRAME', image)

    misty.ChangeLED(255, 255, 0)
    best_answer, probability, all_answer = model.evaluate(Image.fromarray(image), message)
    # TODO speech_to_text(url, '')

    misty.ChangeLED(0, 255, 0)
    misty.DisplayImage('e_Joy.jpg')

    tts.synthesize_text_to_robot(misty, best_answer + ' van előttem', 'output.wav')
    time.sleep(5)
    misty.DisplayImage('e_DefaultContent.jpg')
    tts.synthesize_text_to_robot(misty, again, 'again.wav')

def speech_to_text(url, filename):
    stt_api = SpeechToTextAPI(url)
    signal.signal(signal.SIGALRM, stt.outoftime_handler)
    signal.alarm(10)
    try:
        if asyncio.run(stt_api.ws_check_connection()):
            res = asyncio.run(stt_api.ws_wav_recognition(filename))
            print("Result: ", res.split(";")[1])
            return res
        else:
            print("Unable to establish connection to the ASR server!")
            return ''
    except Exception as e:
        print("ERROR")

