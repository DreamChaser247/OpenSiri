import asyncio
import time 
import openwakeword
import numpy as np
import sounddevice as sd
import whisper
import webrtcvad

from pydub import AudioSegment
from threading import Thread, Event
from queue import Queue
from openwakeword.model import Model

# Load the Whisper model
# model = whisper.load_model("tiny.en")

print(sd.query_devices()) # List available audio devices

chunkQueue = Queue() # Create a queue to hold audio chunks

# openwakeword.utils.download_models()  # download the pre-trained models if they are not already present

# Instantiate the model(s)
model = Model(
    wakeword_models=["env310/lib/python3.10/site-packages/openwakeword/resources/models/alexa_v0.1.tflite"],  # can also leave this argument empty to load all of the included pre-trained models
)


sample_rate = 16000
chunk_duration = 0.08  # 80ms chunks
chunk_size = int(sample_rate * chunk_duration)  # 1280 samples

vad = webrtcvad.Vad()  # Aggressiveness mode (0-3)
vad.set_mode(3)
vadFrameDuration = 20  # ms
vadFrameSamples = int(sample_rate * vadFrameDuration / 1000)  # 320 samples

class AudioProcessor:
    def __init__(self, threshold=0.5):
        self.threshold = threshold
        self.endingSilenceDuration = 1.0  # seconds
        self.startingSilenceDuration = 2  # seconds
        self.listeningToSilence = False
        self.silenceStart = time.time()
        self.listeningStart = time.time()
        self.isListening = False
        self.maximumListeningTime = 6.0 # seconds
        self.commandAudioChunks = []


    def voiceDetect(self, frame):
        results = []
        for i in range(0, len(frame), vadFrameSamples):
            chunkToAnalyze = frame[i:i+vadFrameSamples]
            audioBytes = (chunkToAnalyze.tobytes())
            if vad.is_speech(audioBytes, sample_rate):
                results.append(1)
            else:
                results.append(0)
        print(results)
        if results.count(1) == 0:
            if not self.listeningToSilence:
                self.silenceStart = time.time()
                self.listeningToSilence = True
        else:
            self.listeningToSilence = False
        timeNow = time.time()
        if (timeNow - self.silenceStart > self.endingSilenceDuration and self.listeningToSilence) or timeNow - self.listeningStart > self.maximumListeningTime:
            print("ending listening") 
            self.isListening = False
            self.listeningToSilence = False
            self.extractAudioFile()
            
        return results

    def openWakeWord(self, frame):
        prediction = model.predict(frame, debounce_time=1, threshold={"alexa_v0.1": 0.4})
        # prediction = model.predict(frame)
        if prediction['alexa_v0.1'] > self.threshold:
            print("Alexa!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!")
            self.listeningStart = time.time()
            self.isListening = True
            self.commandAudioChunks.clear()
        else:
            print(prediction)

    def extractAudioFile(self):
        audioData = np.concatenate(self.commandAudioChunks)
        audioPreExport = AudioSegment(
            data=audioData.tobytes(),
            sample_width=2,  # 16-bit audio
            frame_rate=sample_rate,
            channels=1
        )

        audioPreExport.export(".command.mp3", format="mp3", bitrate="128k")

    async def audioProcess(self):
        while True:
            if not chunkQueue.empty():
                frame = chunkQueue.get()
                self.openWakeWord(frame)
                if self.isListening:
                    self.voiceDetect(frame)
                    self.commandAudioChunks.append(frame)
            
            await asyncio.sleep(0.01)  # Slight delay to prevent busy waiting

def audioStream(exitCondition):
    def callback(inData, frameCount, timeInfo, status):
        if status:
            print(f"Error: {status}")
        audioChunk = (inData[:, 0] * 32767).astype(np.int16)
        chunkQueue.put(audioChunk)

    stream = sd.InputStream(samplerate=sample_rate, channels=1, dtype='float32', blocksize=chunk_size, callback=callback)

    stream.start()
    print("Audio stream started.")
    exitCondition.wait()  # Wait until the exit condition is set
    stream.stop()
    stream.close()
    print("Audio stream stopped.")


async def main(audioGate, audioStreamThread):
    
    audioStreamThread.start()
    await audioGate.audioProcess()

async def getAudioCommand():
    print("Listening for command...")
    frames = []
    start_time = time.time()



if __name__ == "__main__":
    exitCondition = Event()
    # isListening = Event()
    audioStreamThread = Thread(target=audioStream, args=(exitCondition,) , daemon=True)
    audioGate = AudioProcessor()
    try:
        asyncio.run(main(audioGate, audioStreamThread))

    except KeyboardInterrupt:
        print("Exiting...")
        exitCondition.set()
        audioStreamThread.join()