# from huclip_the_text.model.clip import KeywordCLIP
# from PIL import Image
# import cv2
#
# if __name__ == '__main__':
#     model = KeywordCLIP()
#     image = cv2.imread("file.jpg")
#
#     best_answer, probability, all_answer = model.evaluate(Image.fromarray(image), "Ez egy telefon, vagy egy szivacs")
#     print('best_answer: ', {best_answer})
#     print('probabilty: ', {probability})
#     print(all_answer)
#

import wave
import contextlib

def length_audio():
    fname = "input.wav"
    with contextlib.closing(wave.open(fname, 'r')) as f:
        frames = f.getnframes()
        rate = f.getframerate()
        duration = frames / float(rate)
        print(duration)

if __name__ == '__main__':
    length_audio()
