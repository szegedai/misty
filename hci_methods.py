import cv2
from TextToSpeech import TextToSpeechAPI
import time
import base64
import asyncio
import SpeechToText
# from RPS.detection import _grab_mid
from huclip_the_text.model.clip import KeywordCLIP
from PIL import Image

stt = SpeechToText.SpeechToTextAPI("wss://chatbot-rgai3.inf.u-szeged.hu/socket")
model = KeywordCLIP()


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
