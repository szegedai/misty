# import asyncio
# from mistyPy.Robot import Robot
# from main import init
# from main import datastream
# import Recorder as Recorder
# import SpeechToText as SpeechToText
#
#
# def misty_audio():
#     stream_params = Recorder.StreamParams()
#     recorder = Recorder.Recorder(stream_params)
#     recorder.create_recording_resources()
#
#     stt = SpeechToText.SpeechToTextAPI("wss://chatbot-rgai3.inf.u-szeged.hu/socket")
#     data_stream = datastream(recorder, stt)
#     try:
#         loop = asyncio.new_event_loop()
#         asyncio.set_event_loop(loop)
#         loop.run_until_complete(init(stt))
#         res = loop.run_until_complete(asyncio.gather(data_stream, stt.message_listener()))
#         print("KESZ")
#         print(res[1])
#
#     except KeyboardInterrupt as e:
#         print(e)
#         recorder.close_recording_resources()
#     finally:
#         recorder.close_recording_resources()
#
#
def asf(speech_to_text_result):
    if "még egyet" or "játszunk" or "még" or "játszani" or "szeretnék" in speech_to_text_result:
        print("asga")

if __name__ == '__main__':
    asf("játszunk szeretnék")


