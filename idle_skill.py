# idle skill (and currently skill manager and conversational skill) for misty
# ones we tap his head, she starts to listen for the speech around her, and after she hears the
# Éva <sentence longer than 2 words>, if it is possible, she starts the wanted skill, it can either be the recoginzer or
# the rock paper scissors.
# some of this skill was based on misty developers' moveToSound and followFace js skills
# mistyPy https://github.com/MistyCommunity/Wrapper-Python
# misty documentation: https://docs.mistyrobotics.com/


import sys
import traceback
import time
import base64
import asyncio

from mistyPy.Robot import Robot
from mistyPy.Events import Events

import Recorder
import globals
from data_stream import init
from data_stream import datastream
from rps_cvzone import *
from hci_methods import *
from TextToSpeech import TextToSpeechAPI
from SpeechToText import SpeechToTextAPI

misty = None

stt = SpeechToTextAPI("wss://chatbot-rgai3.inf.u-szeged.hu/socket")
tts = TextToSpeechAPI("https://chatbot-rgai3.inf.u-szeged.hu/flask/tts", "MK")


# In the code below asyncio creates a loop, so we can run asynchronous tasks, and a Recorder which connects to the
# speech to text server and the default microphone
def connection_to_stt():
    globals.loop = asyncio.new_event_loop()
    asyncio.set_event_loop(globals.loop)
    globals.loop.run_until_complete(init(stt))

    stream_params = Recorder.StreamParams()
    globals.recorder = Recorder.Recorder(stream_params)
    globals.recorder.create_recording_resources()
    globals.first_contact = True


# initializing variables, registering events and starting services required for the idle skill
def init_variables_and_events():
    # setting misty head position to look forward
    misty.MoveArms(leftArmPosition=90, rightArmPosition=90, duration=0.1)
    misty.MoveHead(pitch=0, roll=0, yaw=0, velocity=1, duration=1)
    misty.DisplayImage("e_DefaultContent.jpg")
    # initializing global variables
    globals.idle_skill = True
    globals.start_external = False
    globals.waiting_for_response = False
    globals.first_contact = True
    globals.return_to_idle = False
    globals.length_of_audio = 0.0
    globals.searching_for_face = True

    misty.ChangeLED(0, 0, 0)

    misty.UnregisterAllEvents()
    misty.EnableCameraService()
    # Starting captouch event, and adding the callback that needed to be called
    misty.RegisterEvent("captouch", Events.TouchSensor, callback_function=captouch_callback, debounce=1000,
                        keep_alive=True)


# callback for the captouch event
# we use this to start the idle_skill's speech recognition, so we can select the games provided by misty
def captouch_callback(data):
    print(data['message']['sensorPosition'])
    # When we first start the captouch event it will say the following text
    if globals.first_contact and (data['message']['sensorPosition'] == "HeadFront"):
        globals.length_of_start_audio = tts.synthesize_text_to_wav(
            "Hello, én Éva vagyok! Kettő játékot tudsz velem játszani, "
            "kő papír ollót vagy mutatsz 2 tárgyat megkérdezed mit mutatsz,"
            " és én eldöntöm, hogy mi van a kezedben."
            "Pittyenés után kérlek mondd mivel szeretnél játszani", misty)
        globals.first_contact = False
    # Play Awe, its a cute feature if we touch the chin
    if data['message']['sensorPosition'] == "Chin":
        misty.PlayAudio("s_Awe2.wav")
        misty.DisplayImage("e_EcstacyStarryEyed.jpg")
        time.sleep(5)
        misty.DisplayImage("e_DefaultContent.jpg")


# this function stops the idle skill and starts an external skill based on the skill parameter
# we pass the name of the skill we want to start as a parameter
def start_external_skill(skill=""):
    stop_idle_skill()
    time.sleep(1)
    print(f"starting {skill} skill")

    if skill == "ph_rps":
        rps_start_skill()
    elif skill == "ph_recognizer":
        recognizer_start_skill()

    print("restarting idle_skill")
    start_idle_skill(misty, False)


# Voice recording function that recognizes the voice until the wanted format is provided
# the wanted format: Éva {any text, but needed to be longer than 3 word Éva included}
# This can be improved with spacy.
def recording():
    data_stream = datastream(globals.recorder, stt)
    try:
        misty.ChangeLED(200, 0, 0)
        # This will run until, the format is good
        res = globals.loop.run_until_complete(asyncio.gather(data_stream, stt.message_listener()))
        print(res[1])
        misty.ChangeLED(0, 200, 0)
        # This was the error handling, which than turned out as License problem.
        if "error|recog-error" in res[1]:
            misty.DisplayImage("e_Disoriented.jpg")
            tts.synthesize_text_to_wav("Várj egy kicsit, elvesztettem a fonalat.", misty)
            misty.MoveHead(-5, 0, 0, 4, 0.1)
            globals.loop.run_until_complete(stt.ws_stream_close())
            time.sleep(1)
            connection_to_stt()
            length = tts.synthesize_text_to_wav("meglett a fonál", misty)
            time.sleep(length)
            misty.DisplayImage("e_DefaultContent.jpg")
            recording()
        else:
            misty.ChangeLED(0, 200, 0)
            respond(str.lower(res[1]))

    except Exception as e:
        print("Recording error from idle_skill: ", e)


# this function starts the idle skill, and runs until gets aborted with ctrl + C or the stop button if started from IDE
def start_idle_skill(misty_robot, calibration=False):
    global misty
    globals.init()
    misty = misty_robot
    misty.MoveHead(-6, 0, 0, 2)
    init_variables_and_events()

    print("idle_skill STARTED")
    # this is the main loop of the skill
    # misty.StartFaceRecognition()
    while globals.idle_skill:
        time.sleep(0.1)

        if misty is not None:

            if not globals.first_contact:
                start_time = time.time()

                globals.loop = asyncio.new_event_loop()
                asyncio.set_event_loop(globals.loop)
                globals.loop.run_until_complete(init(stt))

                stream_params = Recorder.StreamParams()
                globals.recorder = Recorder.Recorder(stream_params)
                globals.recorder.create_recording_resources()
                print("len start audio: ", globals.length_of_start_audio)

                if (time.time() - start_time) <= globals.length_of_start_audio:
                    length = globals.length_of_start_audio - round(time.time() - start_time, 2)
                    while length >= 5:
                        globals.loop.run_until_complete(stt.ping_send())
                        time.sleep(5)
                        length = length - 5

                    if length > 0:
                        time.sleep(length)

                misty.PlayAudio("s_SystemWakeWord.wav")
                globals.searching_for_face = False
            if not globals.searching_for_face:
                # misty.StopFaceRecognition()
                globals.waiting_for_response = True
                recording()

                globals.searching_for_face = True


# this function is supposed to make Misty respond appropriately to the user
# if the speech_to_text_result contains "papir" or "ismer" the skill starts
# otherwise misty repeats what she heard
def respond(speech_to_text_result=""):
    print(speech_to_text_result)

    misty.DisplayImage("e_Love.jpg")
    if "papír" in speech_to_text_result:
        start_external_skill("ph_rps")
    if "ismer" in speech_to_text_result:
        start_external_skill("ph_recognizer")
    else:
        print("Nem értette")
        globals.length_of_audio = tts.synthesize_text_to_wav(f"Azt hallottam, hogy: {speech_to_text_result}", misty,
                                                             "response.wav")
        time.sleep(globals.length_of_audio)

    globals.waiting_for_response = False


# this function stops the idle skill
# it unregisters all events, stop any services used in the skill and stops misty's movement
# we call this when we want to switch to a different skill
def stop_idle_skill():
    globals.idle_skill = False
    misty.DisplayImage("e_DefaultContent.jpg")
    misty.Halt()
    time.sleep(1)
    print("IDLE_SKILL_STOPPED")


# This is the rock paper scissors game's main function which returns True if we got bored playing it
def rps_start_skill():
    global misty
    globals.return_to_idle = False
    globals.length_of_audio = tts.synthesize_text_to_wav("Elindult a kő papír olló játék, ha készen állsz, mondd,"
                                                         " hogy Éva szeretnék játszani ellened egyet", misty,
                                                         "response.wav")
    time.sleep(globals.length_of_audio)
    print("rps skill started")
    # misty.UnregisterAllEvents()
    misty.MoveArms(leftArmPosition=90, rightArmPosition=0, duration=0.1)
    # misty.MoveHead(pitch=0, roll=0, yaw=0)
    try:
        if misty is not None:
            misty.ChangeLED(255, 255, 0)

        rps_recording()
        while True:
            time.sleep(1)
            if globals.return_to_idle:
                globals.return_to_idle = False
                globals.loop.run_until_complete(stt.ws_stream_close())

                time.sleep(2)
                return True

    except KeyboardInterrupt:
        time.sleep(2)
        return True

    except Exception as e:
        print("Exception in user code: ")
        print("-" * 60)
        traceback.print_exc(file=sys.stdout)
        print("-" * 60)

    finally:
        return True

# same as recording only this one calls the rps respond
def rps_recording():
    data_stream = datastream(globals.recorder, stt)
    try:
        misty.ChangeLED(200, 0, 0)
        res = globals.loop.run_until_complete(asyncio.gather(data_stream, stt.message_listener()))
        print(res[1])
        if "error|recog-error" in res[1]:
            misty.DisplayImage("e_Disoriented.jpg")
            tts.synthesize_text_to_wav("Várj egy kicsit, elvesztettem a fonalat.", misty)
            misty.MoveHead(-5, 0, 0, 4, 0.1)
            globals.loop.run_until_complete(stt.ws_stream_close())
            time.sleep(1)
            connection_to_stt()
            length = tts.synthesize_text_to_wav("meglett a fonál", misty)
            time.sleep(length)
            misty.DisplayImage("e_DefaultContent.jpg")
            rps_recording()

        else:
            misty.ChangeLED(0, 200, 0)
            rps_respond(str.lower(res[1]))

    except Exception as e:
        print("Exception in user code: ", e)


# Based on the text from the speech it stops working or starts the game
def rps_respond(speech_to_text_result=""):
    globals.return_to_idle = False
    matches = ["egyet", "játszunk", "még", "játszani", "szeretnék"]
    rps_exiting = ["kilép", "befejez", "vége", "abba", "lép"]

    misty.DisplayImage("e_Thinking2.jpg")
    if any(x in speech_to_text_result for x in rps_exiting):
        globals.return_to_idle = True

    elif any(x in speech_to_text_result for x in matches):
        rps()

    else:
        print(speech_to_text_result)
        misty.DisplayImage("e_Disoriented.jpg")
        globals.length_of_audio = tts.synthesize_text_to_wav("Nem értettelek, kérlek ismételd meg!", misty,
                                                             "response.wav")
        time.sleep(globals.length_of_audio)
        rps_recording()


# Takes a picture and with cvzone's hand detector you get all the necessary finger position called landmarks
# and with those positions we can calculate which of the three moves the player is showing.
def get_human_move():
    data = misty.TakePicture(base64=True, fileName="test_photo", width=1440, height=1080)
    with open("file.jpg", "wb") as pic:
        pic.write(base64.b64decode(data.json()['result']['base64']))

    return image_landmarks(file_name="file.jpg")


# Misty takes a screenshot and by that detects what the player showed, and also randomly selects a move
def rps():
    globals.length_of_audio = tts.synthesize_text_to_wav("Kőőőőő, papííííír, olllllló", misty, "response.wav")

    # Wave arms three times
    for _ in range(3):
        misty.MoveArm("right", 30, duration=0.5)
        time.sleep(1)
        misty.MoveArm("right", -29, duration=1)
        time.sleep(1)

    misty.MoveArm("right", 0, duration=0.5)

    # Detect the player's move and pick a random move for Misty
    human_move = get_human_move()
    misty_move = get_random_move()

    while human_move is None:
        globals.length_of_audio = tts.synthesize_text_to_wav("kérlek mutasd újra, mert nem láttam megfelelően a kezed",
                                                             misty,
                                                             "response.wav")
        time.sleep(globals.length_of_audio)
        for _ in range(3):
            misty.MoveArm("right", 30, duration=1)
            misty.MoveArm("right", -29, duration=1)
        human_move = get_human_move()
    # Show Misty's move
    # Images are preloaded on the robot
    misty.DisplayImage(f"{misty_move}_disp.png")

    # Determine the winner and assemble the text that announces the winner
    misty_move_hun = f"Én {get_move_hun(misty_move)} választottam."
    human_move_hun = f"Te {get_move_hun(human_move)} választottál."
    winner_hun = ""

    winner = get_winner(human_move, misty_move)
    expression = ""
    if winner == 2:
        print("Misty wins!")
        winner_hun = "Én nyertem."
        expression = "e_EcstacyStarryEyed.jpg"
    elif winner == 0:
        print("Draw!")
        winner_hun = "Döntetlen."
        expression = "e_Surprise.jpg"
    elif winner == 1:
        print("You won")
        winner_hun = "Te nyertél."
        expression = "e_Rage3.jpg"

    # Announce Misty's move and winner
    misty_move_and_winner_announcement_hun = f"{misty_move_hun} {human_move_hun} {winner_hun}"
    print(misty_move_and_winner_announcement_hun)

    globals.length_of_audio = tts.synthesize_text_to_wav(misty_move_and_winner_announcement_hun, misty, "response.wav")
    misty.DisplayImage(expression)
    time.sleep(globals.length_of_audio)

    # Reset Misty's face
    misty.DisplayImage("e_DefaultContent.jpg")

    # Prompt the user to play again or stop playing

    globals.length_of_audio = tts.synthesize_text_to_wav(
        "Kérlek jelezd, ha szeretnél még egyet játszani.", misty, "response.wav")
    time.sleep(globals.length_of_audio)

    rps_recording()


thanks = 'Köszönöm a játékot'
input_text = 'Kérlek mutass egy tárgyat és kérdezd meg, hogy mit mutatsz, például Éva ez egy alma vagy körte?'
again = 'Tegyél fel még egy kérdést, ha még szeretnél játszani vagy' \
        ' ha nem szeretnél tovább játszani mondd, hogy fejezzem be.'

# starts game or returns to idle skill based on text that comes from the speech to text
def recognizer_respond(speech_to_text_result):
    print(speech_to_text_result)
    recog_exiting = ["kilép", "fejez", "vége", "abba", "lép"]
    if any(x in speech_to_text_result for x in recog_exiting):
        globals.length_of_audio = tts.synthesize_text_to_wav(thanks, misty, "response.wav")

        time.sleep(globals.length_of_audio)
        globals.return_to_idle = True
    elif "vagy" in speech_to_text_result:
        print("még egy játék!")
        recognizer(speech_to_text_result)
        recognizer_recording()
    else:
        print("nem értettem, próbáld újra")
        recognizer_recording()


# Takes a picture and provides it to the model, with the text from the recognizer, in which we ask what is in our hand,
# what is shown by the player
def recognizer(message):
    time.sleep(2)
    misty.SetBlinking(True)
    data = misty.TakePicture(base64=True, fileName="test_photo", width=1440, height=1080)
    misty.SetBlinking(False)
    with open("file.jpg", "wb") as pic:
        pic.write(base64.b64decode(data.json()['result']['base64']))
    image = cv2.imread('file.jpg')

    misty.ChangeLED(255, 255, 0)
    best_answer, probability, all_answer = model.evaluate(Image.fromarray(image), message)

    misty.ChangeLED(0, 255, 0)
    misty.DisplayImage('e_Joy.jpg')
    print("hello")
    globals.length_of_audio = tts.synthesize_text_to_wav(best_answer + ' van előttem', misty, 'response.wav')
    print(globals.length_of_audio)
    time.sleep(globals.length_of_audio)
    misty.DisplayImage('e_DefaultContent.jpg')
    globals.length_of_audio = tts.synthesize_text_to_wav(again, misty, 'response.wav')
    time.sleep(globals.length_of_audio)


# This is the same as recording, just in this we call the recognizer respond.
def recognizer_recording():
    data_stream = datastream(globals.recorder, stt)
    try:
        misty.ChangeLED(200, 0, 0)

        res = globals.loop.run_until_complete(asyncio.gather(data_stream, stt.message_listener()))

        misty.ChangeLED(0, 200, 0)

        if "error|recog-error" in res[1]:
            misty.DisplayImage("e_Disoriented.jpg")
            tts.synthesize_text_to_wav("Várj egy kicsit, elvesztettem a fonalat.", misty)
            misty.MoveHead(-5, 0, 0, 4, 0.1)
            globals.loop.run_until_complete(stt.ws_stream_close())
            time.sleep(1)
            connection_to_stt()
            length = tts.synthesize_text_to_wav("meglett a fonál", misty)
            time.sleep(length)

            misty.DisplayImage("e_DefaultContent.jpg")

            recognizer_recording()
        else:
            recognizer_respond(str.lower(res[1]))

    except KeyboardInterrupt as e:
        print(e)

# This is the core of the recognizer skill, this will return True if we got bored or want to get back to idle skill
def recognizer_start_skill():
    global misty
    globals.return_to_idle = False
    misty.MoveHead(-5, 0, 0, velocity=4, duration=0.1)
    try:
        globals.length_of_audio = tts.synthesize_text_to_wav(input_text, misty, "response.wav")
        globals.loop.run_until_complete(stt.ping_send())
        time.sleep(globals.length_of_audio)
        print("recognizer skill started")
        if misty is not None:
            misty.ChangeLED(255, 0, 255)

            recognizer_recording()

        while True:
            time.sleep(1)
            if globals.return_to_idle:
                globals.return_to_idle = False
                time.sleep(2)
                globals.loop.run_until_complete(stt.ws_stream_close())
                return True
    except KeyboardInterrupt:
        globals.return_to_idle = True

    except Exception as e:
        print(e)
        connection_to_stt()
        recognizer_recording(globals.recorder)
    finally:
        return True


if __name__ == "__main__":
    print("start")
    start_time = time.time()

    print("Time: ", time.time() - start_time)
    try:
        if len(sys.argv) > 1:
            misty_ip_address = sys.argv[1]

        else:
            misty_ip_address = "10.2.8.5"
        misty = Robot(misty_ip_address)

        misty.UnregisterAllEvents()
        start_idle_skill(misty, False)

    except Exception as ex:
        print("Exception in user code:")
        print("-" * 60)
        traceback.print_exc(file=sys.stdout)
        print("-" * 60)

    except KeyboardInterrupt:
        # when exiting, stop every running service, unregister events, stop motors
        misty.StopAvStreaming()
        misty.StopFaceRecognition()
        misty.UnregisterAllEvents()
        misty.ChangeLED(0, 0, 0)
        misty.DisplayImage("e_DefaultContent.jpg")
        misty.StopKeyPhraseRecognition()
        misty.StopRecordingAudio()
        misty.Halt()
        print("face rec stopped, unregistered all events")
