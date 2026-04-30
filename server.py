from fastapi import FastAPI
from contextlib import asynccontextmanager
import smbus2
import time
import threading

bus = smbus2.SMBus(1)
ADDR = 0x42

MAX_SAMPLES = 360
SIX_HR_OFFSET = 6
TWELVE_HR_OFFSET = 12
TWENTY_FOUR_HR_OFFSET = 24

count = 0
roll_1hr = False
roll_6hr = False
roll_12hr = False
roll_24hr = False


samples_1hr_bpm = [] # update every count, start rolling @ 360 samples
samples_1hr_spo2 = []
samples_1hr_temp = []

samples_6hr_bpm = [] # update every 6 counts, start rolling @ 2160 samples
samples_6hr_spo2 = []
samples_6hr_temp = []

samples_12hr_bpm = [] # update every 12 counts, start rolling @ 4320 samples
samples_12hr_spo2 = []
samples_12hr_temp = []

samples_24hr_bpm = [] # update every 24 counts, start rolling @ 8640 samples
samples_24hr_spo2 = []
samples_24hr_temp = []

# count will go up to (highest_sample_rate * MAX_SAMPLES) = 24 * 360 = 8640


@asynccontextmanager
async def lifespan(app: FastAPI):
    # Startup: begin collecting data
    t = threading.Thread(target=collect_data, daemon=True)
    t.start()
    yield
    # Shutdown: anything you want to clean up goes here
    
app = FastAPI(lifespan=lifespan)

latest_data = {"bpm": None, "spo2": None, "temp": None, "timestamp": None}
lock = threading.Lock()
first = True

def avg(lis):
    return sum(lis) / len(lis)

def collect_data():
    global first
    global count
    global roll_1hr
    global roll_6hr 
    global roll_12hr
    global roll_24hr
    global samples_1hr_bpm
    global samples_1hr_spo2
    global samples_1hr_temp
    global samples_6hr_bpm
    global samples_6hr_spo2
    global samples_6hr_temp
    global samples_12hr_bpm
    global samples_12hr_spo2
    global samples_12hr_temp
    global samples_24hr_bpm
    global samples_24hr_spo2
    global samples_24hr_temp
    
    while True:
        # send register index 0, then read 10 bytes
        try:
            data = bus.read_i2c_block_data(ADDR, 0, 11)
            # for i, val in enumerate(data):
                # print(f"reg[{i}] = {val:#04x}")
            if first:
                first = False
                continue
            bpm  = (data[0] << 16) | (data[1] << 8) | data[2]
            ir   = (data[3] << 16) | (data[4] << 8) | data[5]
            temp = (data[8] << 8) | data[9]
            spo2 = data[10]
            temp_f = ((temp * 9) * 0.00078125) + 32
            
            print(f"BPM: {bpm} | SpO2: {spo2}% | Temp: {temp_f:.1f}°F")

            if count >= MAX_SAMPLES:
                roll_1hr = True
            if count >= MAX_SAMPLES * SIX_HR_OFFSET:
                roll_6hr = True
            if count >= MAX_SAMPLES * TWELVE_HR_OFFSET:
                roll_12hr = True
            if count >= MAX_SAMPLES * TWENTY_FOUR_HR_OFFSET:
                roll_24hr = True

            with lock:
                latest_data['bpm'] = bpm
                latest_data['spo2'] = spo2
                latest_data['temp'] = temp_f
                if roll_1hr:
                    samples_1hr_bpm.pop(0)
                    samples_1hr_spo2.pop(0)
                    samples_1hr_temp.pop(0)
                samples_1hr_bpm.append(bpm)
                samples_1hr_spo2.append(spo2)
                samples_1hr_temp.append(temp_f)
                
                if count % SIX_HR_OFFSET == 0:
                    if roll_6hr:
                        samples_6hr_bpm.pop(0)
                        samples_6hr_spo2.pop(0)
                        samples_6hr_temp.pop(0)
                    samples_6hr_bpm.append(avg(samples_1hr_bpm[-SIX_HR_OFFSET:]))
                    samples_6hr_spo2.append(avg(samples_1hr_spo2[-SIX_HR_OFFSET:]))
                    samples_6hr_temp.append(avg(samples_1hr_temp[-SIX_HR_OFFSET:]))
                
                if count % TWELVE_HR_OFFSET == 0:
                    if roll_12hr:
                        samples_12hr_bpm.pop(0)
                        samples_12hr_spo2.pop(0)
                        samples_12hr_temp.pop(0)
                    samples_12hr_bpm.append(avg(samples_1hr_bpm[-TWELVE_HR_OFFSET:]))
                    samples_12hr_spo2.append(avg(samples_1hr_spo2[-TWELVE_HR_OFFSET:]))
                    samples_12hr_temp.append(avg(samples_1hr_temp[-TWELVE_HR_OFFSET:]))
                    
                if count % TWENTY_FOUR_HR_OFFSET == 0:
                    if roll_24hr:
                        samples_24hr_bpm.pop(0)
                        samples_24hr_spo2.pop(0)
                        samples_24hr_temp.pop(0)
                    samples_24hr_bpm.append(avg(samples_1hr_bpm[-TWENTY_FOUR_HR_OFFSET:]))
                    samples_24hr_spo2.append(avg(samples_1hr_spo2[-TWENTY_FOUR_HR_OFFSET:]))
                    samples_24hr_temp.append(avg(samples_1hr_temp[-TWENTY_FOUR_HR_OFFSET:]))
            count += 1
            if count >= MAX_SAMPLES * TWENTY_FOUR_HR_OFFSET:
                count = 0
                
                    
               
            time.sleep(11)

        except Exception as e:
            print(f"Error: {e}")
            print("Whooops")
            time.sleep(11)
            continue
        

@app.get("/latest_data")
def get_latest():
    with lock:
        return dict(latest_data)
    

@app.get("/one_hr_data")
def get_one_hr():
    with lock:
        return {
            "bpm": list(samples_1hr_bpm),
            "spo2": list(samples_1hr_spo2),
            "temp": list(samples_1hr_temp)
        }

@app.get("/six_hr_data")
def get_six_hr():
    with lock:
        return {
            "bpm": list(samples_6hr_bpm),
            "spo2": list(samples_6hr_spo2),
            "temp": list(samples_6hr_temp)
        }

@app.get("/twelve_hr_data")
def get_twelve_hr():
    with lock:
        return {
            "bpm": list(samples_12hr_bpm),
            "spo2": list(samples_12hr_spo2),
            "temp": list(samples_12hr_temp)
        }

@app.get("/twenty_four_hr_data")
def get_twenty_four_hr():
    with lock:
        return {
            "bpm": list(samples_24hr_bpm),
            "spo2": list(samples_24hr_spo2),
            "temp": list(samples_24hr_temp)
        }
    


