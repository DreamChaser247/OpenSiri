import asyncio
import time 
import openwakeword
import numpy as np
import sounddevice as sd
from threading import Thread, Event
from queue import Queue
from openwakeword.model import Model

print(sd.query_devices())

chunkQueue = Queue()

# openwakeword.utils.download_models()  # download the pre-trained models if they are not already present

# Instantiate the model(s)
model = Model(
    wakeword_models=["env310/lib/python3.10/site-packages/openwakeword/resources/models/alexa_v0.1.tflite"],  # can also leave this argument empty to load all of the included pre-trained models
)


sample_rate = 16000
chunk_duration = 0.08  # 80ms chunks
chunk_size = int(sample_rate * chunk_duration)  # 1280 samples

def audioStream(exitCondition):
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
    
async def OpenWakeWord():
    while True:
        if not chunkQueue.empty():
            frame = chunkQueue.get()
            prediction = model.predict(frame, debounce_time=1, threshold={"alexa_v0.1": 0.4})
            # prediction = model.predict(frame)
            if prediction['alexa_v0.1']>0.5:
                print("Alexa!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!")
            else:
                print(prediction)
        
        await asyncio.sleep(0.01)  # Slight delay to prevent busy waiting

async def main(exitCondition, audioStreamThread):
    
    audioStreamThread.start()
    await OpenWakeWord()



if __name__ == "__main__":
    exitCondition = Event()
    audioStreamThread = Thread(target=audioStream, args=(exitCondition,) , daemon=True)
    try:
        asyncio.run(main(exitCondition, audioStreamThread))

    except KeyboardInterrupt:
        print("Exiting...")
        exitCondition.set()
        audioStreamThread.join()