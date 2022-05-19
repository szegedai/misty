import asyncio
import websockets
import signal
import wave
import sys
import signal

class SpeechToTextAPI():
    ws = None
    uri = ""
    sample_rate = 0 # the audio sample rate (e.g. 44100 for 44,1kHz)
    frame_size = 0 # the size of one audio frame (e.g. 2 for 16 bit encoding)
    
    frames_sent = 0
    
    is_sending = False
    
    def __init__(self, stt_uri):
        self.uri = stt_uri
    
    async def message_listener(self):
        i = 0
        while True:
            # Yield control and give other async coroutines a chance to run
            await asyncio.sleep(0)
            #print("message_listener")
            #i+= 1
            #if i % 100 == 0:
                #print("message_listener")
            if self.ws is not None:
                print("awaiting message")
                message = await self.ws.recv()
                print("msg: ", message)
    
    async def ws_check_connection(self):
        async for ws in websockets.connect(self.uri):
            try:
                pong_waiter = await ws.ping()
                await pong_waiter
                return True
            except:
                return False
    
    async def ws_stream_init(self, sample_rate, frame_size):
        try:
            self.ws = await websockets.connect(self.uri)
            
            print("Binding model")
            await self.ws.send("control|bind-request;general_hu")
            #resp = await self.ws.recv()
            #print(resp)
            #print("Starting streaming")
            print("speechtotext.py sending control|start to the websocket server")
            await self.ws.send("control|start;" + str(self.sample_rate) + ";-1;0")
            #resp = await self.ws.recv()
            #print(resp)
            self.is_sending = True
            
        except Exception as e:
            print(e)
            print("Unable to connect to the websocket server!")
            
    async def ws_stream_send(self, audio_frame):
        #return "stt_api ws_stream_send " +  str(audio_frame)
        if self.ws is not None:
            if len(audio_frame) > 1:
                # TODEBUG: Trying to stream bytearrays is not working!
                # The example JavaScript code sends audio data as 16 bit int arrays
                
                test_data = bytearray(b"\x00\x00\x00\x00")
                #await self.ws.send([int.from_bytes(test_data, sys.byteorder)])
                #await self.ws.send(audio_frame)
                await self.ws.send(test_data)
                #resp = await self.ws.recv()
                #return resp
                if self.is_sending is True:
                    self.frames_sent+=1
                    if self.frames_sent % 10000 == 0:
                        print("frames sent: ", self.frames_sent)
                    
                    if self.frames_sent == 330000:
                        print("sending control|stop to the websocket server")
                        await self.ws.send("control|stop")
                        self.is_sending = False
                
                #return type(audio_frame)
                #test = await self.ws.send("control|ping")
                
        # Process messages received on the connection.
        #async for message in self.ws:
            #if message.startswith("result|1;"):
                #return message
            
    async def ws_stream_close(self):
        print("Closing the websocket.")
        await self.ws.send("control|stop")
        await self.ws.send("control|disconnect")
        await self.ws.close()
        print("websocket closed")
            
    # params: 
    #   websocket:      WebSocket object
    #   wav_filename:   string
    #   wav_length:     int (length of the data part only)
    #   wav_nframes:    int (number of audio frames)
    async def ws_wav_upload(self, websocket, wav_filename, wav_length, wav_nframes): 
        with open(wav_filename, "rb") as wav_file_bin:
            # Warning: Some parameters below are hardcoded!
            await websocket.send("control|start;16000;-1;1," + str(wav_length))
           
            wav_bin_header = bytearray()
            wav_bin_data = bytearray()
            frame = bytearray()
            
            # The first 44 bytes (the wav header) is not needed!
            # So we skip through these by reading it in one go 
            wav_bin_header = wav_file_bin.read(44)
        
            # While there are frames left, we send them to the ws server
            nframe = 0
            while nframe < wav_nframes:
                frame = wav_file_bin.read(2) # 16 bit -> 1 frame = 2 Bytes
                await websocket.send(frame)
                nframe += 1
                
            # This function still needs error handling!

    async def ws_wav_recognition(self, wav_filename):
        async with websockets.connect(self.uri) as ws:        
            try:
                # Bind model
                await ws.send("control|bind-request;general_hu")
                
                # Getting information of the wav file
                wav_file = wave.open(wav_filename, "rb")
                print(wav_file.getparams()) # FORDEBUG
                wav_nframes = wav_file.getnframes()
                wav_length = wav_nframes*wav_file.getsampwidth()
                wav_file.close()
                
                # Uploading the wav file through websocket
                await self.ws_wav_upload(ws, wav_filename, wav_length, wav_nframes)
                
            except websockets.ConnectionClosed:
                return
                
            # Process messages received on the connection.
            async for message in ws:
                #print(message)
                if message.startswith("result|1;"):
                    return message
 
def outoftime_handler(signum, frame):
    raise Exception("Out of time exception!")
               
if __name__ == "__main__":
    if(len(sys.argv) > 2):
        print(f"Recognizing speech in: {sys.argv[1]}")
        stt_uri = sys.argv[1]
        wav_filename = sys.argv[2]
        
        stt_api = SpeechToTextAPI(sys.argv[1])
        
        # Time-out after 10 seconds
        signal.signal(signal.SIGALRM, outoftime_handler)
        signal.alarm(10)
        try:
            if asyncio.run(stt_api.ws_check_connection()):        
                res = asyncio.run(stt_api.ws_wav_recognition(wav_filename))
                print("Result: ", res.split(";")[1])
            else:
                print("Unable to establish connection to the ASR server!")
        except Exception as e:
            print("ERROR")
        
