# sample skill for misty, doesn't do anything special, can be used as a starting point for future skills
# start_sample_skill gets the robot as a parameter,
# so we can use its functions (we call this function from the idle skill)
# an infinite loop is required to not exit the function (or misty.KeepAlive() if we only use events)
# the function needs to return with True with the current skill switching implementation
import tts
import time
import base64
import stt_bme
import asyncio
import hci_methods
from mistyPy.Robot import Robot
from mistyPy.Events import Events

return_to_idle = False
stt_api = stt_bme.SpeechToTextAPI("wss://chatbot-rgai3.inf.u-szeged.hu/socket")
misty = None
message = ''
thanks = 'Köszönöm a játékot'
input_text = 'Sziasztok! Én vagyok a miszti robot, aki tárgyakat képes felismerni. ' \
             'Mutass nekem tárgyakat és tegyél fel nekem találós kérdést a tárggyal kapcsolatban. ' \
             'Például, ha felmutatsz egy almát megkérdezheted, hogy "Almát vagy banánt mutatok?". ' \
             'Simogasd meg a fejem s tedd fel a kérdésed.'


def captouch_callback(data):
    # https://docs.mistyrobotics.com/misty-ii/javascript-sdk/code-samples/#captouch
    sensor_pos = data["message"]["sensorPosition"]
    print("Misty's head sensor pressed at: ", sensor_pos)

    # https://docs.mistyrobotics.com/misty-ii/rest-api/api-reference/#playaudio
    if sensor_pos == "Chin":
        tts.synthesize_text_to_robot(misty, thanks, "end.wav")
        exit_function()
        # misty.DisplayImage("e_EcstacyStarryEyed.jpg", 1)
        # misty.PlayAudio("s_Awe2.wav", 50)

    if 'Head' in sensor_pos:
        pass


def voice_rec_callback(data):
    speech_to_text_result = ""
    print("voice_rec_callback START")
    if data["message"]["success"]:
        # misty.StopKeyPhraseRecognition()

        # misty.StopRecordingAudio()
        # accessing the wav file
        encoded_string = misty.GetAudioFile("capture_HeyMisty.wav", True).json()["result"]["base64"]
        misty.DeleteAudio("capture_HeyMisty.wav")
        # copying the file into "out.wav"
        wav_file = open("out.wav", "wb")
        wav_file.write(base64.b64decode(encoded_string))
        # we send the wav file to the BME stt
        try:
            # while we wait for the result,
            # we change the led to green to indicate that stuff is happening in the background

            misty.ChangeLED(0, 255, 0)
            misty.DisplayImage("e_Thinking4.jpg")

            res = asyncio.run(stt_api.ws_wav_recognition("out.wav", 4096))
            print("Result: ", res.split(";")[1])
            speech_to_text_result = res.split(";")[1]

        except Exception as e:
            print("ERROR")
            print(e)
        print("waiting for response")
        respond(speech_to_text_result)
    else:
        print("Unsuccessful voice recording")
    # print("unregistering...")
    # after responding, unregister events needed for the conversation
    time.sleep(1)
    print("voice_rec_callback DONE")


def respond(speech_to_text_result):
    global return_to_idle
    if ("kilép" or "befejez" or "vége" or "abba") in speech_to_text_result:
        tts.synthesize_text_to_robot(misty, "Köszönöm a játékot! Viszlát!", "mistynek.wav")
        exit_function()
        return_to_idle = True
    elif ("ez" or "mi" or "vagy") in speech_to_text_result:
        print("még egy játék!")
        hci_methods.recognizer(misty, speech_to_text_result)
    else:
        print("nem értettem, próbáld újra")


def exit_function():
    # Reset the robot's default state
    # IMPORTANT: If you have started any audio recordings, please stop them here etc.
    if misty is not None:
        misty.UnregisterAllEvents()
        misty.DisplayImage("e_DefaultContent.jpg", 1)
        misty.StopAvStreaming()

    print("Exiting program.")


def start_skill(misty_robot):
    global misty, return_to_idle
    misty = misty_robot

    try:
        #
        # tts.synthesize_text_to_robot(misty, "Elindult a felismerő játék", "response.wav")
        tts.synthesize_text_to_robot(misty, input_text, "response.wav")
        print("recognizer skill started")
        if misty is not None:
            misty.ChangeLED(255, 0, 255)
            misty.RegisterEvent("CapTouchSensor", Events.TouchSensor, callback_function=captouch_callback,
                                debounce=2000, keep_alive=True)
            misty.RegisterEvent("VoiceRec", Events.VoiceRecord, callback_function=voice_rec_callback, debounce=20,
                                keep_alive=False)
            misty.RegisterEvent("KeyPhraseRec", Events.KeyPhraseRecognized, debounce=20, keep_alive=False)
            misty.StartKeyPhraseRecognition()
            print("KeyPhraseRecognition started (for conversation)")

            # misty.UnregisterAllEvents()
        while True:
            time.sleep(1)
            if return_to_idle:
                return_to_idle = False
                exit_function(misty)
                time.sleep(2)
                return True
    except KeyboardInterrupt:
        exit_function()

    except Exception as e:
        print(e)
    # finally:
    #     return True


if __name__ == '__main__':
    misty_ip = "10.2.8.5"
    misty = Robot(misty_ip)
    start_skill(misty)
