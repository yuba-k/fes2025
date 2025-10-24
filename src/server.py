# server.py（Raspberry Pi側）
import asyncio
import websockets
import cv2
import base64
import RPi.GPIO as GPIO
from picamera2 import Picamera2
import time
import threading

from adafruit_lsm6ds.lsm6ds33 import LSM6DS33
import board
import math

import motor

command = ""

picam = Picamera2()
picam.configure(picam.create_still_configuration(main={"format":"RGB888","size":(400,300)}))

mv = motor.Motor()
gyro = {"x":0.0,"y":0.0,"z":0.0}

async def handler(websocket):
    picam.start()
    cap = picam.capture_array()
    try:
        while True:
            # 映像送信
            frame = picam.capture_array()
            _, buffer = cv2.imencode('.jpg', frame)
            img_str = base64.b64encode(buffer).decode('utf-8')
            await websocket.send(img_str)

            # コマンド受信
#            try:
#                command = await asyncio.wait_for(websocket.recv(), timeout=0.1)
#                if command == "forward":
#                    GPIO.output(18, GPIO.HIGH)
#                elif command == "stop":
#                    GPIO.output(18, GPIO.LOW)
#                print(command)
#            except asyncio.TimeoutError:
#                pass
    finally:
        GPIO.cleanup()
        picam.close()

async def recvcommand(websocket):
    global command
    while True:
        try:
            command = await asyncio.wait_for(websocket.recv(),timeout=0.1)
            mv.direction = command
            print(command)
        except asyncio.TimeoutError:
            pass

async def handler6asix(websocket):
    tn = time.perf_counter()
    try:
        while True:
            msg = f"{gyro['x']},{gyro['y']},{gyro['z']},{time.perf_counter()-tn:.2f}"
            print(msg)
            await websocket.send(msg) 
            await asyncio.sleep(1)
    finally:
        print("全終了")

def start_video_server():
    async def video_server():
        async with websockets.serve(handler,"0.0.0.0",8765):
            print("映像サーバ起動(8765)")
            await asyncio.Future()
    asyncio.run(video_server())

def start_other_servers():
    async def main():
        await asyncio.gather(
                websockets.serve(handler6asix, "0.0.0.0", 9000),
                websockets.serve(recvcommand,"0.0.0.0",9001),
        )
    # 永久待機
        await asyncio.Future()
    asyncio.run(main())

def start_motor():
    mv.move()

def gyro_angle():
    global gyro
#    while True:
#        print("動いてます")
##        gyro["x"] = 10
#        gyro["y"] = 5
#        gyro["z"] = 1
#        time.sleep(1)
#    global angle
    i2c = board.I2C()
    sensor = LSM6DS33(i2c)
    dt = 0.05
    while True:
        gyro["x"] = 0;gyro["y"] = 0;gyro["z"] = 0
        while command == "right" or command == "left":
            gyro_x, gyro_y, gyro_z = sensor.gyro
            gyro["x"] += gyro_x * dt
            gyro["y"] += gyro_y * dt
            gyro["z"] += gyro_z * dt
            time.sleep(dt)

try:
    threading.Thread(target=start_video_server,daemon=True).start()
    threading.Thread(target=start_other_servers,daemon=True).start()
    threading.Thread(target=start_motor).start()
    threading.Thread(target=gyro_angle).start()
    print("全サーバ起動")
    while True:
        time.sleep(1)
finally:
    mv.cleanup()
    picam.close()
