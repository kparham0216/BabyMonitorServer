
import smbus2
import time

bus = smbus2.SMBus(1)
ADDR = 0x42

while True:
    
    # send register index 0, then read 10 bytes
    try:
        data = bus.read_i2c_block_data(ADDR, 0, 11)
        # for i, val in enumerate(data):
            # print(f"reg[{i}] = {val:#04x}")

        bpm  = (data[0] << 16) | (data[1] << 8) | data[2]
        ir   = (data[3] << 16) | (data[4] << 8) | data[5]
        temp = (data[8] << 8) | data[9]
        spo2 = data[10]
        temp_f = ((temp * 9) * 0.00078125) + 32

        if bpm == 0 and spo2 == 0 and temp == 0:
            print("Whooops")
            continue
        print(f"BPM = {bpm}\nSpO2 = {spo2}\nTemp = {temp_f}\n")
        
        time.sleep(11)

    except:
        print("Whooops")
        time.sleep(11)
        continue
            
