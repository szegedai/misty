# sample skill for misty, doesn't do anything special, can be used as a starting point for future skills
# start_sample_skill gets the robot as a parameter, so we can use its functions (we call this function from the
# idle skill)
# an infinite loop is required to not exit the function (or misty.KeepAlive() if we only use events)
# the function needs to return with True with the current skill switching implementation

from rps_cvzone import *
from hci_methods import *
from mistyPy.Robot import Robot
from mistyPy.Events import Events

# from idle_skill import start_idle_skill
return_to_idle = False
misty = None
stt_api = stt_bme.SpeechToTextAPI("wss://chatbot-rgai3.inf.u-szeged.hu/socket")


def start_skill(misty_robot, misty_ip_address):
    global return_to_idle
    print("started")
    global misty
    misty = misty_robot
    tts.synthesize_text_to_robot(misty, "Elindult a kő papír olló játék", "response.wav")
    print("rps skill started")
    misty.MoveArms(leftArmPosition=90, rightArmPosition=0, duration=0.1)
    # misty.MoveHead(pitch=0, roll=0, yaw=0)
    try:
        if misty is not None:
            misty.ChangeLED(255, 255, 0)
            misty.RegisterEvent("CapTouchSensor", Events.TouchSensor, callback_function=captouch_callback,
                                debounce=2000,
                                keep_alive=True)

        start_listening()
        while True:
            time.sleep(1)
            if return_to_idle:
                return_to_idle = False
                exit_function(misty)
                time.sleep(2)
                return True
    except KeyboardInterrupt:
        exit_function(misty)
        time.sleep(2)
        return True

    except Exception as e:
        print(e)

    finally:
        return True


def key_phrase_callback(data):
    print(f"Misty heard you, trying to wake her up. Confidence: {data['message']['confidence']}%")


def start_listening():
    misty.RegisterEvent("voice_cap", Events.VoiceRecord, callback_function=voice_rec_callback, debounce=10,
                        keep_alive=False)
    misty.RegisterEvent("key_phrase_recognized", Events.KeyPhraseRecognized, callback_function=key_phrase_callback,
                        debounce=10, keep_alive=False)
    misty.StartKeyPhraseRecognition()
    print("KeyPhraseRecognition started (for conversation)")


def voice_rec_callback(data):
    speech_to_text_result = ""
    print("voice_rec_callback START")
    if data["message"]["success"]:
        misty.StopKeyPhraseRecognition()
        # misty.StopRecordingAudio()
        # accessing the wav file
        encoded_string = misty.GetAudioFile("capture_HeyMisty.wav", True).json()["result"]["base64"]
        misty.DeleteAudio("capture_HeyMisty.wav")
        # copying the file into "out.wav"
        wav_file = open("out.wav", "wb")
        wav_file.write(base64.b64decode(encoded_string))

        # we send the wav file to the BME stt
        try:
            if asyncio.run(stt_api.ws_check_connection()):
                # while we wait for the result,
                # we change the led to green to indicate that stuff is happening in the background

                misty.ChangeLED(0, 255, 0)
                misty.DisplayImage("e_Thinking4.jpg")
                res = asyncio.run(stt_api.ws_wav_recognition("out.wav", 4096))
                print("Result: ", res.split(";")[1])
                speech_to_text_result = res.split(";")[1]
            else:
                print("Unable to establish connection to the ASR server!")
        except Exception as e:
            print("ERROR")
            print(e)
        print("waiting for response")
        respond(str.lower(speech_to_text_result))

    else:
        print("Unsuccessful voice recording")
    # print("unregistering...")
    # after responding, unregister events needed for the conversation
    if "voice_cap" in misty.active_event_registrations:
        misty.UnregisterEvent("voice_cap")
    if "key_phrase_recognized" in misty.active_event_registrations:
        misty.UnregisterEvent("key_phrase_recognized")
    time.sleep(1)
    print("voice_rec_callback DONE")


def respond(speech_to_text_result=""):
    global return_to_idle
    print(speech_to_text_result)
    # TODO: recognise the user's intent and answer or start a skill based on that
    # e.g.
    # if intent == "play rock paper scissors":
    #   start_external_skill("rps")
    misty.DisplayImage("e_Thinking2.jpg")
    if ("lépj" or "lép") in speech_to_text_result:
        exit_function(misty)
        return_to_idle = True
        # start_idle_skill()

    elif ("még egyet" or "játszunk" or "még" or "játszani" or "szeretnék") in speech_to_text_result:
        rps()
    # elif "papír" in speech_to_text_result:
    #     start_external_skill("ph_rps")
    # elif "felismerő" in speech_to_text_result or "ismer" in speech_to_text_result:
    #     start_external_skill("ph_recognizer")

    else:
        print("Nem értette")
        misty.DisplayImage("e_Disoriented.jpg")
        tts.synthesize_text_to_robot(misty, f"Azt hallottam, hogy: {speech_to_text_result}", "response.wav")
        misty.StartKeyPhraseRecognition(captureSpeech=False)
        tts.synthesize_text_to_robot(misty, "Nem értettem, kérlek mondd máshogy!", "response.wav")


# Takes a picture and with cvzone's hand detector you get all the necessary finger position called landmarks
# and with those positions we can calculate which of the three moves the player is showing.
def get_human_move():
    data = misty.TakePicture(base64=True, fileName="test_photo", width=1440, height=1080)
    # print()
    with open("file.jpg", "wb") as pic:
        pic.write(base64.b64decode(data.json()['result']['base64']))

    return image_landmarks(file_name="file.jpg")


def rps():
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
    if "voice_cap" and "key_phrase_recognized" in misty.active_event_registrations:
        misty.UnregisterEvent("key_phrase_recognized")
        misty.UnregisterEvent("voice_cap")
        print("Events unregistered")
    time.sleep(1)
    start_listening()


def captouch_callback(data):
    global return_to_idle
    sensor_pos = data["message"]["sensorPosition"]
    print("Misty's head sensor pressed at: ", sensor_pos)
    rps_misty_wins = 0
    rps_human_wins = 0
    rps_draws = 0

    # Start RPS game if Misty's head is touched
    if sensor_pos == "HeadFront":
        rps()

    # Announce the results and end the program if Misty's chin is touched
    if sensor_pos == "Chin":
        return_to_idle=True
        misty_wins = f"Én nyertem {rps_misty_wins} alkalommal."
        human_wins = f"Te nyertél {rps_human_wins} alkalommal."
        draws = f"Döntetlen lett {rps_draws} alkalommal."

        summary = f"{misty_wins} {human_wins} {draws}"

        tts.synthesize_text_to_robot(misty, summary, "mistynek.wav")

        if "voice_cap" and "key_phrase_recognized" in misty.active_event_registrations:
            misty.UnregisterEvent("key_phrase_recognized")
            misty.UnregisterEvent("voice_cap")
            print("Events unregistered")

        exit_function(misty)
        # start_idle_skill(misty)


if __name__ == '__main__':
    ip = '10.2.8.5'
    misty = Robot(ip)
    misty.UnregisterAllEvents()
    start_skill(misty, misty_ip_address=ip)
