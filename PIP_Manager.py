from tkinter import *
import os
import subprocess
import sys
import win32gui, win32con

the_program_to_hide = win32gui.GetForegroundWindow()
win32gui.ShowWindow(the_program_to_hide , win32con.SW_HIDE)

root = Tk()
root.title("PIP Manager App V.2")
root.geometry("350x250")
root.iconbitmap("pip.ico")

global lb1
lb1 = Label(root, text="PIP Manager App", font="50")
lb1.pack(pady=15)

lb2 = Label(root, text="Type in Module Name:").pack()

global user
user = Entry(root)
user.pack(pady=10)


def install():
    try:
        f = user.get()
        subprocess.check_call([sys.executable, "-m", "pip", "install", f])
        lb23.config(text=f"{f} Installed", fg="blue")

    except Exception as e:
        print(e)
        lb23.config(text=f"No Module Named '{f}'", fg="red")

def uninstall():
    try:
        f = user.get()
        subprocess.check_call([sys.executable, "-m", "pip", "uninstall", f, "-y"])
        lb23.config(text=f"{f} Uninstalled", fg="blue")

    except Exception as e:
        print(e)
        lb23.config(text=f"No Module Named '{f}' Found In Your Python", fg="red")

def upgrade():
    try:
        f = user.get()
        subprocess.check_call([sys.executable, "-m", "pip", "install", f, "--upgrade"])
        lb23.config(text=f"{f} Updated", fg="blue")

    except Exception as e:
        print(e)
        lb23.config(text=f"No Module Named '{f}'", fg="red")

def upgrade_pip():
    try:
        f = user.get()
        subprocess.check_call([sys.executable, "-m", "pip", "--upgrade", "pip"])
        lb23.config(text=f"PIP Updated", fg="blue")

    except Exception as e:
        print(e)
        lb23.config(text=e, fg="red")
    

controls_frame = Frame()
controls_frame.pack()

install_btn = Button(controls_frame, text="Install", command=install).grid(row=0, column=0, padx=10)
uninstall_btn = Button(controls_frame, text="Uninstall", command=uninstall).grid(row=0, column=1, padx=10)
upgrade_btn = Button(controls_frame, text="Upgrade", command=upgrade).grid(row=0, column=2, padx=10)
upgrade_pip_btn = Button(controls_frame, text="Upgrade PIP", command=upgrade_pip).grid(row=1, column=1, pady=10)

global lb23
lb23 = Label(root, text="Waiting For input")
lb23.pack()


root.mainloop()
