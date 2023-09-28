import imitate
# import voiceCommand
import datetime
import threading
import time
from Misty import Misty
from mistyPy.Robot import Robot
from mistyPy.Events import Events
from mistyPy.EventFilters import EventFilters


def start():
    global misty

    # misty = Robot("10.2.8.5")
    misty = Misty("10.2.8.5")

    misty.RegisterEvent("StartImitating", Events.TouchSensor, debounce=500, callback_function=chinTouchCallback, \
                        condition=[EventFilters.CapTouchPosition.Chin], keep_alive=True)

    imitate.speak("Ha szeretnéd, hogy elkezdjelek utánozni érintsd meg egyszer az államat.", "hu-hu-x-kfl-local", ip=misty.ip)

def chinTouchCallback(data=None):
    global isImitating, lastTouch, thread1

    if data["message"]["isContacted"]:
        if lastTouch is None:
            lastTouch = datetime.datetime.now()

        delta = datetime.datetime.timestamp(lastTouch) - datetime.datetime.timestamp(datetime.datetime.now())
        delta = datetime.datetime.fromtimestamp(delta)
        
        lastTouch = datetime.datetime.now()

        if (delta.second == 59 and delta.microsecond < 900000) or (58 < delta.second < 59):
            try:
                imitate.stopImitating()
                misty.DisableCameraService()
                isImitating = False
            except Exception as e:
                print(e)
        elif not isImitating:
            try:
                isImitating = True
                thread1 = threading.Thread(target=imitate.init, args=(misty,), name="ImitateThread")
                # thread1 = threading.Thread(target=voiceCommand.init, args=(misty,), name="ImitateThread")
                thread1.run()
                lastTouch = None
            except Exception as e:
                print(e)


if __name__ == "__main__":
    global touchCount, lastTouch, isImitating, touch, misty


    touchCount = 0
    lastTouch = None
    isImitating = False
    ip = "10.2.8.5"
    misty = None

    while misty is None:
        try:
            start()
        except Exception as e:
            print(e)
            time.sleep(5)

