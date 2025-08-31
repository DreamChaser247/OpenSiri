import asyncio
import time 
import openwakeword
import numpy as np
import sounddevice as sd
import whisper
import webrtcvad

from threading import Thread, Event
from queue import Queue
from openwakeword.model import Model

# Load the Whisper model
# model = whisper.load_model("turbo")

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

vad = webrtcvad.Vad(3)  # Aggressiveness mode (0-3)
vadFrameDuration = 20  # ms
vadFrameSamples = int(sample_rate * vadFrameDuration / 1000)  # 320 samples

def voiceDetect(frame):
    results = []
    for i in range(0, len(frame), vadFrameSamples):
        chunkToAnalyze = frame[i:i+vadFrameSamples]
        audioBytes = (chunkToAnalyze.tobytes())
        if vad.is_speech(audioBytes, sample_rate):
            results.append(1)
        else:
            results.append(0)
    print(results)
    return results

def openWakeWord(frame):
    prediction = model.predict(frame, debounce_time=1, threshold={"alexa_v0.1": 0.4})
    # prediction = model.predict(frame)
    if prediction['alexa_v0.1']>0.5:
        print("Alexa!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!")
    else:
        print(prediction)

def audioStream(exitCondition, isListening):
    def callback(inData, frameCount, timeInfo, status):
        if status:
            print(f"Error: {status}")
        audioChunk = (inData[:, 0] * 32767).astype(np.int16)
        chunkQueue.put(audioChunk)

    stream = sd.InputStream(samplerate=sample_rate, channels=1, dtype='float32', blocksize=chunk_size, callback=callback)

    stream.start()
    print("Audio stream started.")
    while not exitCondition.is_set():
        sd.sleep(100)  # Keep thread alive

    stream.stop()
    stream.close()
    print("Audio stream stopped.")

async def audioProcess(isListening):
    while True:
        if not chunkQueue.empty():
            frame = chunkQueue.get()
            openWakeWord(frame, isListening)
            voiceDetect(frame)
        
        await asyncio.sleep(0.01)  # Slight delay to prevent busy waiting

async def main(exitCondition, isListening, audioStreamThread):
    
    audioStreamThread.start()
    await audioProcess(isListening)

async def getAudioCommand():
    print("Listening for command...")
    frames = []
    start_time = time.time()



if __name__ == "__main__":
    exitCondition = Event()
    isListening = Event()
    audioStreamThread = Thread(target=audioStream, args=(exitCondition, isListening) , daemon=True)
    try:
        asyncio.run(main(exitCondition, isListening, audioStreamThread))

    except KeyboardInterrupt:
        print("Exiting...")
        exitCondition.set()
        audioStreamThread.join()