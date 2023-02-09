# sample skill for misty, doesn't do anything special, can be used as a starting point for future skills
# start_sample_skill gets the robot as a parameter, so we can use its functions (we call this function from the
# idle skill)
# an infinite loop is required to not exit the function (or misty.KeepAlive() if we only use events)
# the function needs to return with True with the current skill switching implementation

import time
import sys, traceback

from rps_cvzone import *
from mistyPy.Robot import Robot
from mistyPy.Events import Events
from tts import TextToSpeechAPI

exit = False
captouch = False
misty = None
first_contact = True

tts = TextToSpeechAPI("http://szeged:s23936@cyrus.tmit.bme.hu/hmmtts2/synth_hmm_wav.php")


def start_skill(misty_robot):
    global return_to_idle, misty, captouch


    misty = misty_robot
    print("rps skill started")
    misty.UnregisterAllEvents()
    misty.MoveArms(leftArmPosition=90, rightArmPosition=0, duration=0.1)
    misty.MoveHead(0, 0, 0, None, 1)
    try:
        if misty is not None:
            misty.ChangeLED(255, 255, 0)
            misty.RegisterEvent("CapTouchSensor", Events.TouchSensor, callback_function=captouch_callback,
                                debounce=2000,
                                keep_alive=True)
        time.sleep(2)
        while True:
            if captouch:
                rps()
                captouch = False

            time.sleep(1)
            if exit:
                return True
    except KeyboardInterrupt:
        misty.UnregisterAllEvents()
        time.sleep(2)
        return True

    except Exception as e:
        print("Exception in user code: ")
        print("-" * 60)
        traceback.print_exc(file=sys.stdout)
        print("-" * 60)

    finally:
        return True


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
        "Kérlek érintsd meg a fejem, ha szeretnél még egyet játszani.", misty, "response.wav")
    misty.RegisterEvent("CapTouchSensor", Events.TouchSensor, callback_function=captouch_callback,
                        debounce=2000,
                        keep_alive=True)
    time.sleep(length_of_audio)



def captouch_callback(data):
    global captouch, exit, first_contact

    sensor_pos = data["message"]["sensorPosition"]
    print("Misty's head sensor pressed at: ", sensor_pos)
    if first_contact and (data['message']['sensorPosition'] == "HeadFront"):
        length_of_start_audio = tts.synthesize_text_to_wav(
            "Szia, én Miszti vagyok, ha megsimogatod a buksim, "
            "amit már meg is tettél akkor tudsz velem kő, papír, ollózni", misty)
        time.sleep(length_of_start_audio)
        misty.UnregisterAllEvents()
        captouch = True
        first_contact = False

    # Announce the results and end the program if Misty's chin is touched
    if sensor_pos == "Chin":
        misty.PlayAudio("s_Awe2.wav")
        misty.DisplayImage("e_EcstacyStarryEyed.jpg")
        time.sleep(5)
        misty.DisplayImage("e_DefaultContent.jpg")


if __name__ == '__main__':
    if len(sys.argv) > 1:
        misty_ip_address = sys.argv[1]
    else:
        misty_ip_address = "10.2.8.5"
    misty = Robot(misty_ip_address)

    misty.UnregisterAllEvents()
    start_skill(misty)
