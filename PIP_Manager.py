import subprocess
from tkinter import *
from tkinter.ttk import *
import os
import importlib
from ttkthemes import ThemedTk
from tkinter.scrolledtext import ScrolledText
import _thread
from subprocess import Popen, PIPE
import json
import win32gui, win32con



root = ThemedTk(theme='breeze')
tabControl = Notebook(root)
root.title("PIP Manager App V.3")
root.geometry("488x390")

def build_cogs():
    dinct = {
        "darkmode": "on",
        "cmd": "off"
    }

    cogs = json.dumps(dinct, indent=2)
    with open("cogs.json", 'w') as f:
        f.write(cogs)




tab1 = Frame(tabControl)
tab2 = Frame(tabControl)

tabControl.add(tab1, text ='Manager')
tabControl.add(tab2, text ='Settings')
tabControl.pack(expand = 1, fill ="both")


global lb1
lb1 = Label(tab1, text="PIP Manager App", font="50")
lb1.pack(pady=15)

lb2 = Label(tab1, text="Type in Module Name:").pack()

global user
user = Entry(tab1)
user.pack(pady=10)

# Core Codes
def command(command):
    if command == "install":
        try:
            _thread.start_new_thread(install, ())
        except:
            print("Failed to start thread!")
    elif command == "uninstall":
        try:
            _thread.start_new_thread(uninstall, ())
        except:
            print("Failed to start thread!")
    elif command == "upgrade":
        try:
            _thread.start_new_thread(upgrade, ())
        except:
            print("Failed to start thread!")
    elif command == "test_import":
        try:
            _thread.start_new_thread(test_import, ())
        except:
            print("Failed to start thread!")
    elif command == "upgradepip":
        try:
            _thread.start_new_thread(upgrade_pip, ())
        except:
            print("Failed to start thread!")
    else:
        raise ValueError("Not a valid command")

def install():
    try:
        f = user.get()
        os.system(f"pip install {f}")
        text.config(state=NORMAL)
        output = subprocess.getstatusoutput(f"echo [+] Sucessfully Installed: {f}")
        text.insert(INSERT, f"{output}\n")
        text.see("end")
        text.config(state=DISABLED)
        _thread.exit() #Exit running thread cuz it is done
    except Exception as e:
        print(e)

def uninstall():
    try:
        f = user.get()
        os.system(f"pip uninstall {f} -y")
        text.config(state=NORMAL)
        output = subprocess.getstatusoutput(f"echo [-] Sucessfully Uninstalled: {f}")
        text.insert(INSERT, f"{output}\n ")
        text.see("end")
        text.config(state=DISABLED)
        _thread.exit()  # Exit running thread cuz it is done
    except Exception as e:
        print(e)

def upgrade():
    try:
        f = user.get()
        os.system(f"pip install {f} --upgrade")
        _thread.exit()  # Exit running thread cuz it is done
    except Exception as e:
        print(e)

def upgrade_pip():
    try:
        f = user.get()
        os.system("python -m pip install --upgrade pip")
        _thread.exit()  # Exit running thread cuz it is done
    except Exception as e:
        print(e)

def test_import():
    try:
        f = user.get()
        i = importlib.import_module(f)
        text.config(state=NORMAL)
        output = subprocess.getstatusoutput(f"echo Module Found: {f}\n")
        text.insert(INSERT, f"{output} \n")
        text.see("end")
        text.config(state=DISABLED)
        _thread.exit()  # Exit running thread cuz it is done
    except Exception as e:
        f = user.get()
        text.config(state=NORMAL)
        output = subprocess.getstatusoutput(f"echo [-] Module Not Found: {f}\n")
        text.insert(INSERT, f"{output} \n")
        text.see("end")
        text.config(state=DISABLED)
        



def stop_all(event):
    root.destroy()


controls_frame = Frame(tab1)
controls_frame.pack()

install_btn = Button(controls_frame, text="Install", command= lambda: command("install")).grid(row=0, column=0, padx=10)
uninstall_btn = Button(controls_frame, text="Uninstall", command= lambda: command("uninstall")).grid(row=0, column=1, padx=10)
upgrade_btn = Button(controls_frame, text="Upgrade", command=lambda: command("upgrade")).grid(row=0, column=2, padx=10)
import_btn = Button(controls_frame, text="Import", command=lambda: command("test_import")).grid(row=0, column=3, padx=10)
upgrade_pip_btn = Button(tab1, text="Upgrade PIP", command=lambda: command("upgradepip")).pack(pady=10)


#settings 



def dark_mode():
    if var1.get() == 1:
        root.config(theme='equilux')
        with open('cogs.json', 'r') as f:
            data = json.load(f)
        data['darkmode'] = 'on'

        with open("cogs.json", "w") as jsonFile:
                json.dump(data, jsonFile)

    elif var1.get() == 0:
        root.config(theme='breeze')
        with open('cogs.json', 'r') as f:
            data = json.load(f)
            
        data['darkmode'] = 'off'

        with open("cogs.json", "w") as jsonFile:
                json.dump(data, jsonFile)


the_program_to_hide = win32gui.GetForegroundWindow()
win32gui.ShowWindow(the_program_to_hide , win32con.SW_HIDE)


def turn_cmd_off():
    if var2.get() == 1:
        win32gui.ShowWindow(the_program_to_hide , win32con.SW_HIDE)
        with open('cogs.json', 'r') as f:
            data = json.load(f)
            
        data['cmd'] = 'off'

        with open("cogs.json", "w") as jsonFile:
                json.dump(data, jsonFile)


    elif var2.get() == 0:
        win32gui.ShowWindow(the_program_to_hide , win32con.SW_SHOW)
        with open('cogs.json', 'r') as f:
            data = json.load(f)
            
        data['cmd'] = 'on'

        with open("cogs.json", "w") as jsonFile:
                json.dump(data, jsonFile)
        




frame = LabelFrame(
    root,
    text='Console: ',
    
)
frame.pack()

global text
text=Text(frame, width=69, height=8.5, background='black', foreground="green", state=DISABLED)
text.insert(END, "")
text.pack()

settings_frame = Frame(tab2)
settings_frame.pack()

var1 = IntVar()
var2 = IntVar()

def clear_console(event):
   text.config(state=NORMAL)
   text.delete(1.0, END)
   text.config(state=DISABLED)


global cogs
try:
    with open("cogs.json", 'r') as f:
        cogs = json.loads(f.read())

        if cogs["darkmode"] == "on":
            root.config(theme='equilux')
            var1.set(1)

        elif cogs["darkmode"] == "off":
            root.config(theme='breeze')
            var1.set(0)
        print("[]")
        if cogs["cmd"] == 'on':
            win32gui.ShowWindow(the_program_to_hide , win32con.SW_SHOW)
            var2.set(0)
        elif cogs['cmd'] == 'off':
            win32gui.ShowWindow(the_program_to_hide , win32con.SW_HIDE)
            var2.set(1)
            turn_cmd_off()
    print(cogs)
    
except Exception as e:
    build_cogs()

dark_mode1 = Checkbutton(settings_frame, text="Darkmode",variable=var1, onvalue=1, offvalue=0, command=dark_mode).grid(row=1, column=3)
cmd_off = Checkbutton(settings_frame, text="CMD Off", variable=var2, onvalue=1,offvalue=0, command=turn_cmd_off).grid(row=2, column=3)

root.bind("<Control-Key-q>", stop_all)
root.bind("<Control-Key-x>", clear_console)


root.mainloop()
