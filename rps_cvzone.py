import cv2
import random
from cvzone.HandTrackingModule import HandDetector


def rock_paper_scissors(landmarks, detector):

    benching_distance_back = landmarks[10][0:2]
    benching_distance_front = landmarks[0][0:2]

    index_finger_mcp = landmarks[5][0:2]
    index_finger = landmarks[8][0:2]

    middle_finger_mcp = landmarks[9][0:2]
    middle_finger = landmarks[12][0:2]

    ring_finger_mcp = landmarks[13][0:2]
    ring_finger = landmarks[16][0:2]

    pinky_finger_mcp = landmarks[17][0:2]
    pinky_finger = landmarks[20][0:2]

    euk_index = detector.findDistance(index_finger_mcp, index_finger)[0]
    euk_middle = detector.findDistance(middle_finger_mcp, middle_finger)[0]
    euk_ring = detector.findDistance(ring_finger_mcp, ring_finger)[0]
    euk_pinky = detector.findDistance(pinky_finger_mcp, pinky_finger)[0]
    # The bench distance can be 2 one is calculated from the metacarpal
    # the other one is the distance between the wrist
    # and the middle finger's MCP * 0.75
    euk_bench_back = detector.findDistance(benching_distance_back, middle_finger_mcp)[0]
    euk_bench_front = detector.findDistance(benching_distance_front, middle_finger_mcp)[0]*0.65

    euk_bench = euk_bench_back

    if euk_bench_front > euk_bench_back:
        euk_bench = euk_bench_front

    # print(euk_index, "\n", euk_middle, "\n euk_bench back: ", euk_bench_back,
    # "\n euk_bench_front", euk_bench_front)
    # If the index and the middle fingers are closed it's going to be rock,
    # if the ring and pinky fingers are smaller
    # than the benching distance than it's scissors else its paper
    if (euk_index and euk_middle) < euk_bench:
        return "rock"
    if (euk_ring and euk_pinky) < euk_bench < (euk_middle and euk_index):
        return "scissors"
    return "paper"


def image_landmarks(file_name):
    image = cv2.imread(file_name)
    detector = HandDetector(detectionCon=0.8, maxHands=1)
    hands, img = detector.findHands(image)
    if hands:
        hand1 = hands[0]
        lmList1 = hand1["lmList"]  # List of 21 Landmark points
        # print(rockPaperScissors(landmarks=lmList1, detector=detector))
        return rock_paper_scissors(landmarks=lmList1, detector=detector)


MOVES = ['rock', 'paper', 'scissors']


def get_random_move() -> str:
    """Returns a random RPS move as sring."""

    return MOVES[random.randrange(0, 3)]


def get_winning_move(enemy_move: str) -> str:
    """Returns the RPS move that wins against the paramater move."""

    if enemy_move == "rock":
        return "paper"
    if enemy_move == "paper":
        return "scissors"
    if enemy_move == "scissors":
        return "rock"
    return None


def get_winner(player1_move: str, player2_move: str) -> int:
    """Determines the winner by two RPS moves.

    Args:
        player1_move: Label of the first player's move.
        player2_move: Label of the second player's move.

    Returns:
        1 if the first player wins, 2 if the second player wins, 0 if the result
        is a draw.
    """
    if player1_move == player2_move:
        return 0

    if get_winning_move(player1_move) != player2_move:
        return 1
    return 2


def get_move_hun(move: str) -> str:
    """Returns the Hungarian word for the chosen move.

    Only used in text-to-speech.
    """
    if move == "rock":
        return "követ"
    elif move == "paper":
        return "papírt"
    elif move == "scissors":
        return "ollót"