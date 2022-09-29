"""
Recorder uses pyaudio to record sound from mic.
"""
from dataclasses import dataclass, asdict
import pyaudio


@dataclass
class StreamParams:
    format: int = pyaudio.paInt16
    channels: int = 1
    rate: int = 44100
    frames_per_buffer: int = 4096
    input: bool = True
    output: bool = False

    def to_dict(self) -> dict:
        return asdict(self)


class Recorder:

    def __init__(self, stream_params: StreamParams) -> None:
        self.stream_params = stream_params
        self._pyaudio = None
        self._stream = None

    def create_recording_resources(self) -> None:
        self._pyaudio = pyaudio.PyAudio()
        self._stream = self._pyaudio.open(**self.stream_params.to_dict())

    def read_audio_data_from_stream(self) -> None:
        audio_data = self._stream.read(self.stream_params.frames_per_buffer)
        return audio_data

    def close_recording_resources(self) -> None:
        print("stop")
        self._stream.close()
        self._pyaudio.terminate()
