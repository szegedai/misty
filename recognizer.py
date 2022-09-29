# sample skill for misty, doesn't do anything special, can be used as a starting point for future skills
# start_sample_skill gets the robot as a parameter,
# so we can use its functions (we call this function from the idle skill)
# an infinite loop is required to not exit the function (or misty.KeepAlive() if we only use events)
# the function needs to return with True with the current skill switching implementation
import tts
import time
import base64
import asyncio

import Recorder
import SpeechToText
from main import init
from main import datastream
import hci_methods
from mistyPy.Robot import Robot
from mistyPy.Events import Events

return_to_idle = False
stt = SpeechToText.SpeechToTextAPI("wss://chatbot-rgai3.inf.u-szeged.hu/socket")
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


def respond(speech_to_text_result, recorder):
    global return_to_idle
    print(speech_to_text_result)
    if "kilép" or "befejez" or "vége" or "abba" in speech_to_text_result:
        tts.synthesize_text_to_robot(misty, "Köszönöm a játékot! Viszlát!", "mistynek.wav")
        exit_function()
        return_to_idle = True
    if "vagy" in speech_to_text_result:
        print("még egy játék!")
        hci_methods.recognizer(misty, speech_to_text_result)
        recording(recorder)
    else:
        print("nem értettem, próbáld újra")
        recording(recorder)


def exit_function():
    # Reset the robot's default state
    # IMPORTANT: If you have started any audio recordings, please stop them here etc.
    if misty is not None:
        misty.UnregisterAllEvents()
        misty.DisplayImage("e_DefaultContent.jpg", 1)
        misty.StopAvStreaming()

    print("Exiting program.")


def recording(recorder):
    data_stream = datastream(recorder, stt)
    try:
        misty.ChangeLED(200, 0,0)

        loop = asyncio.get_event_loop()
        res = loop.run_until_complete(asyncio.gather(data_stream, stt.message_listener()))

        misty.ChangeLED(0,200,0)
        respond(str.lower(res[1]), recorder)

    except KeyboardInterrupt as e:
        print(e)
        recorder.close_recording_resources()
    finally:
        recorder.close_recording_resources()


def start_skill(misty_robot, recorder):
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

            # loop = asyncio.new_event_loop()
            # asyncio.set_event_loop(loop)
            # loop.run_until_complete(init(stt))
            #
            # stream_params = Recorder.StreamParams()
            # RECORDER = Recorder.Recorder(stream_params)
            # RECORDER.create_recording_resources()

            recording(recorder)
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

    loop = asyncio.new_event_loop()
    asyncio.set_event_loop(loop)
    loop.run_until_complete(init(stt))

    stream_params = Recorder.StreamParams()
    recorder = Recorder.Recorder(stream_params)
    recorder.create_recording_resources()
    start_skill(misty, recorder)
