from tkinter import *
import tkinter
import os
import subprocess
import sys
import win32gui, win32con
import importlib
import pkg_resources
from tkinter import Checkbutton

dir_path = os.path.dirname(os.path.realpath(__file__))
print(f"python {dir_path}/PIP_Manager.py")

try:
    print("PIP_Manager_Startup.bat built")
    f = open("PIP_Manager_Startup.bat", "x")
    f.write(f"python {dir_path}/PIP_Manager.py")
    f.close()
except Exception as e:
    print(e)

try:
    print("logs.txt built")
    f = open("logs.txt", "x")
    f.write(" [start]: Making Logs")
    f.close()
except Exception as e:
    print(e)


'''
the_program_to_hide = win32gui.GetForegroundWindow()
win32gui.ShowWindow(the_program_to_hide , win32con.SW_HIDE)
'''
the_program_to_hide = win32gui.GetForegroundWindow()


root = Tk()
root.title("PIP Manager App V.2")
root.geometry("360x250")
#root.iconbitmap("pip.ico")


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
        log = open("logs.txt", "a")
        log.write(f"\n [Installed]: {f}")
        log.close()

    except Exception as e:
        print(e)
        lb23.config(text=f"No Module Named '{f}'", fg="red")

def uninstall():
    try:
        f = user.get()
        subprocess.check_call([sys.executable, "-m", "pip", "uninstall", f, "-y"])
        lb23.config(text=f"{f} Uninstalled", fg="blue")
        log = open("logs.txt", "a")
        log.write(f" \n [uninstalled]: {f}")
        log.close()

    except Exception as e:
        print(e)
        lb23.config(text=f"No Module Named '{f}' Found In Your Python", fg="red")

def upgrade():
    try:
        f = user.get()
        subprocess.check_call([sys.executable, "-m", "pip", "install", f, "--upgrade"])
        lb23.config(text=f"{f} Updated", fg="blue")
        log = open("logs.txt", "a")
        log.write(f"\n [Upgraded]: {f}")
        log.close()

    except Exception as e:
        print(e)
        lb23.config(text=f"No Module Named '{f}'", fg="red")

def upgrade_pip():
    try:
        f = user.get()
        subprocess.check_call([sys.executable, "-m", "pip", "--upgrade", "pip"])
        lb23.config(text=f"PIP Updated", fg="blue")
        log = open("logs.txt", "a")
        log.write("\n [PIP UPGRADED]")
        log.close()

    except Exception as e:
        print(e)
        lb23.config(text=e, fg="red")

def test_import():
    try:
        f = user.get()
        i = importlib.import_module(f)
        lb23.config(text=f"You do have {f}", fg="blue")
    except Exception as e:
        f = user.get()
        print(e)
        lb23.config(text=f"{f} is not installed on the system", fg="red")

      
var = IntVar()
def hide_console():
    win32gui.ShowWindow(the_program_to_hide , win32con.SW_HIDE)

    if var.get() == 0:
        win32gui.ShowWindow(the_program_to_hide , win32con.SW_SHOW)

def stop_all(event):
    root.destroy()

def wipe_logs(event):
    f = open("logs.txt", "w")
    f.write(" [Wiped]: Logs have been wiped")
    f.close()

   
controls_frame = Frame()
controls_frame.pack()

install_btn = Button(controls_frame, text="Install", command=install).grid(row=0, column=0, padx=10)
uninstall_btn = Button(controls_frame, text="Uninstall", command=uninstall).grid(row=0, column=1, padx=10)
upgrade_btn = Button(controls_frame, text="Upgrade", command=upgrade).grid(row=0, column=2, padx=10)
import_btn = Button(controls_frame, text="Import", command=test_import).grid(row=0, column=3, padx=10)
upgrade_pip_btn = Button(root, text="Upgrade PIP", command=upgrade_pip).pack(pady=10)


global lb23
lb23 = Label(root, text="Waiting For input")
lb23.pack()

global cbox
cbox = Checkbutton(root, text="Hide Console",variable=var, command = hide_console).pack(side=LEFT)

root.bind("<Control-Key-q>", stop_all)
root.bind("<Control-Key-W>", wipe_logs)

root.mainloop()
