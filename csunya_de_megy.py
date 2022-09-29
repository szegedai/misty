# idle skill (and currently skill manager and conversational skill) for misty
# misty moves her head around, looking for faces, if she finds one, she tries to follow it
# once she sees a face she listens to the "Hey, Misty!" keyword
# after she recognises the keyphrase, she listens to speech
# at the end of speech she attempts to recognise the intent and respond based on that (currently intent recognition is
# not implemented yet)
# she can also switch skills based on the intent (intent recognition not implemented, but skill switching is working)
# if misty doesn't see a face, she listens to the "Hey, Misty!" keyword
# when she hears it, she starts listening to speech for a few seconds and attempts to turn towards the sound
# some of this skill was based on misty developers' moveToSound and followFace js skills
# moveToSound: https://github.com/CPsridharCP/MistySkills/blob/master/ExampleSkills/Advanced/moveToSound/moveToSound.js
# followFace: https://github.com/CPsridharCP/MistySkills/blob/master/ExampleSkills/Advanced/followFace/followFace.js
# misty documentation: https://docs.mistyrobotics.com/

from tts import TextToSpeechAPI
import time
import random
import base64
import asyncio
import numpy as np
import dateutil.parser
import sys
import traceback
import Recorder
import SpeechToText
import globals
from main import init
from main import datastream
from rps_cvzone import *
from hci_methods import *
from statistics import mean
from mistyPy.Robot import Robot
from mistyPy.Events import Events
from datetime import datetime, timezone
from mistyPy.EventFilters import EventFilters
import hci_methods

# LOOP = None
length_of_start_audio = 0
searching_for_face = None
head_yaw = None
head_pitch = None
yaw_right = None
yaw_left = None
pitch_up = None
pitch_down = None
misty = None
face_rec_event_status = None
idle_skill = None
date_time_of_last_face_detection = None
testing_skill = True
skill_finished = True
restart_skill = False
start_external = False
skill_to_start = ""
waiting_for_response = False
first_contact = True
seconds_since_last_detection = 0
# move to sound változók
turn_in_progress = False
looked_at = None
robot_yaw = None
head_yaw_for_turning = None
_1b = None
_2b = None
vector = None
# RECORDER = None
degree_list = []
stt = SpeechToText.SpeechToTextAPI("wss://chatbot-rgai3.inf.u-szeged.hu/socket")

tts = TextToSpeechAPI("http://szeged:s23936@cyrus.tmit.bme.hu/hmmtts2/synth_hmm_wav.php")


def connection_to_stt():
    globals.init()
    globals.LOOP = asyncio.new_event_loop()
    asyncio.set_event_loop(globals.LOOP)
    globals.LOOP.run_until_complete(init(stt))

    stream_params = Recorder.StreamParams()
    globals.RECORDER = Recorder.Recorder(stream_params)
    globals.RECORDER.create_recording_resources()
    first_contact = True


# initializing variables, registering events and starting services required for the idle skill
def init_variables_and_events():
    global searching_for_face, head_yaw, head_pitch, yaw_right, yaw_left, pitch_up, pitch_down, misty, looked_at, \
        robot_yaw, _1b, _2b, vector, head_yaw_for_turning, face_rec_event_status
    global idle_skill, skill_finished, restart_skill, start_external, waiting_for_response
    # setting misty head position
    misty.MoveArms(leftArmPosition=90, rightArmPosition=90, duration=0.1)
    misty.MoveHead(pitch=0, roll=0, yaw=0)
    misty.DisplayImage("e_DefaultContent.jpg")
    # initializing variables
    idle_skill = True
    restart_skill = False
    start_external = False
    waiting_for_response = False
    # set skill finished False, so the while loop in the main function doesn't keep calling start_idle_skill
    skill_finished = False

    misty.MoveHead(0, 0, 0, None, 1)
    searching_for_face = True
    misty.ChangeLED(0, 0, 0)

    misty.UnregisterAllEvents()
    # starting services
    misty.EnableCameraService()
    # # event for bump sensor and cap touch sensor
    # misty.RegisterEvent("bump_sensor_pressed", Events.BumpSensor, callback_function=bump_callback, debounce=10,
    #                     keep_alive=True)
    misty.RegisterEvent("captouch", Events.TouchSensor, callback_function=captouch_callback, debounce=1000,
                        keep_alive=True)


# callback for the captouch event
# we use this to restart the idle skill if something goes wrong
def captouch_callback(data):
    global restart_skill, first_contact, length_of_start_audio
    print(data['message']['sensorPosition'])
    if first_contact and (data['message']['sensorPosition'] == "HeadFront"):
        length_of_start_audio = tts.synthesize_text_to_wav(
            # "Hello, én Éva vagyok! Kettő játékot tudsz velem játszani, "
            # "kő papír ollót vagy mutatsz 2 tárgyat megkérdezed mit mutatsz,"
            # " és én eldöntöm, hogy mi van a kezedben."
            "Pittyenés után kérlek mondd mivel szeretnél játszani", misty)
        first_contact = False
    if data['message']['sensorPosition'] == "Chin":
        misty.PlayAudio("s_Awe2.wav")
        misty.DisplayImage("e_EcstacyStarryEyed.jpg")
        time.sleep(5)
        misty.DisplayImage("e_DefaultContent.jpg")
        # time.sleep(length_of_audio)


# stop_idle_skill()
# time.sleep(1)

# start_idle_skill()


# callback for the bump_sensor_pressed event
# currently only used for testing purposes
# def bump_callback(data):
#     start_external_skill("ph_rps")


# this function stops the idle skill and sets the start_external variable to True
# we call this function when we want to start an external skill from the main loop
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


def recording():
    # global idle_skill
    # idle_skill=False
    # misty.StopFaceRecognition()
    data_stream = datastream(globals.RECORDER, stt)
    try:
        misty.ChangeLED(200, 0, 0)
        print("try")
        res = globals.LOOP.run_until_complete(asyncio.gather(data_stream, stt.message_listener()))
        print("KESZ")
        print(res[1])
        misty.ChangeLED(0, 200, 0)
        if "error|recog-error" in res[1]:
            misty.DisplayImage("e_Disoriented.jpg")
            tts.synthesize_text_to_wav("Várj egy kicsit, elvesztettem a fonalat.", misty)
            misty.MoveHead(-5, 0, 0, 4, 0.1)
            globals.LOOP.run_until_complete(stt.ws_stream_close())
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

        # recorder.close_recording_resources()
    # finally:
    #     recorder.close_recording_resources()


# this function starts the idle skill
def start_idle_skill(misty_robot, calibration=False):
    global searching_for_face, misty, turn_in_progress, face_rec_event_status
    global date_time_of_last_face_detection, idle_skill, waiting_for_response, seconds_since_last_detection

    misty = misty_robot
    misty.MoveHead(-6, 0, 0, 2)
    init_variables_and_events()

    print("idle_skill STARTED")
    # this is the main loop of the skill
    # misty.StartFaceRecognition()
    while idle_skill:
        time.sleep(0.1)

        if misty is not None:

            if not first_contact:
                start_time = time.time()

                globals.init()
                globals.LOOP = asyncio.new_event_loop()
                asyncio.set_event_loop(globals.LOOP)
                globals.LOOP.run_until_complete(init(stt))

                stream_params = Recorder.StreamParams()
                globals.RECORDER = Recorder.Recorder(stream_params)
                globals.RECORDER.create_recording_resources()
                print("len start audio: ", length_of_start_audio)

                if (time.time() - start_time) <= length_of_start_audio:
                    length = length_of_start_audio - round(time.time() - start_time, 2)
                    while length >= 5:
                        globals.LOOP.run_until_complete(stt.ping_send())
                        time.sleep(5)
                        length = length - 5

                    if length > 0:
                        time.sleep(length)

                misty.PlayAudio("s_SystemWakeWord.wav")
                searching_for_face = False
            if not searching_for_face:
                # misty.StopFaceRecognition()
                waiting_for_response = True
                recording()

                searching_for_face = True


# this function is supposed to make Misty respond appropriately to the user
# right now intent recognition is not implemented
# if the speech_to_text_result contains "minta" or "mint a" the sample skill starts
# otherwise misty repeats what she heard
def respond(speech_to_text_result=""):
    global waiting_for_response
    print(speech_to_text_result)

    # TODO: recognise the user's intent and answer or start a skill based on that
    # e.g.
    # if intent == "play rock paper scissors":
    #   start_external_skill("rps")
    misty.DisplayImage("e_Love.jpg")
    if "papír" in speech_to_text_result:
        start_external_skill("ph_rps")
    if "ismer" in speech_to_text_result:
        start_external_skill("ph_recognizer")
    else:
        print("Nem értette")
        length_of_audio = tts.synthesize_text_to_wav(f"Azt hallottam, hogy: {speech_to_text_result}", misty,
                                                     "response.wav")
        time.sleep(length_of_audio)
        # length_of_audio = tts.synthesize_text_to_robot(misty, "Nem értettem, kérlek mondd máshogy!", "response.wav")

    waiting_for_response = False
    # misty.StartFaceRecognition()


# this function is called when misty doesn't see a face and turning is not in progress
# misty moves her head randomly, trying to find a face
def look_side_to_side():
    print("looking for face...")

    global misty
    misty.DisplayImage("e_DefaultContent.jpg")

    if head_yaw > 0 and not turn_in_progress:
        misty.MoveHead(random.randint(-20, 0), 0, -40, None, 4)
        misty.DisplayImage("e_Thinking.jpg")
    elif head_yaw <= 0 and not turn_in_progress:
        misty.MoveHead(random.randint(-20, 0), 0, 40, None, 4)
        misty.DisplayImage("e_Thinking2.jpg")


# this function stops the idle skill
# it unregisters all events, stop any services used in the skill and stops misty's movement
# we call this when we want to switch to a different skill
def stop_idle_skill():
    # misty.MoveHead(0, 0, 0, None, 2)
    global idle_skill
    idle_skill = False
    # RECORDER.close_recording_resources()
    # misty.StopFaceRecognition()
    # misty.UnregisterAllEvents()
    # misty.ChangeLED(255, 255, 255)
    misty.DisplayImage("e_DefaultContent.jpg")
    # misty.StopKeyPhraseRecognition()
    # misty.StopRecordingAudio()
    # misty.DisableCameraService()
    misty.Halt()
    time.sleep(1)
    print("IDLE_SKILL_STOPPED")


# sample skill for misty, doesn't do anything special, can be used as a starting point for future skills
# start_sample_skill gets the robot as a parameter, so we can use its functions (we call this function from the
# idle skill)
# an infinite loop is required to not exit the function (or misty.KeepAlive() if we only use events)
# the function needs to return with True with the current skill switching implementation

# from idle_skill import start_idle_skill
# RECORDER = None

# LOOP = None
# RECORDER = None


def rps_start_skill():
    global return_to_idle, misty
    return_to_idle = False

    time.sleep(1)
    print("started")
    length_of_audio = tts.synthesize_text_to_wav("Elindult a kő papír olló játék, ha készen állsz, mondd,"
                                                 " hogy Éva szeretnék játszani ellened egyet", misty, "response.wav")
    print(length_of_audio)
    time.sleep(length_of_audio)
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
            if return_to_idle:
                return_to_idle = False
                globals.LOOP.run_until_complete(stt.ws_stream_close())

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


def rps_recording():
    data_stream = datastream(globals.RECORDER, stt)
    try:
        misty.ChangeLED(200, 0, 0)
        res = globals.LOOP.run_until_complete(asyncio.gather(data_stream, stt.message_listener()))
        print(res[1])
        if "error|recog-error" in res[1]:
            misty.DisplayImage("e_Disoriented.jpg")
            tts.synthesize_text_to_wav("Várj egy kicsit, elvesztettem a fonalat.", misty)
            misty.MoveHead(-5, 0, 0, 4, 0.1)
            globals.LOOP.run_until_complete(stt.ws_stream_close())
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

        # globals.RECORDER.close_recording_resources()
    # finally:
    # globals.RECORDER.close_recording_resources()


def rps_respond(speech_to_text_result=""):
    global return_to_idle, RECORDER
    return_to_idle = False
    matches = ["egyet", "játszunk", "még", "játszani", "szeretnék"]
    rps_exiting = ["kilép", "befejez", "vége", "abba", "lép"]
    # TODO: recognise the user's intent and answer or start a skill based on that

    misty.DisplayImage("e_Thinking2.jpg")
    if any(x in speech_to_text_result for x in rps_exiting):
        return_to_idle = True

    elif any(x in speech_to_text_result for x in matches):
        print("még egyet")
        rps()

    else:
        print("Nem értette")
        print(speech_to_text_result)
        misty.DisplayImage("e_Disoriented.jpg")
        length_of_audio = tts.synthesize_text_to_wav("Nem értettelek, kérlek ismételd meg!", misty, "response.wav")
        time.sleep(length_of_audio)
        rps_recording()


# Takes a picture and with cvzone's hand detector you get all the necessary finger position called landmarks
# and with those positions we can calculate which of the three moves the player is showing.
def get_human_move():
    data = misty.TakePicture(base64=True, fileName="test_photo", width=1440, height=1080)
    with open("file.jpg", "wb") as pic:
        pic.write(base64.b64decode(data.json()['result']['base64']))

    return image_landmarks(file_name="file.jpg")


def rps():
    length_of_audio = tts.synthesize_text_to_wav("Kőőőőő, papííííír, olllllló", misty, "response.wav")

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
        length_of_audio = tts.synthesize_text_to_wav("kérlek mutasd újra, mert nem láttam megfelelően a kezed", misty,
                                                     "response.wav")
        time.sleep(length_of_audio)
        for _ in range(3):
            misty.MoveArm("right", 30, duration=1)
            misty.MoveArm("right", -29, duration=1)
        human_move = get_human_move()
    # Show Misty's move
    # Images are preloaded on the robot
    misty.DisplayImage(f"{misty_move}_disp.png")

    print(f"Human's move is {human_move}")
    print(f"Misty's move is {misty_move}")

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

    length_of_audio = tts.synthesize_text_to_wav(misty_move_and_winner_announcement_hun, misty, "response.wav")
    misty.DisplayImage(expression)
    time.sleep(length_of_audio)

    # Reset Misty's face
    misty.DisplayImage("e_DefaultContent.jpg")

    # Prompt the user to play again or stop playing

    length_of_audio = tts.synthesize_text_to_wav(
        "Kérlek jelezd, ha szeretnél még egyet játszani.", misty, "response.wav")
    time.sleep(length_of_audio)

    rps_recording()


# sample skill for misty, doesn't do anything special, can be used as a starting point for future skills
# start_sample_skill gets the robot as a parameter,
# so we can use its functions (we call this function from the idle skill)
# an infinite loop is required to not exit the function (or misty.KeepAlive() if we only use events)
# the function needs to return with True with the current skill switching implementation


thanks = 'Köszönöm a játékot'
input_text = 'Kérlek mutass egy tárgyat és kérdezd meg, hogy mit mutatsz, például Éva ez egy alma vagy körte?'
again = 'Tegyél fel még egy kérdést, ha még szeretnél játszani vagy' \
        ' ha nem szeretnél tovább játszani mondd, hogy fejezzem be.'


def recognizer_respond(speech_to_text_result):
    global return_to_idle
    print(speech_to_text_result)
    recog_exiting = ["kilép", "fejez", "vége", "abba", "lép"]
    if any(x in speech_to_text_result for x in recog_exiting):
        length_of_audio = tts.synthesize_text_to_wav(thanks, misty, "response.wav")

        time.sleep(length_of_audio)
        return_to_idle = True
    elif "vagy" in speech_to_text_result:
        print("még egy játék!")
        recognizer(speech_to_text_result)
        recognizer_recording()
    else:
        print("nem értettem, próbáld újra")
        recognizer_recording()


def recognizer(message):
    time.sleep(2)
    misty.SetBlinking(True)
    data = misty.TakePicture(base64=True, fileName="test_photo", width=1440, height=1080)
    misty.SetBlinking(False)
    # print()
    with open("file.jpg", "wb") as pic:
        pic.write(base64.b64decode(data.json()['result']['base64']))
    image = cv2.imread('file.jpg')

    misty.ChangeLED(255, 255, 0)
    best_answer, probability, all_answer = model.evaluate(Image.fromarray(image), message)
    # TODO speech_to_text(url, '')

    misty.ChangeLED(0, 255, 0)
    misty.DisplayImage('e_Joy.jpg')
    print("hello")
    length_of_audio = tts.synthesize_text_to_wav(best_answer + ' van előttem', misty, 'response.wav')
    print(length_of_audio)
    time.sleep(length_of_audio)
    misty.DisplayImage('e_DefaultContent.jpg')
    length_of_audio = tts.synthesize_text_to_wav(again, misty, 'response.wav')
    time.sleep(length_of_audio)


def recognizer_recording():
    data_stream = datastream(globals.RECORDER, stt)
    try:
        misty.ChangeLED(200, 0, 0)

        res = globals.LOOP.run_until_complete(asyncio.gather(data_stream, stt.message_listener()))

        misty.ChangeLED(0, 200, 0)

        if "error|recog-error" in res[1]:
            misty.DisplayImage("e_Disoriented.jpg")
            tts.synthesize_text_to_wav("Várj egy kicsit, elvesztettem a fonalat.", misty)
            misty.MoveHead(-5, 0, 0, 4, 0.1)
            globals.LOOP.run_until_complete(stt.ws_stream_close())
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
    except Exception as e:
        connection_to_stt()


def recognizer_start_skill():
    global misty, return_to_idle
    return_to_idle = False
    misty
    misty.MoveHead(-5, 0, 0, velocity=4, duration=0.1)
    try:
        length_of_audio = tts.synthesize_text_to_wav(input_text, misty, "response.wav")
        globals.LOOP.run_until_complete(stt.ping_send())
        time.sleep(length_of_audio)
        print("recognizer skill started")
        if misty is not None:
            misty.ChangeLED(255, 0, 255)

            recognizer_recording()
            # misty.UnregisterAllEvents()
        while True:
            time.sleep(1)
            if return_to_idle:
                return_to_idle = False
                time.sleep(2)
                globals.LOOP.run_until_complete(stt.ws_stream_close())
                return True
    except KeyboardInterrupt:
        return_to_idle = True

    except Exception as e:
        print(e)
        connection_to_stt()
        recognizer_recording(globals.RECORDER)
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

        # this loop keeps the program alive
        # if skill_finished is True, we start the idle skill (which sets the skill_finished variable to false)
        # we keep cheking if skill_finished is True, so we can start the idle skill again
        # this is why external skills should return with True when finished

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
