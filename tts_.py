import sys
import requests # https://docs.python-requests.org/en/latest/user/quickstart/

# https://chatbot-rgai3.inf.u-szeged.hu/flask"
tmit_tts_uri = "http://szeged:s23936@cyrus.tmit.bme.hu/hmmtts2/synth_hmm_wav.php"
#tmit_tts_uri = "https://chatbot-rgai3.inf.u-szeged.hu/flask/tts"
payload = {"speaker" : "MK"} # NG male voice, MK female voice

if __name__ == "__main__":
    if(len(sys.argv) > 1):
        print(f"Synthesizing text: {sys.argv[1]}")
        payload["q"] = sys.argv[1]
        
        if (len(sys.argv) > 2):
            wav_f_name = sys.argv[2] + ".wav"
        else:
            wav_f_name = "003.wav"
        
        # Sending the get request
        print(payload)
        r = requests.get(tmit_tts_uri, params=payload)
        #r = requests.get(tmit_tts_uri)
        
        # Was that successful?
        print(f"Response STATUS CODE: {r.status_code}")
        
        if (r.status_code == requests.codes.ok):
        
            # Getting rid of non alphanumeric chars - in order to create manageable file names
            import re, string
            re_pattern = re.compile("[\W_]+", re.UNICODE)
            wav_f_name = re_pattern.sub("", sys.argv[1]) + ".wav"
           
            # Writing the response to file
            with open(wav_f_name, "wb") as wav_f:
                wav_f.write(r.content)
        
            # THIS PART CAN BE OMITTED!
            # Source: https://stackoverflow.com/questions/17657103/how-to-play-wav-file-in-python      
            # Play the file just to test it immediately
            #import playsound
            #playsound.playsound(wav_f_name)
            

print("End of speech.")
