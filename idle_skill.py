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

import tts
import sys
import time
import random
import base64
import asyncio
import numpy as np
import dateutil.parser
import rps
import recognizer

import Recorder
import SpeechToText
from main import init
from main import datastream

from statistics import mean
from mistyPy.Robot import Robot
from mistyPy.Events import Events
from datetime import datetime, timezone
from mistyPy.EventFilters import EventFilters

LOOP = None
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
RECORDER = None
degree_list = []
stt = SpeechToText.SpeechToTextAPI("wss://chatbot-rgai3.inf.u-szeged.hu/socket")


# initializing variables, registering events and starting services required for the idle skill
def init_variables_and_events():
    global searching_for_face, head_yaw, head_pitch, yaw_right, yaw_left, pitch_up, pitch_down, misty, looked_at, \
        robot_yaw, _1b, _2b, vector, head_yaw_for_turning, face_rec_event_status
    global idle_skill, skill_finished, restart_skill, start_external, waiting_for_response
    # setting misty head position
    misty.MoveArms(leftArmPosition=0, rightArmPosition=0, duration=0.1)
    misty.MoveHead(pitch=0, roll=0, yaw=0)
    # initializing variables
    idle_skill = True
    restart_skill = False
    start_external = False
    waiting_for_response = False
    # set skill finished False, so the while loop in the main function doesn't keep calling start_idle_skill
    skill_finished = False

    # these are the results of the calibration() function
    yaw_right = -85.94366926962348
    yaw_left = 78.49521793292278
    pitch_down = 26.92901637114869
    pitch_up = -33.231552117587746

    misty.MoveHead(0, 0, 0, None, 1)
    searching_for_face = True
    misty.ChangeLED(0, 0, 0)
    head_yaw = 0.0
    head_yaw_for_turning = 0.0
    head_pitch = 0.0
    robot_yaw = 0.0
    _1b = 0.0
    _2b = 0.0
    vector = 0.0
    looked_at = datetime.now(timezone.utc)
    misty.UnregisterAllEvents()
    # starting services
    # misty.EnableCameraService()
    # misty.StopFaceRecognition()
    # misty.StartFaceRecognition()
    # registering evnets
    # event needed for face recognition
    face_rec_event_status = misty.RegisterEvent("face_rec", Events.FaceRecognition, callback_function=face_rec_callback,
                                                debounce=1300, keep_alive=True)
    # events needed to store head position data
    misty.RegisterEvent("set_head_yaw", Events.ActuatorPosition, condition=[EventFilters.ActuatorPosition.HeadYaw],
                        callback_function=set_head_yaw_callback, debounce=100, keep_alive=True)
    misty.RegisterEvent("set_head_pitch", Events.ActuatorPosition, condition=[EventFilters.ActuatorPosition.HeadPitch],
                        callback_function=set_head_pitch_callback, debounce=100, keep_alive=True)
    misty.RegisterEvent("heading", Events.IMU, callback_function=heading_callback, debounce=10, keep_alive=True)
    # events needed for audio localisation and turning
    misty.RegisterEvent("sound", Events.SourceTrackDataMessage, callback_function=sound_callback, debounce=100,
                        keep_alive=True)
    misty.RegisterEvent("key_phrase_turn", Events.KeyPhraseRecognized, callback_function=key_phrase_turn_callback,
                        debounce=10, keep_alive=False)
    # event for bump sensor and cap touch sensor
    misty.RegisterEvent("bump_sensor_pressed", Events.BumpSensor, callback_function=bump_callback, debounce=10,
                        keep_alive=True)
    misty.RegisterEvent("captouch", Events.TouchSensor, callback_function=captouch_callback, debounce=100,
                        keep_alive=True)


# callback for the captouch event
# we use this to restart the idle skill if something goes wrong
def captouch_callback(data):
    global restart_skill, first_contact
    print(data)
    restart_skill = True
    first_contact = True
    print("Restarting skill...")
    stop_idle_skill()
    time.sleep(1)

    # start_idle_skill()


# callback for the bump_sensor_pressed event
# currently only used for testing purposes
def bump_callback(data):
    start_external_skill("ph_rps")


# this function stops the idle skill and sets the start_external variable to True
# we call this function when we want to start an external skill from the main loop
# we pass the name of the skill we want to start as a parameter
def start_external_skill(skill=""):

    global start_external, skill_to_start
    stop_idle_skill()
    time.sleep(1)
    print(f"starting {skill} skill")
    skill_to_start = skill
    start_external = True


def recording(recorder):
    # global idle_skill
    # idle_skill=False

    data_stream = datastream(recorder, stt)
    try:
        misty.ChangeLED(200, 0,0)
        print("try")
        # loop_a = asyncio.new_event_loop()
        # asyncio.set_event_loop(loop_a)
        print(LOOP)
        res = LOOP.run_until_complete(asyncio.gather(data_stream, stt.message_listener()))
        print("KESZ")
        print(res[1])
        misty.ChangeLED(0,200,0)

        respond(str.lower(res[1]))
    except Exception as e:
        print(e)
        recorder.close_recording_resources()


# this function starts the idle skill
def start_idle_skill(misty_robot, calibration=False):
    global searching_for_face, misty, turn_in_progress,  face_rec_event_status
    global date_time_of_last_face_detection, idle_skill, waiting_for_response, seconds_since_last_detection
    misty = misty_robot
    init_variables_and_events()
    print("idle_skill STARTED")
    if calibration:
        calibrate()
    # this is the main loop of the skill
    misty.StartFaceRecognition()
    while idle_skill:
        time.sleep(0.1)
        if misty is not None:
            # if status is not in face_rec_event_status.data it means misty sees a face,
            # so we save the time of the detection
            if not "status" in face_rec_event_status.data:
                date_time_of_last_face_detection = dateutil.parser.isoparse(
                    face_rec_event_status.data["message"]["created"])
            # if we already detected a face, we calculate the seconds since the last detection
            if date_time_of_last_face_detection is not None:
                seconds_since_last_detection = (
                        datetime.now(timezone.utc) - date_time_of_last_face_detection).total_seconds()
            # if the last face detection was more than 4 seconds ago, and turning is not in progress
            # then we unregister events for conversation and register events for turning
            if not searching_for_face:
                misty.StopFaceRecognition()
                recording(RECORDER)

            if (seconds_since_last_detection >= 4 or searching_for_face) \
                    and not turn_in_progress \
                    and not waiting_for_response\
                    and not start_external:

                # if the key_phrase_recognized event is still registered,
                # we stop the KeyPhraseRecognition and unregister the event
                # this is needed, because we need the key_phrase_turn event,
                # and it also uses KeyPhraseRecognition so it conflicts with key_phrase_recognized
                if "key_phrase_recognized" in misty.active_event_registrations:
                    misty.StopKeyPhraseRecognition()
                    time.sleep(1)
                    misty.UnregisterEvent("key_phrase_recognized")
                    print("Face lost...")
                    print("KeyPhraseRecognition stopped (for conversation)")
                # we also unregister voic_cap if it's still registered

                # if key_phrase_turn is not registered, we register it
                # this event is needed for turning towards sound
                if not "key_phrase_turn" in misty.active_event_registrations:
                    print("KeyPhraseRecognition started (for turning)")
                    misty.StartKeyPhraseRecognition(captureSpeech=False)
                    misty.RegisterEvent("key_phrase_turn", Events.KeyPhraseRecognized,
                                        callback_function=key_phrase_turn_callback, debounce=10, keep_alive=False)
                # if sound is not registered, we register it
                # this event is also needed for turning towards sound
                if not "sound" in misty.active_event_registrations:
                    misty.RegisterEvent("sound", Events.SourceTrackDataMessage, callback_function=sound_callback,
                                        debounce=100, keep_alive=True)
                searching_for_face = True
                # we call the look_side_to_side() function to move Misty's head
                look_side_to_side()
                # we wait so misty can finish moving her head before calling stuff again
                time.sleep(5)
            # print(misty.active_event_registrations)


# calibration function, currently not calling it anywhere,
# the results are stored in the yaw_right, yaw_left, pitch_down, pitch_up variables
def calibrate():
    global yaw_right, yaw_left, pitch_down, pitch_up
    print("CALIBRATION STARTED")
    misty.MoveHead(0, 0, -90, None, 2)
    time.sleep(4)
    yaw_right = head_yaw
    print(f"yaw_right recorded: {yaw_right}")

    misty.MoveHead(0, 0, 90, None, 2)
    time.sleep(4)
    yaw_left = head_yaw
    print(f"yaw_left recorded: {yaw_left}")

    misty.MoveHead(90, 0, 0, None, 2)
    time.sleep(4)
    pitch_down = head_pitch
    print(f"pitch_down recorded: {pitch_down}")

    misty.MoveHead(-90, 0, 0, None, 2)
    time.sleep(4)
    pitch_up = head_pitch
    print(f"pitch_up recorded: {pitch_up}")

    print("CALIBRATION COMPLETE")
    misty.MoveHead(0, 0, 0, None, 2)


# utility function to remove outliers from the voice detection (degreeOfArrivalSpeech) list
def reject_outliers(data, m=6.):
    data = np.array(data)
    d = np.abs(data - np.median(data))
    mdev = np.median(d)
    s = d / (mdev if mdev else 1.)
    return data[s < m].tolist()


# callback for the heading event
# we receive data from the robot every 10ms, and we store the data in the robot_yaw variable
def heading_callback(data):
    global robot_yaw
    yaw = data["message"]["yaw"]
    if yaw > 180: yaw -= 360
    robot_yaw = yaw


# callback for the sound event
# this triggers, when an audio recording is started(StartRecordingAudio)
# we store the degrees of arrival speech in the degree_list list
def sound_callback(data):
    global degree_list

    degree_list.append(data['message']['degreeOfArrivalSpeech'])
    print(data['message']['degreeOfArrivalSpeech'])
    # misty.StopKeyPhraseRecognition()


# callback for the key_phrase_turn event
# this triggers when misty is not looking at a face and she hears "Hey, Misty!"
# we attempt to localise the incoming voice activity and turns towards the sound
def key_phrase_turn_callback(data):
    global turn_in_progress, _1b, _2b, misty, vector, degree_list
    print("key_phrase_turn_callback START")
    turn_in_progress = True
    misty.MoveHead(0, 0, 0, None, 2)
    time.sleep(2)

    # we start recording audio, this is needed for the sound event to trigger
    misty.StartRecordingAudio("deleteThis.wav")
    misty.UnregisterEvent("key_phrase_turn")
    misty.StopKeyPhraseRecognition()
    time.sleep(0.5)
    # we set the LED to green to indicate that misty is listening
    misty.ChangeLED(0, 255, 0)
    misty.DisplayImage("e_Thinking.jpg")
    # we wait a few seconds, continuous speech is required for misty to accurately pick up voice activity
    time.sleep(2)
    misty.ChangeLED(0, 0, 0)
    misty.DisplayImage("e_DefaultContent.jpg")
    # we unregister the sound event and stop the audio recording
    misty.UnregisterEvent("sound")
    misty.StopRecordingAudio()

    # processing the sound data
    degree_list = list(set(degree_list))
    if len(degree_list) > 1:
        # the default value for degreeOfArrivalSpeech is 90, we filter this out if it's not the only element in the list
        # so it doesn't skew the data
        degree_list = list(filter(lambda x: x != 90, degree_list))
    # we also filter out outliers
    degree_list = reject_outliers(degree_list)
    print(degree_list)
    # finally we get the mean of the data, this is our final degree_of_arrival_speech
    degree_of_arrival_speech = mean(degree_list)

    print(f"degree_of_arrival_speech: {degree_of_arrival_speech}")
    degree_list = []
    # if our final result is exactly 90 it is likely that misty didn't pick up the sound (and just sent the default 90),
    # so we don't do anything
    # could also make misty say something
    if degree_of_arrival_speech == 90:
        print("already facing the right direction")
        time.sleep(1)
    else:
        # if the final result is not 90, we call the look_at function
        # the math is taken from the original js script
        # https://github.com/CPsridharCP/MistySkills/blob/master/ExampleSkills/Advanced/moveToSound/moveToSound.js
        vector = 0.4 * to_robot_frame(degree_of_arrival_speech) + 0.35 * _1b + 0.25 * _2b
        # if seconds_past(looked_at) > 5.0 and searching_for_face:
        print("Misty hallott, fordul a hang felé...")
        print(f"vector: {vector}")
        # turn_in_progress = True
        # print(f"{vector} <-- Look At Input Global")
        look_at(vector, robot_yaw, head_yaw_for_turning)
        misty.RegisterEvent("sound", Events.SourceTrackDataMessage, callback_function=sound_callback, debounce=100,
                            keep_alive=True)
        _2b = _1b
        _1b = vector
    turn_in_progress = False
    print("key_phrase_callback DONE")


# utility function needed for the turn calculation
def to_robot_frame(data):
    sound_in = data
    if sound_in > 180: sound_in -= 360
    return sound_in


# utility function needed for the turn calculation
def offset_heading(to_offset):
    heading = robot_yaw + to_offset
    return (360.0 + (heading % 360)) % 360.0


# utility function needed for the turn calculation
def angle_difference(now, to):
    diff = (to - now + 180) % 360 - 180
    return diff + 360 if diff < -180 else diff


# misty turns towards sound
def look_at(heading, robot_yaw_at_start, head_yaw_at_start):
    global face_rec_event_status, misty
    print("look_at START")
    look_at_start_time = datetime.now(timezone.utc)
    # we unregister the face_rec event, so misty doesn't look for faces during turning
    misty.UnregisterEvent("face_rec")

    global_heading = offset_heading(heading + (head_yaw_at_start * 2.0))

    if global_heading > 180: global_heading -= 360
    # start to turn in place
    misty.Drive(0, 30) if angle_difference(robot_yaw_at_start, global_heading) >= 0 else misty.Drive(0, -30)
    initial_error = abs(angle_difference(robot_yaw_at_start, global_heading))
    current_abs_error = initial_error
    # keep checking if we reached the target heading
    while abs(robot_yaw - global_heading) >= 3:
        # if misty is turning for more than 10 secs, it is likely that something went wrong
        # e.g robot_yaw - global_heading goes below -3, so abs(robot_yaw - global_heading) >= 3 will always be true
        # so we break and stop misty's turn
        if (datetime.now(timezone.utc) - look_at_start_time).total_seconds() > 10:
            print("something went wrong during turning")
            break
    # when we reach the target, we stop misty's turn
    misty.Stop()
    # after the turning is done, we register the face_rec event again
    face_rec_event_status = misty.RegisterEvent("face_rec", Events.FaceRecognition, callback_function=face_rec_callback,
                                                debounce=1300, keep_alive=True)
    print("look_at DONE")


# callback for the set_head_yaw event
# stores head position data needed for turning and following face
def set_head_yaw_callback(data):
    global head_yaw, head_yaw_for_turning
    head_yaw = data["message"]["value"]
    head_yaw_local = data["message"]["value"]
    head_yaw_local = -45.0 if head_yaw_local < -45.0 else head_yaw_local
    head_yaw_local = 45.0 if head_yaw_local > 45.0 else head_yaw_local
    head_yaw_for_turning = head_yaw_local
    # print(f"head_yaw set to: {head_yaw}")


# callback for the set_head_pitch event
# stores head position data needed for turning and following face
def set_head_pitch_callback(data):
    global head_pitch
    head_pitch = data["message"]["value"]
    # print(f"head_pitch set to: {head_pitch}")


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
    if "minta" in speech_to_text_result or "mint a" in speech_to_text_result:
        start_external_skill("sample")
    elif "papír" in speech_to_text_result:
        start_external_skill("ph_rps")
    elif "felismerő" in speech_to_text_result or "ismer" in speech_to_text_result:
        start_external_skill("ph_recognizer")
    else:
        print("Nem értette")
        tts.synthesize_text_to_robot(misty, f"Azt hallottam, hogy: {speech_to_text_result}", "response.wav")
        # tts.synthesize_text_to_robot(misty, "Nem értettem, kérlek mondd máshogy!", "response.wav")
        recording(RECORDER)

    waiting_for_response = False


# callback for the face_rec event
# this event triggers when misty sees a face
# in this function we unregister events needed for turning (we want to disable turning while misty sees someone)
# and we register events for conversation (so we can have a conversation or start a skill with speech)
# we also try to follow the recognised face
def face_rec_callback(data):
    global searching_for_face, misty, turn_in_progress, first_contact


    print("face found!")
    # print(data["message"]["label"])

    if first_contact:
        tts.synthesize_text_to_robot(misty,
                                     # "Hello Én miszti robot vagyok! Örülök, hogy itt vagy! 3 szuper játékot tudsz "
                                     # "velem játszani. Kő papír olló, felismerő robot és érzelem robot. Melyikkel "
                                     # "szeretnél játszani? A héj miszti paranccsal tudsz megszólítani, "
                                     "majd a pittyenés után beszélhetsz.",
                                     "response.wav")
        first_contact = False

    # unregistering events used for turning
    if "key_phrase_turn" in misty.active_event_registrations:
        misty.StopKeyPhraseRecognition()
        misty.UnregisterEvent("key_phrase_turn")
        print("key_phrase_turn unregistered")
        misty.Halt()
    if "sound" in misty.active_event_registrations:
        misty.UnregisterEvent("sound")
        print("sound unregistered")
        # respond()

    # we call the start_listening() function, that registers events needed for conversation
    if searching_for_face and not turn_in_progress and not waiting_for_response:
        searching_for_face = False
        # misty.ChangeLED(0, 255, 0);
        misty.DisplayImage("e_Love.jpg")
        time.sleep(1)

        # recording(RECORDER)

    # storing head position data
    bearing = data["message"]["bearing"]
    elevation = data["message"]["elevation"]
    # print(f"bearing: {bearing}")
    # print(f"elevation: {elevation}")

    # misty followes recognised face with her head
    # maths taken from the original skill:
    # https://github.com/CPsridharCP/MistySkills/blob/master/ExampleSkills/Advanced/followFace/followFace.js
    if bearing != 0 and elevation != 0:
        misty.MoveHead(head_pitch + ((pitch_down - pitch_up) / 33) * elevation, 0,
                       head_yaw + ((yaw_left - yaw_right) / 66) * bearing, None, 7 / abs(bearing))
    elif bearing != 0:
        misty.MoveHead(None, 0, head_yaw + ((yaw_left - yaw_right) / 66) * bearing, None, 7 / abs(bearing))
    else:
        misty.MoveHead(head_pitch + ((pitch_down - pitch_up) / 33) * elevation, 0, None, None, 5 / abs(elevation))


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
    misty.StopFaceRecognition()
    misty.UnregisterAllEvents()
    # misty.ChangeLED(255, 255, 255)
    misty.DisplayImage("e_DefaultContent.jpg")
    misty.StopKeyPhraseRecognition()
    misty.StopRecordingAudio()
    # misty.DisableCameraService()
    misty.Halt()
    time.sleep(3)
    print("IDLE_SKILL_STOPPED")


if __name__ == "__main__":

    LOOP = asyncio.new_event_loop()
    asyncio.set_event_loop(LOOP)
    LOOP.run_until_complete(init(stt))

    stream_params = Recorder.StreamParams()
    RECORDER = Recorder.Recorder(stream_params)
    RECORDER.create_recording_resources()

    try:
        if len(sys.argv) > 1:
            misty_ip_address = sys.argv[1]
        else:
            misty_ip_address = "10.2.8.5"
        misty = Robot(misty_ip_address)

        misty.UnregisterAllEvents()
        # print(EventFilters.mro())
        # print(Robot.Get)
        while True:
            time.sleep(0.1)
            print("main cycle")
            if skill_finished or restart_skill:
                print("starting idle skill")
                first_contact = False
                start_idle_skill(misty)

            # if start_external is True, we check the skill_to_start variable's value and start a skill based on that
            if start_external:

                if skill_to_start == "ph_rps":
                    skill_finished = rps.start_skill(misty, recorder=RECORDER, loop=LOOP)
                elif skill_to_start == "ph_recognizer":
                    skill_finished = recognizer.start_skill(misty, recorder=RECORDER)

                else:
                    print("skill not found restarting idle_skill")
                    restart_skill = True
        # this loop keeps the program alive
        # if skill_finished is True, we start the idle skill (which sets the skill_finished variable to false)
        # we keep cheking if skill_finished is True, so we can start the idle skill again
        # this is why external skills should return with True when finished

    except Exception as ex:
        print(ex)

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
