import cv2
from tts import TextToSpeechAPI
import time
import base64
import asyncio
import SpeechToText
# from RPS.detection import _grab_mid
from huclip_the_text.model.clip import KeywordCLIP
from PIL import Image

stt = SpeechToText.SpeechToTextAPI("wss://chatbot-rgai3.inf.u-szeged.hu/socket")
model = KeywordCLIP()

#
# def show_rps_frame(image):
#     im_mid = _grab_mid(image, 256, 256)
#     cv2.imshow('VIDEO', im_mid)
#     cv2.waitKey(1)


# def recognizer(misty, message):
#     time.sleep(2)
#     misty.SetBlinking(True)
#     data = misty.TakePicture(base64=True, fileName="test_photo", width=1440, height=1080)
#     misty.SetBlinking(False)
#     # print()
#     with open("file.jpg", "wb") as pic:
#         pic.write(base64.b64decode(data.json()['result']['base64']))
#     image = cv2.imread('file.jpg')
#
#     misty.ChangeLED(255, 255, 0)
#     best_answer, probability, all_answer = model.evaluate(Image.fromarray(image), message)
#     # TODO speech_to_text(url, '')
#
#     misty.ChangeLED(0, 255, 0)
#     misty.DisplayImage('e_Joy.jpg')
#     print("hello")
#     length_of_audio = tts.synthesize_text_to_wav(best_answer + ' van előttem', misty, 'response.wav')
#     print(length_of_audio)
#     time.sleep(length_of_audio)
#     misty.DisplayImage('e_DefaultContent.jpg')
#     length_of_audio = tts.synthesize_text_to_wav(again, misty, 'response.wav')
#     time.sleep(length_of_audio)


def default_image_classification_algorithm(image):
    # Write your own method here...
    # At the moment we are just displaying the image

    # HAMMER Classification Algorithm
    # print("Hmm... it looks like a nail!")

    cv2.imshow('VIDEO', image)
    cv2.waitKey(1)


def captouch_callback(data):
    print("captouch")


def exit_function(misty):
    # Reset the robot's default state
    # IMPORTANT: If you have started any audio recordings, please stop them here etc.
    if misty is not None:
        misty.UnregisterAllEvents()
        misty.DisplayImage("e_DefaultContent.jpg", 1)
        misty.StopAvStreaming()
        misty.DisableAvStreamingService()
        misty.StopRecordingAudio()
        misty.StopKeyPhraseRecognition()
        misty.StopAudio()

        time.sleep(1)

    print("Exiting program.")


def remove_closed_events(misty):
    events_to_remove = []

    for event_name, event_subscription in misty.active_event_registrations.items():
        if not event_subscription.is_active:
            events_to_remove.append(event_name)

    for event_name in events_to_remove:
        print(f"Event connection has closed for event: {event_name}")
        misty.UnregisterEvent(event_name)
