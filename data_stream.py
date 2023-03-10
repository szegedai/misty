"""
Get the audio_data with recorder then send to the speechtotext as a stream.
"""

import asyncio
import SpeechToText
import Recorder


async def init(stt_obj):
    stream_init = asyncio.create_task(stt_obj.ws_stream_init(44100, 2))
    await stream_init


async def datastream(recorder_obj, stt_obj):
    print("Datastream started")
    while True:
        audio_data = recorder_obj.read_audio_data_from_stream()
        asd = await stt_obj.ws_stream_send(audio_data)
        if asd:
            return ""

if __name__ == "__main__":
    stream_params = Recorder.StreamParams()
    recorder = Recorder.Recorder(stream_params)
    recorder.create_recording_resources()

    stt = SpeechToText.SpeechToTextAPI("wss://chatbot-rgai3.inf.u-szeged.hu/socket")
    data_stream = datastream(recorder, stt)
    try:
        loop = asyncio.new_event_loop()
        asyncio.set_event_loop(loop)
        loop.run_until_complete(init(stt))
        res = loop.run_until_complete(asyncio.gather(data_stream, stt.message_listener()))
        print("KESZ")
        print(res[1])

    except KeyboardInterrupt as e:
        print(e)
        recorder.close_recording_resources()
    finally:
        recorder.close_recording_resources()