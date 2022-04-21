import asyncio
import websockets
import signal
import wave
import sys
import signal

class SpeechToTextAPI():
    uri = ""
    
    def __init__(self, stt_uri):
        self.uri = stt_uri
    
    async def ws_check_connection(self):
        async for ws in websockets.connect(self.uri):
            try:
                pong_waiter = await ws.ping()
                await pong_waiter
                return True
            except:
                return False
            
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
        
