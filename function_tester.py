
import time
import cv2
import base64
import numpy as np

from numpy.linalg.linalg import norm
from cvzone.HandTrackingModule import HandDetector

#
# def take_pic():
#     data = misty.TakePicture(base64=True, fileName="test_photo", width=3120, height=2000)
#     # print()
#     with open("file.jpg", "wb") as pic:
#         pic.write(base64.b64decode(data.json()['result']['base64']))
#     # misty.DisplayImage("test_photo.jpg")
    # misty.DeleteImage("test_photo.jpg")
    # misty.DisplayImage("e_Amazement.jpg")

#
# def stream(misty_ip, misty):
#     misty.EnableAvStreamingService()
#     misty.StartAvStreaming("rtspd:1936", 640, 480)
#
#     # And connecting to it via openCV
#
#     while True:
#         try:
#             if misty is not None:
#                 print("Using Misty's camera")
#                 print("rtsp://" + misty_ip + ":1936")
#                 vcap = cv2.VideoCapture("rtsp://" + misty_ip + ":1936", cv2.CAP_FFMPEG)
#             else:
#                 # If a Misty Robot IP address is not given
#                 # And connecting to it via openCV
#                 print("Trying to use the default camera of the computer")
#                 vcap = cv2.VideoCapture(0)
#
#             ret, frame = vcap.read()
#             if not ret:
#                 print("Stream is not available")
#                 time.sleep(1)
#             else:
#                 break
#         except Exception as e:
#             print("Unkown error")
#             print(e)
#             time.sleep(1)

#
# def cv():
#     pTime = 0
#     cTime = 0
#     cap = cv2.VideoCapture(0)
#     # detector = HandDetector()
#
#     while True:
#         success, img = cap.read()
#         # img = detector.findHands(img)
#
#         cTime = time.time()
#         fps = 1 / (cTime - pTime)
#         pTime = cTime
#
#         cv2.putText(img, str(int(fps)), (10, 70), cv2.FONT_HERSHEY_COMPLEX, 3, (255, 0, 255), 3)
#
#         cv2.imshow("Image", img)
#         cv2.waitKey(1)
#
#
# def rockPaperScissors(landmarks, detector):
#
#     benching_distance_back = landmarks[10][0:2]
#     benching_distance_front = landmarks[0][0:2]
#
#     index_finger_mcp = landmarks[5][0:2]
#     index_finger = landmarks[8][0:2]
#
#     middle_finger_mcp = landmarks[9][0:2]
#     middle_finger = landmarks[12][0:2]
#
#     ring_finger_mcp = landmarks[13][0:2]
#     ring_finger = landmarks[16][0:2]
#
#     pinky_finger_mcp = landmarks[17][0:2]
#     pinky_finger = landmarks[20][0:2]
#
#     euk_index = detector.findDistance(index_finger_mcp, index_finger)[0]
#     euk_middle = detector.findDistance(middle_finger_mcp, middle_finger)[0]
#     euk_ring = detector.findDistance(ring_finger_mcp, ring_finger)[0]
#     euk_pinky = detector.findDistance(pinky_finger_mcp, pinky_finger)[0]
#
#     euk_bench_back = detector.findDistance(benching_distance_back, middle_finger_mcp)[0]
#     euk_bench_front = detector.findDistance(benching_distance_front, middle_finger_mcp)[0]*0.75
#
#     euk_bench = euk_bench_back
#
#     if euk_bench_front > euk_bench_back:
#         euk_bench = euk_bench_front
#
#     print(euk_index, "\n", euk_middle, "\n euk_bench back: ", euk_bench_back, "\n euk_bench_front", euk_bench_front)
#
#     if (euk_index and euk_middle) < euk_bench:
#         return "kő"
#     elif (euk_ring and euk_pinky) < euk_bench < (euk_middle and euk_index):
#         return "olló"
#     else:
#         return "papír"
#
#
#     # return euk_index, euk_middle, euk_ring, euk_pinky, euk_bench
#
#
# def image_landmarks(file_name):
#     image = cv2.imread(file_name)
#     detector = HandDetector(detectionCon=0.8, maxHands=1)
#     hands, img = detector.findHands(image)
#     if hands:
#         hand1 = hands[0]
#         lmList1 = hand1["lmList"]  # List of 21 Landmark points
#         bbox1 = hand1["bbox"]  # Bounding box info x,y,w,h
#         centerPoint1 = hand1['center']  # center of the hand cx,cy
#         handType1 = hand1["type"]  # Handtype Left or Right
#
#         fingers1 = detector.fingersUp(hand1)
#         print(rockPaperScissors(landmarks=lmList1, detector=detector))
#
#     cv2.imshow("Image", img)
#     cv2.waitKey(1)
#
#
#
#
# def base():
#     cap = cv2.VideoCapture(0)
#     detector = HandDetector(detectionCon=0.8, maxHands=2)
#     while True:
#         # Get image frame
#         success, img = cap.read()
#         # Find the hand and its landmarks
#         hands, img = detector.findHands(img)  # with draw
#         # hands = detector.findHands(img, draw=False)  # without draw
#
#         if hands:
#             # Hand 1
#             hand1 = hands[0]
#             lmList1 = hand1["lmList"]  # List of 21 Landmark points
#             bbox1 = hand1["bbox"]  # Bounding box info x,y,w,h
#             centerPoint1 = hand1['center']  # center of the hand cx,cy
#             handType1 = hand1["type"]  # Handtype Left or Right
#
#             fingers1 = detector.fingersUp(hand1)
#             # print(lmList1[0])
#             # print(lmList1[0][0:2])
#
#             # euk_index, euk_middle, euk_ring, euk_pinky, euk_bench = rockPaperScissors(lmList1, detector)
#             # print(euk_index, "\n", euk_middle, "\n", euk_ring, "\n", euk_pinky, "\n", euk_bench, "\n\n\n")
#             print(rockPaperScissors(landmarks=lmList1, detector=detector))
#             if len(hands) == 2:
#                 # Hand 2
#                 print("hand 2")
#                 hand2 = hands[1]
#                 lmList2 = hand2["lmList"]  # List of 21 Landmark points
#                 bbox2 = hand2["bbox"]  # Bounding box info x,y,w,h
#                 centerPoint2 = hand2['center']  # center of the hand cx,cy
#                 handType2 = hand2["type"]  # Hand Type "Left" or "Right"
#
#                 fingers2 = detector.fingersUp(hand2)
#
#                 # # Find Distance between two Landmarks. Could be same hand or different hands
#                 # try:
#                 #     length, info, img = detector.findDistance(lmList1[0], lmList1[8], img)  # with draw
#                 #     print(length)
#                 # # length, info = detector.findDistance(lmList1[8], lmList2[8])  # with draw
#                 # except Exception as e:
#                 #     continue
#
#         # Display
#         cv2.imshow("Image", img)
#         cv2.waitKey(1)
#     cap.release()
#     cv2.destroyAllWindows()
#

if __name__ == '__main__':
    misty_ip = '10.2.8.5'
    print(40000//4096)
    print(40000/4096)
    print(45440%2)
    # misty = Robot(misty_ip)
    # misty.RestartRobot(True, True)
    # image_landmarks()
    # stream(misty_ip, misty)
    # cv()
