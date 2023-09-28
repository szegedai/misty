import cv2 as cv
import websocket
import requests
import numpy as np
import mediapipe as mp
import time
import threading
import queue
# import timeit
# from sixdrepnet import SixDRepNet
from mistyPy.Events import Events
# from mistyPy.EventFilters import EventFilters

def stopImitating(data : dict=None) -> None:
    """ Misty stops imitating and all related websockets are destroyed and events unregistered.

    This functian can also be used as a callback function.

    Parameters
    ----------
    data: dict, optional
        The data from the event calling this (default is None)
    """

    global run, socket, misty

    defaultPose()

    cv.destroyAllWindows()

    run = False

    while True:
        try:
            req = requests.post(f"http://{misty.ip}/api/videostreaming/stop")
            break
        except Exception as e:
            print(e)

    print("Video streaming successfully stopped")

    misty.DisableCameraService()

    misty.UnregisterEvent("IMU")

    while True:
        try:
            socket.close()
            break
        except Exception as e:
            print(e)

    print("Socket is closed")


    speak("Nem utánozlak tovább.", "hu-hu-x-kfl-local", 1)


def getStream() -> None:
    """ Collects the video streaming data and puts in a LIFO queue for the pose handler thread. """

    while run:
        stream = socket.recv()
        streamQueue.put(stream)


def showDetection(image : np.ndarray, results: object) -> None:
    """ Draws the detected landmarks on the current frame of the video stream.

    Parameters
    ----------
    image: numpy array
        The current frame of the video stream
    results:
        The object containing the detected landmarks
    """


    image.flags.writeable = True
    image = cv.cvtColor(image, cv.COLOR_RGB2BGR)

    mp_drawing.draw_landmarks(
        image,
        results.pose_landmarks,
        mp_pose.POSE_CONNECTIONS,
        landmark_drawing_spec=mp_drawing_styles.get_default_pose_landmarks_style())

    cv.imshow("cam", image)
    cv.waitKey(1)


def defaultPose() -> None:
    """ Sets Misty back to its default pose """

    global moving

    moving = True

    misty.MoveHead(pitch=0, roll=0, yaw=0, duration=.1)
    misty.MoveArms(leftArmPosition=90, rightArmPosition=90, duration=.1)

    time.sleep(0.1)

    moving = False


def handleHand(landmarks : dict) -> None:
    """ Determines the target positions for Misty's arms according to the landmarks then moves them.

    Parameters
    ----------
    landmarks: dict
        The dictionary containing the landmarks of the persons arms and head. Every key is camel case made up of the side and the body part like: leftElbow
    """

    global moving

    lastPosition = hands.copy()

    if landmarks["leftShoulder"].y <= landmarks["leftElbow"].y:
        if landmarks["leftShoulder"].y >= landmarks["leftWrist"].y:
            hands["left"] = 20
        else:
            hands["left"] = 90
    else:
        hands["left"] = -90

    if landmarks["rightShoulder"].y <= landmarks["rightElbow"].y:
        if landmarks["rightShoulder"].y >= landmarks["rightWrist"].y:
            hands["right"] = 20
        else:
            hands["right"] = 90
    else:
        hands["right"] = -90

    for hand in hands:
        if hands[hand] != lastPosition[hand]:
            moving = True

    if moving:
        misty.MoveArms(hands["left"], hands["right"], duration=.1)
        # time.sleep(.15)
        moving = False


def handleHead(landmarks : dict) -> None:
    """ Determines the target pitch, yaw, roll for Misty's head and then moves it.

    Parameters
    ----------
    landmarks: dict
        The dictionary containing the landmarks of the persons arms and head. Every key is camel case made up of the side and the body part like: leftElbow
    """

    global moving

    yaw = None
    pitch = None

    if landmarks is None:
        defaultPose()
        return

    if abs(landmarks["leftShoulder"].x - landmarks["rightShoulder"].x) < \
        max(landmarks["leftShoulder"].x - landmarks["leftMouth"].x, landmarks["rightShoulder"].x - landmarks["rightMouth"].x):
        
        return 

    if landmarks["leftEar"].x < landmarks["nose"].x > landmarks["rightEar"].x and \
        abs(landmarks["leftEar"].x - landmarks["rightEar"].x) <= \
        min(abs(landmarks["nose"].x - landmarks["leftEar"].x), abs(landmarks["nose"].x - landmarks["rightEar"].x)) * 2:
        
        yaw = -90

    elif landmarks["leftEar"].x > landmarks["nose"].x < landmarks["rightEar"].x and \
        abs(landmarks["leftEar"].x - landmarks["rightEar"].x) <= \
        min(abs(landmarks["nose"].x - landmarks["leftEar"].x), abs(landmarks["nose"].x - landmarks["rightEar"].x)) * 2:
        
        yaw = 90

    elif abs(landmarks["leftEye"].y - landmarks["nose"].y) <= 0.015 and abs(landmarks["rightEye"].y - landmarks["nose"].y) <= 0.015 :
        
        pitch = -40

    elif min(abs(landmarks["nose"].y - landmarks["leftEar"].y), abs(landmarks["nose"].y - landmarks["rightEar"].y)) > \
        max(abs(landmarks["nose"].y - landmarks["leftMouth"].y), abs(landmarks["nose"].y - landmarks["rightMouth"].y)):
        
        pitch = 25

    if not(pitch is None and yaw is None):
        moving = True

        misty.MoveHead(pitch=pitch, yaw=yaw, duration=1)

        time.sleep(2.5)

        defaultPose()

        time.sleep(1.5)

        moving = False

    roll = (landmarks["rightEar"].y - landmarks["leftEar"].y) * 1000

    misty.MoveHead(roll=roll, duration=.01)


def handleTurnAround(landmarks : dict) -> None:
    """ Misty makes a full 360° turn if the left and right shoulders are switched on the x axis. 

    Parameters
    ----------
    landmarks: dict
        The dictionary containing the landmarks of the persons arms and head. Every key is camel case made up of the side and the body part like: leftElbow
    """

    global moving, turning, initialHeading

    if landmarks is None:
        defaultPose()
        return

    if landmarks["leftShoulder"].x > landmarks["rightShoulder"].x:
        moving = True

        initialHeading = currentHeading

        misty.Drive(linearVelocity=0, angularVelocity=50)

        time.sleep(2)
        
        turning = True

        while turning:
            pass

        misty.Halt()

        time.sleep(0.5)

        while currentHeading != initialHeading:
            asd = misty.DriveArc(initialHeading, 0, 500, False)
            print(asd.json())


        time.sleep(1)

        moving = False

def handlePose(results: object) -> None:
    """ Sorts the detected landmarks in an easier to read and use dictionary and calls the handler functions.

    Parameters: object
        The object containing the detected landmarks
    """

    landmarks = results.pose_landmarks.ListFields()

    landmarks = {
        "nose": landmarks[0][1][0],
        "leftEye": landmarks[0][1][5],
        "leftEar": landmarks[0][1][8],
        "leftMouth": landmarks[0][1][10],
        "rightEye": landmarks[0][1][2],
        "rightEar": landmarks[0][1][7],
        "rightMouth": landmarks[0][1][9],
        "leftShoulder": landmarks[0][1][12],
        "leftElbow": landmarks[0][1][14],
        "leftWrist": landmarks[0][1][16],
        "rightShoulder": landmarks[0][1][11],
        "rightElbow": landmarks[0][1][13],
        "rightWrist": landmarks[0][1][15]
    }

    handleTurnAround(landmarks)

    handleHead(landmarks)

    handleHand(landmarks)


def imitate() -> None:
    """ Converts the frames of the stream data to a numpy array and calls the pose handler with the detected pose landmarks. """

    with mp_pose.Pose(min_detection_confidence=0.9, min_tracking_confidence=0.9) as pose:
        while run:
            stream = streamQueue.get()
            with streamQueue.mutex:
                streamQueue.queue.clear()

            if not moving:
                try:
                    # start = timeit.default_timer()
                    array = np.asarray(bytearray(stream), dtype=np.uint8)
                    image = cv.imdecode(array, 1)
                    image.flags.writeable = False

                    image = cv.cvtColor(image, cv.COLOR_BGR2RGB)

                    results = pose.process(image)

                    if results.pose_landmarks is not None:
                        if not moving:
                            handlePose(results)
                    else:
                        defaultPose()

                    showDetection(image, results)
                    # print(timeit.default_timer() - start)
                except Exception as e:
                    print(e)


def speak(text, voice="hu-hu-x-kfl-local", utteranceId=None, ip=None) -> None:
    if ip is None:
        ip = misty.ip

    try:
        requests.post(f"http://{ip}/api/tts/speak", json={"text": text,
                      "utteranceId": utteranceId, "voice": voice})
    except Exception as e:
        print(e)


def IMUSensorCallback(data : dict) -> None:
    """ Handles the information from Misty's IMU Sensor.

    Parameters
    ----------
    data: dict
        The data from the event calling this (default is None)
    """

    global initialHeading, currentHeading, turning

    currentHeading = int(data["message"]["yaw"])

    if turning and initialHeading - 4 < currentHeading < initialHeading + 4:
        turning = False


def speakCallback(data : dict) -> None:
    """ Handles the event data when Misty stops speaking.

    Parameters
    ----------
    data: dict
        The data from the event calling this (default is None)
    """

    global run

    if data["message"]["utteranceId"] == '0':
        time.sleep(1)
        misty.ChangeLED(0, 0, 255)
        run = True

    if data["message"]["utteranceId"] == '1':
        misty.UnregisterEvent("Speak")
        time.sleep(1)
        misty.ChangeLED(100, 70, 160)


def init(robot):
    global run, socket, misty, moving, turning, initialHeading,streamQueue, hands, mp_pose, mp_drawing, mp_drawing_styles

    run = True
    socket = None
    misty = robot
    moving = False
    turning = False
    initialHeading = None
    streamQueue = queue.LifoQueue()
    hands = {
        "left": 90,
        "right": 90
    }
    mp_pose = mp.solutions.pose
    mp_drawing = mp.solutions.drawing_utils
    mp_drawing_styles = mp.solutions.drawing_styles

    streamPort = 5678
    req = None

    defaultPose()

    misty.EnableCameraService()
    while req is None or req.json()["status"] != "Success":
        try:
            req = requests.post(f"http://{misty.ip}/api/videostreaming/start",
                                json={"Port": streamPort, "Rotation": 90, "Width": 500, "Height": 625, "Quality": 20})
        except Exception as e:
            print(e)
            time.sleep(5)

    print("Video streaming started successfully")

    while socket is None:
        try:
            socket = websocket.create_connection(
                f"ws://{misty.ip}:{streamPort}")
        except Exception as e:
            time.sleep(5)
            print(e)

    print("Socket is open")


    misty.RegisterEvent("IMU", Events.IMU, debounce=10, callback_function=IMUSensorCallback, \
                         keep_alive=True)


    misty.RegisterEvent("Speak", Events.TextToSpeechComplete, debounce=500, callback_function=speakCallback, \
                        keep_alive=True)

    speak("Amikor a fény a mellkasomon kékre vált elkezdelek utánozni. Ha szeretnéd, hogy befejezzem érintsd meg kétszer az államat.", "hu-hu-x-kfl-local", 0)

    while not run:
        pass

    try:
        t1 = threading.Thread(target=getStream, name="StreamThread")
        t1.start()

        t2 = threading.Thread(target=imitate, name="PoseHandlerThread")
        t2.start()

    except KeyboardInterrupt:
        stopImitating()
