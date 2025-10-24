import tkinter as tk
from PIL import Image, ImageTk
import base64
import numpy as np
import cv2
import websocket
import threading
import ctypes
from matplotlib.figure import Figure
from matplotlib.backends.backend_tkagg import FigureCanvasTkAgg, NavigationToolbar2Tk
import math
import time

import imgProcess

class ImageReceiverApp:
    def __init__(self, master):
        self.master = master
        self.master.title("CanSat Camera Viewer")
        self.master.geometry("1400x1000")
        self.master.resizable(False,False)
        self.label = tk.Label(master)
        self.label.grid(column=0,row=0)
        img = Image.open('test.jpg')
        img = ImageTk.PhotoImage(img)
        self.latest_frame = None

        self.imgCanvas = tk.Canvas(self.label,width=800,height=600)#,bg="#70FF03"
        self.item = self.imgCanvas.create_image(0, 0, image=img, anchor=tk.NW)
        self.imgCanvas.pack()

        self.sidepanelLable = tk.Label(master)#,bg="#F900E9"
        self.sidepanelLable.grid(column=1,row=0)
        self.settingLabel = tk.Label(self.sidepanelLable)#,bg="#F80808"
        self.settingLabel.pack(side=tk.TOP)
        self.processimgLable = tk.Label(self.sidepanelLable)#,bg="#FFF200"
        self.processimgLable.pack(side=tk.BOTTOM)

        self.processCanvas = tk.Canvas(self.processimgLable,width=500,height=400)
        self.processCanvas.pack()
        img = Image.open('test.jpg')
        img = ImageTk.PhotoImage(img)
        self.processimg = self.processCanvas.create_image(0, 0, image=img, anchor=tk.NW)

        self.ipaddr = tk.StringVar()
        self.ipaddrEntry = tk.Entry(self.settingLabel,textvariable=self.ipaddr)
        self.ipaddrEntry.grid(column=0,row=0)

        self.conndisconnLabel = tk.Label(self.settingLabel)#,bg="#FF00C8"
        self.conndisconnLabel.grid(column=0,row=1)
        self.connectButton = tk.Button(self.conndisconnLabel,text="接続",command=self.start_connect)
        self.connectButton.pack(side=tk.RIGHT)
        self.disconnectButton = tk.Button(self.conndisconnLabel,text="切断",command=self.close)
        self.disconnectButton.pack(side=tk.LEFT)
        self.disconnectButton["state"] = tk.DISABLED

        self.checkAutoMode = tk.BooleanVar()
        self.auto = tk.Radiobutton(self.settingLabel,text="自律走行",variable=self.checkAutoMode,value=True)
        self.manual = tk.Radiobutton(self.settingLabel,text="遠隔制御",variable=self.checkAutoMode,value=False)
        self.auto.grid(column=0,row=2)
        self.manual.grid(column=0,row=3)
        self.stopButton = tk.Button(self.settingLabel,text="停止",command=lambda:self.send_command("stop"))
        self.stopButton.grid(column=0,row=4)

        pixel = tk.PhotoImage(width=1, height=1)
        self.driverLabel = tk.Label(master)#,bg="#1605FF"
        self.driverLabel.grid(column=0,row=1)
        self.forward = tk.Button(self.driverLabel,text="FORWARD",height=5,width=80,command=lambda:self.send_command("forward"))
        self.forward.pack(side=tk.TOP)
        self.right = tk.Button(self.driverLabel,text="RIGHT",height=5,width=28,command=lambda:self.send_command("right"))
        self.right.pack(side=tk.RIGHT)
        self.left = tk.Button(self.driverLabel,text="LEFT",height=5,width=28,command=lambda:self.send_command("left"))
        self.left.pack(side=tk.LEFT)
        self.back = tk.Button(self.driverLabel,text="BACK",height=5,width=20,command=lambda:self.send_command("back"))
        self.back.pack(side=tk.BOTTOM)

        self.figFrame = tk.Frame(self.master)
        # matplotlibの描画領域の作成
        fig = Figure(figsize=(4,2))
        self.ax = fig.add_subplot(1, 1, 1)
        # matplotlibの行場領域とウィジェットの関連付け
        self.fig_canvas = FigureCanvasTkAgg(fig, self.figFrame)
        # matplotlibのツールバーを作成
        #self.toolbar = NavigationToolbar2Tk(self.fig_canvas, frame)
        # matploglibのグラフをフレームに配置
        self.fig_canvas.get_tk_widget().pack(fill=tk.BOTH, expand=True)
        self.figFrame.grid(column=1,row=1)
        self.x = [];self.y = []
        self.current_image = None  # 画像保持用

        threading.Thread(target=self.auto_drive_loop,daemon=True).start()

    def start_connect(self):
        print("接続開始")
        self.connectButton["state"] = tk.DISABLED
        self.disconnectButton["state"] = tk.NORMAL
        ipaddr = self.ipaddrEntry.get()
        # WebSocket接続開始
        self.ws = websocket.WebSocketApp(#画像
            f"ws://{ipaddr}:8765",  # ← IPアドレスを適宜変更
            on_message=self.on_message,
            on_error=self.on_error,
            on_close=self.on_close,
            on_open=self.on_open
        )
        self.wsSecond = websocket.WebSocketApp(#加速度データ
            f"ws://{ipaddr}:9000",  # ← IPアドレスを適宜変更
            on_message=self.printmessage,
            on_error=self.on_error,
        )
        self.wsThird = websocket.WebSocketApp(#コマンド
            f"ws://{ipaddr}:9001",
            on_error=self.on_error,
        )
        # WebSocketを別スレッドで実行
        threading.Thread(target=self.ws.run_forever, daemon=True).start()
        threading.Thread(target=self.wsSecond.run_forever, daemon=True).start()
        threading.Thread(target=self.wsThird.run_forever, daemon=True).start()

    def printmessage(self,ws,message):
        mg = [float(v) for v in message.split(",")]
        self.master.after(0,self.update_graph,mg)
        # print(f"x:{math.degrees(self.mg[0])}")
        # print(f"y:{math.degrees(self.mg[1])}")
        # print(f"z:{math.degrees(self.mg[2])}")

    def update_graph(self,mg):
        self.x.append(math.degrees(mg[2]));self.y.append(mg[3])
        self.ax.plot(self.y,self.x,color="#242424")
        self.fig_canvas.draw()
        #self.figFrame.update()


    def on_open(self, ws):
        print("接続成功")

    def on_message(self, ws, message):
        try:
            # Base64 → JPEG → OpenCV → PIL → tkinter
            img_data = base64.b64decode(message)
            np_arr = np.frombuffer(img_data, np.uint8)
            frame = cv2.imdecode(np_arr, cv2.IMREAD_COLOR)
            frame = cv2.cvtColor(frame, cv2.COLOR_BGR2RGB)
            frame = np.flipud(frame)
            frame = np.fliplr(frame)
            frame = cv2.resize(frame,dsize = (800,600))
            img = Image.fromarray(frame)
            imgtk = ImageTk.PhotoImage(image=img)
            self.latest_frame = frame.copy()
            # GUIスレッドで画像更新
            self.master.after(0, self.update_image, imgtk)
        except Exception as e:
            print(f"画像処理エラー: {e}")

    def update_image(self, imgtk):
        self.current_image = imgtk  # 保持してGCを防ぐ
        self.imgCanvas.itemconfig(self.item,image=self.current_image)

    # def auto_drive_loop(self):
    #     flag = False #autoからmanualに切り替わった際，1度のみstopコマンドを送信
    #     processingflag = False
    #     while True:
    #         if self.checkAutoMode.get() and self.latest_frame is not None:
    #             self.forward["state"] = tk.DISABLED
    #             self.right["state"] = tk.DISABLED
    #             self.left["state"] = tk.DISABLED
    #             self.back["state"] = tk.DISABLED
    #             cmd,img = imgProcess.imgprocess(self.latest_frame)
    #             self.wsThird.send(cmd)
    #             flag = True
    #             img = Image.fromarray(img)
    #             img = ImageTk.PhotoImage(image=img)
    #             self.processimgLable.after(0,self.update_peocessimg,img)
    #         else:
    #             if flag:
    #                 self.wsThird.send("stop");flag = False
    #             self.forward["state"] = tk.NORMAL
    #             self.right["state"] = tk.NORMAL
    #             self.left["state"] = tk.NORMAL
    #             self.back["state"] = tk.NORMAL

    #         time.sleep(0.5)

    def auto_drive_loop(self):
        flag = False
        processing = False  # 現在処理中かを示すフラグ

        while True:
            if self.checkAutoMode.get() and self.latest_frame is not None:
                if not processing:  # 前回の処理が終わっているときだけ開始
                    processing = True
                    frame_copy = self.latest_frame.copy()

                    def process_and_update():
                        nonlocal processing, flag
                        cmd, img = imgProcess.imgprocess(frame_copy)
                        self.wsThird.send(cmd)
                        flag = True
                        cv2.resize(img,dsize = (400,300))
                        img = cv2.cvtColor(img, cv2.COLOR_BGR2RGB)
                        pil_img = Image.fromarray(img)
                        imgtk = ImageTk.PhotoImage(image=pil_img)
                        self.master.after(0, self.update_peocessimg, imgtk)
                        processing = False  # 処理完了

                    threading.Thread(target=process_and_update, daemon=True).start()

                # 操作ボタン無効化
                self.forward["state"] = self.right["state"] = self.left["state"] = self.back["state"] = tk.DISABLED

            else:
                if flag:
                    self.wsThird.send("stop")
                    flag = False
                self.forward["state"] = self.right["state"] = self.left["state"] = self.back["state"] = tk.NORMAL

            time.sleep(0.05)  # 少し短くしてもOK（メインループは軽い）


    def update_peocessimg(self,imgtk):
        self.current_image_process = imgtk
        self.processCanvas.itemconfig(self.processimg,image=self.current_image_process)


    def on_error(self, ws, error):
        print(f"WebSocketエラー: {error}")

    def on_close(self, ws, close_status_code, close_msg):
        print("接続終了")

    def close(self):
        self.ws.close()
        self.wsSecond.close()
        self.wsThird.close()

    def send_command(self,dir):
        self.wsThird.send(dir)

# tkinter GUI起動
ctypes.windll.shcore.SetProcessDpiAwareness(1)
root = tk.Tk()
app = ImageReceiverApp(root)
root.mainloop()