import sys
# NOTE: https://github.com/MistyCommunity/Python-SDK
from mistyPy.Robot import Robot
from mistyPy.Events import Events

import asyncio

import cv2
import time
import tts

import hci_methods
from time import gmtime, strftime

import base64

import subprocess
import threading

stream_available = False
continue_game = False

misty = None
vcap = None
result = None
frame = None
message = ''
thanks = 'Köszönöm a játékot'
input_text = 'Sziasztok! Én vagyok a miszti robot, aki tárgyakat képes felismerni. Mutass nekem tárgyakat és tegyél fel nekem találós kérdést a tárggyal kapcsolatban. Például, ha felmutatsz egy almát megkérdezheted, hogy "Almát vagy banánt mutatok?". Simogasd meg a fejem s tedd fel a kérdésed.'

first_game = True
recording = False
input_mode = False

@asyncio.coroutine
def send_from_stdin(loop):
    global input_mode
    global message
    while True:
        if input_mode:
            message = yield from loop.run_in_executor(None, input, ">")
            hci_methods.default_image_classification_algorithm(frame, misty, message)
            print(message)
            input_mode = False

# Handles recording stills and video via keyboard input
def image_keyboard_operations(image):
    global recording, result, input_mode
    
    key = cv2.waitKey(1)
    # if P key is pressed
    if key%256 == 112:
        img_name = "img_{}.png".format(strftime("%Y%m%d%H%M%S"))
        cv2.imwrite(img_name, image)
        cv2.imshow("1", image)
    
    # if R key is pressed
    if key%256 == 114:
         if recording is False:
            recording = True
         else:
            recording = False
    
    # if the spacebar is pressed
    if key%256 == 32:
        print("Input mode")
        input_mode = True
        
    if key%256 == 27:
        print("Exiting")
        exit_function()
    
    if recording is True:
        print("Recording")
        result.write(image)

# Robot event handling
def remove_closed_events():
    events_to_remove = []

    for event_name, event_subscription in misty.active_event_registrations.items():
        if not event_subscription.is_active:
            events_to_remove.append(event_name)

    for event_name in events_to_remove:
        print(f"Event connection has closed for event: {event_name}")
        misty.UnregisterEvent(event_name)

def voice_rec_callback(data):
    global misty
    global stream_available
    global vcap
    global continue_game
    global frame

    print("playback start voice_rec_callback")
    misty.PlayAudio("capture_Dialogue.wav")
    time.sleep(5)
    print("audio end voice_rec_callback")
    
    try:
        encoded_string = misty.GetAudioFile("capture_Dialogue.wav", True).json()["result"]["base64"]
        
        with open("out.wav", "wb") as wav_file:
            wav_file.write(base64.b64decode(encoded_string))
            
    except Exception as e:
        print(e)
        print("Error")
    
    
    x = subprocess.check_output(['python stt.py "wss://chatbot-rgai3.inf.u-szeged.hu/socket" "out.wav"'], shell=True)
    print(x)
    speech_to_text_result = x.decode("utf-8").split(":")[1].split("\\n")[0].strip()
    
    print("stt_result:", speech_to_text_result)
    hci_methods.default_image_classification_algorithm(frame, misty, speech_to_text_result)

    if not ("kilép" in speech_to_text_result or "befejez" in speech_to_text_result or "vége" in speech_to_text_result or "abba" in speech_to_text_result):
        
        print("Még egy játék!!!")
        misty.EnableAvStreamingService()
        misty.StartAvStreaming("rtspd:1936", 640, 480)
        
        # TODO: Ezt kiszervezni majd kulon fuggvenybe!
        avstream_connected = False

        while(avstream_connected == False):
            try:
                if misty is not None:
                    print("Using Misty's camera")
                    vcap = cv2.VideoCapture("rtsp://" + misty_ip_address + ":1936", cv2.CAP_FFMPEG)
                else:
                    # If a Misty Robot IP address is not given
                    # And connecting to it via openCV
                    print("Trying to use the default camera of the computer")
                    vcap = cv2.VideoCapture(0)


                # Save captured frame in a global variable
                # This is some pretty shitty workaround but it does the trick...
                # for now that is

                ret, frame = vcap.read()
                if ret == False:
                    print("Stream is not available")
                    time.sleep(1)
                else:
                    avstream_connected = True
                    stream_available = True
            except Exception as e:
                print("Unkown error")
                print(e)
                time.sleep(1)
            
            continue_game = True
        
            
    else:
        tts.synthesize_text_to_robot(misty, "Köszönöm a játékot! Viszlát!", "mistynek.wav")
        continue_game = False
        # TODO: Exiting gracefully

def captouch_callback(data):
    global input_mode
    global first_game

    # https://docs.mistyrobotics.com/misty-ii/javascript-sdk/code-samples/#captouch
    sensor_pos = data["message"]["sensorPosition"]
    print("Misty's head sensor pressed at: ", sensor_pos)
    
    # https://docs.mistyrobotics.com/misty-ii/rest-api/api-reference/#playaudio
    if sensor_pos == "Chin":
        tts.synthesize_text_to_robot(misty, thanks, "end.wav")
        exit_function()
        # misty.DisplayImage("e_EcstacyStarryEyed.jpg", 1)
        # misty.PlayAudio("s_Awe2.wav", 50)
    
    if first_game:
        if 'Head' in sensor_pos:
            try:
                misty.DisplayImage('e_Thinking.jpg')
                misty.ChangeLED(255, 0, 0)
                
                first_game = False
                print("stopping avstream")
                stream_available = False
                
                misty.StopAvStreaming()
                misty.DisableAvStreamingService()
                
                #misty.StartKeyPhraseRecognition()
                #print("keyphrase")
                # Params:
                # overwriteExisting: bool = None, silenceTimeout: int = None, 
                # maxSpeechLength: int = None, requireKeyPhrase: bool = None,
                # speechRecognitionGrammar: str = None
                print("capturing speech")
                ret = misty.CaptureSpeech(True, None, None, False)
                print("CaptureSpeech ret:", ret)
            except Exception as e:
                print(e)
    else:
        try:
            print("stopping avstream")
            stream_available = False
            
            misty.StopAvStreaming()
            misty.DisableAvStreamingService()
            
            #misty.StartKeyPhraseRecognition()
            #print("keyphrase")
            # Params:
            # overwriteExisting: bool = None, silenceTimeout: int = None, 
            # maxSpeechLength: int = None, requireKeyPhrase: bool = None,
            # speechRecognitionGrammar: str = None
            print("capturing speech")
            ret = misty.CaptureSpeech(True, None, None, False)
            print("CaptureSpeech ret:", ret)
        except Exception as e:
            print(e)

    #tts.synthesize_text_to_robot(misty, "Még egyet szeretnél? Mondd azt gyorsan, hogy még egyet!", "mistynek.wav")
    #time.sleep(4)
        
    #try:
        #print("stopping avstream")
        #stream_available = False
        
        #misty.StopAvStreaming()
        #misty.DisableAvStreamingService()
        
        ##misty.StartKeyPhraseRecognition()
        ##print("keyphrase")
        ## Params:
        ## overwriteExisting: bool = None, silenceTimeout: int = None, 
        ## maxSpeechLength: int = None, requireKeyPhrase: bool = None,
        ## speechRecognitionGrammar: str = None
        #print("capturing speech")
        #ret = misty.CaptureSpeech(True, None, None, False)
        #print("CaptureSpeech ret:", ret)
    #except Exception as e:
        #print(e)
    ##if 'Head' in sensor_pos:
        ##print("Input mode")
        ##input_mode = True


def start_robot_connection(misty_ip_address=None):
    global misty
    global vcap
    global result
    global frame
    global continue_game
    try:
        if misty_ip_address is not None:
            print("Connecting to Misty Robot")
            misty = Robot(misty_ip_address)

            tts.synthesize_text_to_robot(misty, input_text, 'input.wav')
            
            # Registering events
            misty.RegisterEvent("CapTouchSensor", Events.TouchSensor,
                callback_function = captouch_callback, debounce = 2000, keep_alive = True)
            
            misty.RegisterEvent("voice_cap", Events.VoiceRecord, 
                callback_function = voice_rec_callback, debounce = 10, keep_alive = True)
            
            # Although the following call was in the original example code...
            # DO NOT USE THIS FUNCTION, AS IT CONTAINS A WHILE TRUE LOOP IN WHICH YOUR CODE MIGHT REMAIN STUCK
            #misty.KeepAlive()
            
            # Starting Misty's audio-video stream
            # https://docs.mistyrobotics.com/misty-ii/rest-api/api-reference/#startavstreaming
            misty.EnableAvStreamingService()
            misty.StartAvStreaming("rtspd:1936", 640, 480)

        # And connecting to it via openCV
        avstream_connected = False

        while(avstream_connected == False):
            try:
                if misty is not None:
                    print("Using Misty's camera")
                    vcap = cv2.VideoCapture("rtsp://" + misty_ip_address + ":1936", cv2.CAP_FFMPEG)
                else:
                    # If a Misty Robot IP address is not given
                    # And connecting to it via openCV
                    print("Trying to use the default camera of the computer")
                    vcap = cv2.VideoCapture(0)
                    
                ret, frame = vcap.read()
                if ret == False:
                    print("Stream is not available")
                    time.sleep(1)
                else:
                    avstream_connected = True
            except Exception as e:
                print("Unkown error")
                print(e)
                time.sleep(1)
        
        
        frame_width = int(vcap.get(3))
        frame_height = int(vcap.get(4))
   
        if misty is not None:
            size = (frame_height, frame_width)
        else:
            size = (frame_width, frame_height)
        
        print(f"size: {size}")
        
        
        fourcc = cv2.VideoWriter_fourcc(*'MJPG')
        result = cv2.VideoWriter('out.avi', 
                         fourcc,
                         30, size)
        # Reading frames, while true...
        # And also handling Misty's events
        cnt = 0
        while True:
            cnt += 1
            if misty is not None:
                remove_closed_events()    
            
            if stream_available is True:
                ret, frame = vcap.read()
                if ret == False:
                    print("Frame is empty")
                    break
                else:
                    if misty is not None:
                        frame = cv2.rotate(frame, cv2.cv2.ROTATE_90_CLOCKWISE)
                        # cv2.imshow('VIDEO', frame)
                        image_keyboard_operations(frame)
                        
                        if continue_game is True:
                            continue_game = False
                            download_thread = threading.Thread(target=captouch_callback, name="Downloader", args=[{"message" : {"sensorPosition" : "HeadFront"}}])
                            download_thread.start()
                    #print(hci_methods.default_image_classification_algorithm(frame))
                
                        
            
    except Exception as e:
        print(e)
        
    finally:
        exit_function()

def exit_function():
    # Reset the robot's default state
    # IMPORTANT: If you have started any audio recordings, please stop them here etc.
    if misty is not None:
        misty.UnregisterAllEvents()
        misty.DisplayImage("e_DefaultContent.jpg", 1)
        misty.StopAvStreaming()
        misty.DisableAvStreamingService()
    
    # OpenCV
    
    if vcap is not None:
        vcap.release()
    if result is not None:
        result.release()
    cv2.destroyAllWindows()
        
    print("Exiting program.")

# The main function
if __name__ == "__main__":
    misty_ip_address = None
    
    if(len(sys.argv) > 1):
        misty_ip_address = sys.argv[1]

    loop = asyncio.get_event_loop()
    #coro = loop.create_task(start_robot_connection(misty_ip_address))
    loop.run_in_executor(None, start_robot_connection, misty_ip_address)
    
    loop.create_task(send_from_stdin(loop))
    
    loop.run_forever()
