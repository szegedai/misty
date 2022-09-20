# sample skill for misty, doesn't do anything special, can be used as a starting point for future skills
# start_sample_skill gets the robot as a parameter, so we can use its functions (we call this function from the
# idle skill)
# an infinite loop is required to not exit the function (or misty.KeepAlive() if we only use events)
# the function needs to return with True with the current skill switching implementation
import asyncio
import time
import globals
import Recorder
import SpeechToText
import sys, traceback
from main import init
from main import datastream
from rps_cvzone import *
from hci_methods import *
from mistyPy.Robot import Robot
from mistyPy.Events import Events

# from idle_skill import start_idle_skill
# RECORDER = None
return_to_idle = False
misty = None
# LOOP = None
# RECORDER = None
stt = SpeechToText.SpeechToTextAPI("wss://chatbot-rgai3.inf.u-szeged.hu/socket")


# def connecting_to_stt():
#     global LOOP, RECORDER
#     LOOP = asyncio.new_event_loop()
#     asyncio.set_event_loop(LOOP)
#     LOOP.run_until_complete(init(stt))
#
#     stream_params = Recorder.StreamParams()
#     RECORDER = Recorder.Recorder(stream_params)
#     RECORDER.create_recording_resources()


def start_skill(misty_robot):
    global return_to_idle, misty
    # global RECORDER
    time.sleep(3)
    # connecting_to_stt()
    print("started")
    misty = misty_robot
    tts.synthesize_text_to_robot(misty, "Elindult a kő papír olló játék", "response.wav")
    print("rps skill started")
    misty.UnregisterAllEvents()
    misty.MoveArms(leftArmPosition=90, rightArmPosition=0, duration=0.1)
    # misty.MoveHead(pitch=0, roll=0, yaw=0)
    try:
        if misty is not None:
            misty.ChangeLED(255, 255, 0)
            misty.RegisterEvent("CapTouchSensor", Events.TouchSensor, callback_function=captouch_callback,
                                debounce=2000,
                                keep_alive=True)

        recording()
        while True:
            time.sleep(1)
            if return_to_idle:
                return_to_idle = False
                exit_function(misty)
                time.sleep(2)
                return True
    except KeyboardInterrupt:
        globals.RECORDER.close_recording_resources()
        exit_function(misty)
        time.sleep(2)
        return True

    except Exception as e:
        print("Exception in user code: ")
        print("-" * 60)
        traceback.print_exc(file=sys.stdout)
        print("-" * 60)

    finally:
        globals.RECORDER.close_recording_resources()
        return True


def recording():
    # global RECORDER, LOOP

    data_stream = datastream(globals.RECORDER, stt)
    try:
        misty.ChangeLED(200, 0,0)
        print("-" * 60)
        print("Globals RECORDER: ", globals.RECORDER)
        # loop = asyncio.get_event_loop()
        print("Globals LOOP: ", globals.LOOP)
        print("-" * 60)
        res = globals.LOOP.run_until_complete(asyncio.gather(data_stream, stt.message_listener()))
        print(res[1])
        misty.ChangeLED(0,200,0)
        respond(globals.RECORDER, globals.LOOP, str.lower(res[1]))

    except Exception:
        print("Exception in user code:")
        print("-" * 60)
        traceback.print_exc(file=sys.stdout)
        print("-" * 60)
        globals.RECORDER.close_recording_resources()
    finally:
        globals.RECORDER.close_recording_resources()


def respond(recorder, loop, speech_to_text_result=""):
    global return_to_idle,RECORDER
    print(speech_to_text_result)
    # TODO: recognise the user's intent and answer or start a skill based on that
    # e.g.
    # if intent == "play rock paper scissors":
    #   start_external_skill("rps")
    misty.DisplayImage("e_Thinking2.jpg")
    if "lépj" or "lép" in speech_to_text_result:
        exit_function(misty)
        return_to_idle = True
        # start_idle_skill()

    elif "még egyet" or "játszunk" or "még" or "játszani" or "szeretnék" in speech_to_text_result:
        rps(globals.RECORDER, loop)
    # elif "papír" in speech_to_text_result:
    #     start_external_skill("ph_rps")
    # elif "felismerő" in speech_to_text_result or "ismer" in speech_to_text_result:
    #     start_external_skill("ph_recognizer")

    else:
        print("Nem értette")
        print(speech_to_text_result)
        misty.DisplayImage("e_Disoriented.jpg")
        tts.synthesize_text_to_robot(misty, "Nem értettem, kérlek mondd máshogy!", "response.wav")
        recording()


# Takes a picture and with cvzone's hand detector you get all the necessary finger position called landmarks
# and with those positions we can calculate which of the three moves the player is showing.
def get_human_move():
    data = misty.TakePicture(base64=True, fileName="test_photo", width=1440, height=1080)
    with open("file.jpg", "wb") as pic:
        pic.write(base64.b64decode(data.json()['result']['base64']))

    return image_landmarks(file_name="file.jpg")


def rps(recorder, loop):
    tts.synthesize_text_to_robot(misty, "Kő, papír, olló.", "mistynek.wav")

    # Wave arms thee times
    for _ in range(3):
        misty.MoveArm("right", 30)
        time.sleep(0.4)
        misty.MoveArm("right", -29)
        time.sleep(0.4)

    # Detect the player's move and pick a random move for Misty
    human_move = get_human_move()
    misty_move = get_random_move()

    while human_move is None:
        print('helo')
        tts.synthesize_text_to_robot(misty, "kérlek mutasd újra, mert nem láttam megfelelően a kezed", "mistynek.wav")
        time.sleep(5)
        human_move = get_human_move()
    # Show Misty's move
    # Images are pre-loaded on the robot
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
        print("You win")
        winner_hun = "Te nyertél."
        expression = "e_Rage3.jpg"

    # Announce Misty's move and winner
    misty_move_and_winner_announcement_hun = f"{misty_move_hun} {human_move_hun} {winner_hun}"
    print(misty_move_and_winner_announcement_hun)

    tts.synthesize_text_to_robot(misty, misty_move_and_winner_announcement_hun, "mistynek.wav")
    misty.DisplayImage(expression)
    time.sleep(5)

    # Reset Misty's face
    misty.DisplayImage("e_DefaultContent.jpg")

    # Prompt the user to play again or stop playing

    tts.synthesize_text_to_robot(misty,
                                 "Kérlek mondd, ha akarsz még egyet játszani.",
                                 "mistynek.wav")
    time.sleep(5)

    print("done")
    recording()


def captouch_callback(data):
    global return_to_idle
    sensor_pos = data["message"]["sensorPosition"]
    print("Misty's head sensor pressed at: ", sensor_pos)
    rps_misty_wins = 0
    rps_human_wins = 0
    rps_draws = 0

    # Announce the results and end the program if Misty's chin is touched
    if sensor_pos == "Chin":
        return_to_idle=True
        misty_wins = f"Én nyertem {rps_misty_wins} alkalommal."
        human_wins = f"Te nyertél {rps_human_wins} alkalommal."
        draws = f"Döntetlen lett {rps_draws} alkalommal."

        summary = f"{misty_wins} {human_wins} {draws}"

        tts.synthesize_text_to_robot(misty, summary, "mistynek.wav")

        exit_function(misty)
        # start_idle_skill(misty)


if __name__ == '__main__':
    ip = '10.2.8.5'
    misty = Robot(ip)

    globals.init()
    globals.LOOP= asyncio.new_event_loop()
    asyncio.set_event_loop(globals.LOOP)
    globals.LOOP.run_until_complete(init(stt))

    stream_params = Recorder.StreamParams()
    globals.RECORDER = Recorder.Recorder(stream_params)
    globals.RECORDER.create_recording_resources()
    misty.UnregisterAllEvents()
    start_skill(misty)
