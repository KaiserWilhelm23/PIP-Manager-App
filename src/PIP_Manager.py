version1 = "5.0.1"
import json
import os
import time
import sys

def build_cogs():
    dinct = {
        "darkmode": "on",
        "cmd": "off",
        "cli": "off",
        "install_auto": "yes",
        "pypi": "off"
    }

    cogs = json.dumps(dinct, indent=2)
    with open("src/cogs.json", 'w') as f:
        f.write(cogs)

    print("Built cogs.json....")


try:
    # Open the JSON file
    with open('src/cogs.json', 'r') as file:
        # Load the JSON data
        data = json.load(file)
except Exception as e:
    print(f"ERROR: {e} Building Cogs...")
    build_cogs()
    

################################################################################
#CLI
################################################################################


def cli():
    
    
    user = input("""
 \033[32m┌──(\033[36mPIP-MAnager\033[32m)
 └─$\033[37m """).split()


    try:
        if user[0] == "install":
            try:
                if user[1] == None:
                        print("install needs package")

            except:
                print("\033[31mcmd install needs package \033[32m>> \033[33m install [package]")
                cli()

            
            print(f"installing: {user[1]}")
            print("==="*20)
            os.system(f"pip install {user[1]}")
            print("==="*20)
            cli()


        elif user[0] == "uninstall":
            try:
                if user[1] == None:
                    print("error")

            except:
                print("\033[31mcmd uninstall needs package \033[32m>> \033[33m uninstall [package]")
                cli()

            print(f"unistalling: {user[1]}")
            print("==="*20)
            os.system(f"pip uninstall {user[1]} -y")
            print("==="*20)
            cli()

        elif user[0] == "upgrade":
            try:
                if user[1] == None:
                    print("error")

            except:
                print("\033[31mcmd upgrade needs package \033[32m>> \033[33m upgrade [package]")
                cli()

            print(f"upgrading: {user[1]}")
            print("==="*20)
            os.system(f"pip install {user[1]} --upgrade")
            print("==="*20)
            cli()



        elif user[0] == "help":
            print(
                """\033[33m
  Commands:
  install [package]   -> installs said package 
  uninstall [package] -> uninstalls said package
  upgrade [package]   -> upgrades said package
  list                -> lists all installed packages
  cli off             -> Turns off CLI Mode to start app in GUI Mode

                """
            )
            cli()

        elif user[0] == "list":
            os.system("pip list")
            cli()

        elif user[0] == "clear":
            os.system("clear")
            cli()

        elif user[0] == "exit":
            sys.exit()

        elif user[0] == "cli" and user[1] == "off":
            try:
                with open('src/cogs.json', 'r') as f:
                    data = json.load(f)

                data['cli'] = 'off'

                with open("src/cogs.json", "w") as jsonFile:
                    json.dump(data, jsonFile)

                print("\033[32m CLI Mode is now off")
                cli()

            except:
                print("\033[31m cmd cli needs to be 'cli off'")
                cli()
            
           
        else:
            print(f"\033[31mcmd error: \033[33m'{user[0]}'\033[31m not found")
            cli()



    except:
        cli()


################################################################################
#GUI
################################################################################


try:

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
    import requests
    from bs4 import BeautifulSoup


except Exception as e:

    print("PIP Manager is unable to start, missing packages:")
    user1 = input("Would you like to install y/n/cli: ")

    if user1 == 'y':
        print("=============Installing missing Packages=============")
        os.system("pip install pywin32")
        os.system("pip install ttkthemes")
        build_cogs()


    elif user1 == 'n':
        print("PIP Manager will close in 5 seconds:")
        time.sleep(5)
        sys.exit()

    elif user1 == "cli":
        os.system("clear")
        cli()
        

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
import pkg_resources
from tkinter import messagebox
import urllib.request
import requests
from bs4 import BeautifulSoup
import threading

os.system("clear")

try:
    with open("src/cogs.json", 'r') as f:
        cogs1 = json.loads(f.read())

        if cogs1["cli"] == "on":
            cli()
            

        elif cogs1["cli"] == "off":
            pass
        print("[]")
    print(cogs1)


except Exception as e:
    build_cogs()



try:
    jsongithub_link = "https://blaze005.github.io/items.json"
    with urllib.request.urlopen(jsongithub_link) as url: 
        json_data = json.loads(url.read().decode())
        vr = json_data["PM-release"]
    
except Exception as e:
    print(e)
    vr = "ERROR [NoI]"
    print("No Connection to https://blaze005.github.io/items.json")




root = ThemedTk(theme='breeze')

if vr != version1:
    root.title(f"PIP Manager App {version1} (Update available: {vr})")
    if vr == "ERROR [NoI]":
        root.title(f"PIP Manager App (https://blaze005.github.io/items.json, Out of Reach)")
        


else:
    root.title(f"PIP Manager App {version1}")

tabControl = Notebook(root)
root.geometry("488x390")
root.resizable(0, 0)


menubar = Menu(root)
root.config(menu=menubar)

tab1 = Frame(tabControl)
tab2 = Frame(tabControl)
tab4 = Frame(tabControl)

tabControl.add(tab1, text='Manager')
tabControl.add(tab2, text="Package List")

tabControl.add(tab4, text='Settings')
tabControl.pack(expand=1, fill="both")

global lb1
lb1 = Label(tab1, text="PIP Manager App", font="50")
lb1.pack(pady=15)

lb2 = Label(tab1, text="Type in Module Name:").pack()

global user
user = Combobox(tab1, width=25, height=5)
user.pack(pady=10)

# Create a list to store package names
package_names = []

if vr == "ERROR [NoI]":
     messagebox.showerror(title="ERROR [NoI]: Internet Error", message="Unable to connect to https://blaze005.github.io/items.json")

def fetch_package_names():
    
    with open("src/cogs.json", 'r') as f:
        cogs1 = json.loads(f.read())

        if cogs1["pypi"] == "on":
            try:
            # Fetch package names from PyPI
                print("Fetching Packages from PyPI.....")
                user.config(state=DISABLED)
                response = requests.get('https://pypi.org/simple/')
                soup = BeautifulSoup(response.content, 'html.parser')
                links = soup.find_all('a')
                package_names.extend([link.text for link in links if link.text])
                user.config(state=NORMAL)
            except Exception as e:
                print(e)

        else:
            print("Automatic PyPI Conection Killed")
            pass

    print(package_names)

def fetch_package_names_thread():
    fetch_thread = threading.Thread(target=fetch_package_names)
    fetch_thread.start()

def filter_package_names(event=None):
    module_name = user.get()
    if module_name:
        # Filter package names based on user input
        suggestions = [pkg for pkg in package_names if pkg.startswith(module_name)]
        user['values'] = tuple(suggestions)
    else:
        user['values'] = ()

def display_menu(event):
    user.event_generate("<Down>")

# Start fetching package names in the background
fetch_package_names_thread()

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
    elif command == "upgrade_pip":
        try:
            _thread.start_new_thread(upgrade_pip, ())
        except:
            print("Failed to start thread!")

    elif command == "upgrade2":
        try:
            _thread.start_new_thread(upgrade2, ())
        except:
            print("error")

    elif command == "uninstall2":
        try:
            _thread.start_new_thread(uninstall2, ())
        except:
            print("error")

    elif command == "update_list1":
        try:
            _thread.start_new_thread()

        except:
            print("errror")


    elif command == "auto_py_to_exe":
        try:
            _thread.start_new_thread(auto_py_to_exe, ())

        except:
            print("error")

    elif command == "update_package_list":
        try:
            _thread.start_new_thread(update_package_list, ())

        except:
            print("error")

    else:
        raise ValueError("Not a valid command")

def update_package_list():
    root.title("PIP Manager App V.4.0 (Updating package list)")
    os.system("pip list -o > src/output.txt")
    root.title("PIP Manager App V.4.0")
    messagebox.showinfo(title="Completed", message="Package List Updated. Shutdown and restart PIP Manager to apply changes.")
    
    
def app_info():
    
    import platform
    from tkinter import Tk, Label



    import urllib.request, json

    try:
        jsongithub_link = "https://blaze005.github.io/items.json"
        with urllib.request.urlopen(jsongithub_link) as url: 
            json_data = json.loads(url.read().decode())
            vr = json_data["PM-release"]
    
    except Exception as e:
        print(e)
        vr = "ERROR [NoI]"
        print("No Connection to https://blaze005.github.io/items.json")
    
    
    info_win = Tk()
    info_win.title("App Info")
    info_win.geometry("300x250")
    info_win.resizable(0, 0)

#
# Update function to allow the user to update the app
#
    

    def update():
        import requests
        from tkinter.messagebox import showinfo


        url = 'https://raw.githubusercontent.com/blaze005/PIP-Manager-App/main/src/PIP_Manager.py'
        r = requests.get(url, allow_redirects=True)

        open('PIP_Manager.py', 'wb').write(r.content)
        f = showinfo(title="Complete!!", message=f"PIP Manager is updated to: {vr}!!! Please restart PIP Manager Clicking OK will shut down the app")
        
        if f == "ok":
            sys.exit()


    with open('src/cogs.json', 'r') as file:
    # Load the JSON data
        data = json.load(file)
        data1 = data["App-ID"]
       

    
    Label(info_win, text="PIP Manger App Info").pack()
    Separator(info_win ,orient='horizontal').pack(fill='x')
    Label(info_win, text=f"App Version: {version1}").pack()
    label = Label(info_win, text=f"App-ID: {data1[:8]}").pack()
    Label(info_win, text=f"Current Release: {vr}").pack()
    Label(info_win, text=f"Python Version: {platform.python_version()}").pack()
    Separator(info_win ,orient='horizontal').pack(fill='x')


    if vr != version1:
        Button(info_win, text="Update", command=update).pack()

    else: 
        Label(info_win, text="You are up to date").pack()



def install():
    try:
        f = user.get()
        output = subprocess.getstatusoutput(f"echo [/] Installing: {f}")
        text.config(state=NORMAL)
        text.insert(INSERT, f"{output}\n")
        os.system(f"pip install {f}")
        text.config(state=NORMAL)
        output = subprocess.getstatusoutput(f"echo [+] Sucessfully Installed: {f} [Restart Manager to update the list]")
        text.insert(INSERT, f"{output}\n")
        text.see("end")
        text.config(state=DISABLED)
        _thread.exit()  # Exit running thread cuz it is done
    except Exception as e:
        print(e)




def uninstall():
    try:
        f = user.get()
        output = subprocess.getstatusoutput(f"echo [/] Uninstalling: {f}")
        text.config(state=NORMAL)
        text.insert(INSERT, f"{output}\n")
        os.system(f"pip uninstall {f} -y")
        text.config(state=NORMAL)
        output = subprocess.getstatusoutput(
            f"echo [-] Sucessfully Uninstalled: {f}  [Restart Manager to update the list]")
        text.insert(INSERT, f"{output}\n ")
        text.see("end")
        text.config(state=DISABLED)
        _thread.exit()  # Exit running thread cuz it is done
    except Exception as e:
        print(e)


def upgrade():
    try:
        f = user.get()
        output = subprocess.getstatusoutput(f"echo [/] Upgrading: {f}")
        text.config(state=NORMAL)
        text.insert(INSERT, f"{output}\n")
        os.system(f"pip install {f} --upgrade")
        text.config(state=NORMAL)
        output = subprocess.getstatusoutput(f"echo [-] Sucessfully Upgraded: {f}  [Restart Manager to update the list]")
        text.insert(INSERT, f"{output}\n ")
        text.see("end")
        text.config(state=DISABLED)
        _thread.exit()  # Exit running thread cuz it is done
    except Exception as e:
        print(e)


def upgrade_pip():
    try:
        f = user.get()
        os.system("python -m pip install --upgrade pip")
        text.config(state=NORMAL)
        output = subprocess.getstatusoutput(f"echo [-] Sucessfully Upgraded PIP")
        text.insert(INSERT, f"{output}\n ")
        text.see("end")
        text.config(state=DISABLED)
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


def clear_console(event):
    text.config(state=NORMAL)
    text.delete(1.0, END)
    text.config(state=DISABLED)

def clear_console1():
    text.config(state=NORMAL)
    text.delete(1.0, END)
    text.config(state=DISABLED)



# create a menu
file_menu = Menu(menubar,tearoff=False)
file_menu.add_command(label='Auto-Py-To-EXE',command=lambda: command("auto_py_to_exe"), accelerator="| F1")
file_menu.add_command(label="Update Pacakge List", command=lambda: command("update_package_list"), accelerator="| Ctr+Shift+u")
file_menu.add_command(label="App Info", command=app_info)

file_menu.add_separator()
file_menu.add_command(label="Clear Console", command=clear_console1, accelerator="| Ctrl+x")
file_menu.add_command(label='Exit',command=root.destroy, accelerator="| Ctrl+q")
menubar.add_cascade(label="Quick Access",menu=file_menu)


controls_frame = Frame(tab1)
controls_frame.pack()

install_btn = Button(controls_frame, text="Install", command=lambda: command("install")).grid(row=0, column=0, padx=10)
uninstall_btn = Button(controls_frame, text="Uninstall", command=lambda: command("uninstall")).grid(row=0, column=1,
                                                                                                    padx=10)
upgrade_btn = Button(controls_frame, text="Upgrade", command=lambda: command("upgrade")).grid(row=0, column=2, padx=10)
import_btn = Button(controls_frame, text="Import", command=lambda: command("test_import")).grid(row=0, column=3,
                                                                                                padx=10)
upgrade_pip_btn = Button(tab1, text="Upgrade PIP", command=lambda: command("upgradepip")).pack(pady=10)


# Package List


def selected_item():
    for i in lists.curselection():
        return lists.get(i)


def upgrade2():
    try:
        f = selected_item()
        print(f)
        output1 = subprocess.getstatusoutput(f"echo [/] Upgrading: {f}")
        text.config(state=NORMAL)
        text.insert(INSERT, f"{output1}\n")
        os.system(f"pip install {f} --upgrade")
        text.config(state=NORMAL)
        output1 = subprocess.getstatusoutput(
            f"echo [-] Sucessfully Upgraded: {f}  [Restart Manager to update the list]")
        text.insert(INSERT, f"{output1}\n ")
        text.see("end")
        text.config(state=DISABLED)
        _thread.exit()
    except Exception as e:
        print(e)


def uninstall2():
    try:
        f = selected_item()
        print(f)
        output1 = subprocess.getstatusoutput(f"echo [/] Uninstalling: {f}")
        text.config(state=NORMAL)
        text.insert(INSERT, f"{output1}\n")
        os.system(f"pip uninstall {f} -y")
        text.config(state=NORMAL)
        output1 = subprocess.getstatusoutput(
            f"echo [-] Sucessfully Uninstalled: {f}  [Restart Manager to update the list]")
        text.insert(INSERT, f"{output1}\n ")
        text.see("end")
        text.config(state=DISABLED)
        _thread.exit()
    except Exception as e:
        print(e)


def MetaData_Window():
    from importlib import metadata
    from functools import partial
    f = selected_item()
    info_win = Tk()
    info_win.title(f"MetaData on {f}")
    info_win.geometry("400x200")


    

    info_box = Text(info_win, width=600, height=400, wrap='word')
    info_box.pack()


    pkg = f

    pkg_data = f"""
Name:      {metadata.metadata(pkg)['Name']}
Version:   {metadata.metadata(pkg)['Version']}
Home Page: {metadata.metadata(pkg)['Home-page']}
Author:    {metadata.metadata(pkg)['Author']}
Email:     {metadata.metadata(pkg)['Author-email']}
License:   {metadata.metadata(pkg)['License']}

Python Version Required: {metadata.metadata(pkg)['Requires-Python']}
    """


    info_box.insert('1.0', pkg_data)
    info_box.config(state=DISABLED)
    info_win.mainloop()


def Scankey(event):
    val = event.widget.get()

    if val == '':
        data = sortedPackages
    else:
        data = []
        for item in sortedPackages:
            if val.lower() in item.lower():
                data.append(item)

                

    Update(data)


def Update(data):
    lists.delete(0, 'end')

    # put new data
    for x in range (len(data)):
        lists.insert('end', data[x])
        for package in outdatedPackages:
                if sortedPackages[x] == package:
                    lists.itemconfig(x, {'fg':'red'})


   

pkg_list = Frame(tab2)
pkg_list.pack()
Label(pkg_list, text='Search:').pack()

entry = Entry(pkg_list, textvariable="Search")
entry.pack()
entry.bind('<KeyRelease>', Scankey)

lists = Listbox(pkg_list, width=100, height=10, selectmode=SINGLE)
lists.pack()

installed_packages = pkg_resources.working_set
installed_packages_list = sorted(["%s==%s" % (i.key, i.version)
                                  for i in installed_packages])

installed_packages2_list = pkg_resources.working_set
sortedPackages = []
for i in installed_packages2_list:
    sortedPackages.append(str(i).split(" ")[0])

try:
    file = open('src/output.txt', 'r')
except:
    print("Cannot find file :/")
    with open('src/output.txt', 'w') as f:
        f.write('')

    file = open('src/output.txt', 'r')

chars = True

outdatedPackages = []

while chars:
    line = file.readline()
    if line == "":
        chars = False
    line = line.split(" ")

    outdatedPackages.append(line[0])


try:
    outdatedPackages.pop(0)
    outdatedPackages.pop(0)
    outdatedPackages.sort()

except Exception as e: 
    print("Unable to load outdated packages fixing problem....")
    os.system("pip list -o > src/output.txt")
    

for x in range(len(sortedPackages)):
    lists.insert("end", sortedPackages[x])
    for package in outdatedPackages:
        if sortedPackages[x] == package:
            lists.itemconfig(x, {'fg':'red'})


m = Menu(pkg_list, tearoff=0)

m.add_command(label="Upgarde", command=lambda: command("upgrade2"))
m.add_command(label="Uninstall", command=lambda: command("uninstall2"))
m.add_separator()
m.add_command(label="Package Info", command=MetaData_Window)


def do_popup(event):
    try:
        m.tk_popup(event.x_root, event.y_root)
    finally:
        m.grab_release()


lists.bind("<Button-3>", do_popup)



# settings

with open('src/cogs.json', 'r') as f:
    data = json.load(f)
    mod = data["darkmode"]

if mod == 'on':
    lists.config(foreground='green', background='black', selectbackground='purple')
    m.config(background='black', foreground='green', activebackground='purple')


elif mod == 'off':
    lists.config(foreground='black', background='white', selectbackground='#19849E')
    m.config(background='white', foreground='black', activebackground='#19849E')


def dark_mode():
    if var1.get() == 1:
        root.config(theme='equilux')
        with open('src/cogs.json', 'r') as f:
            data = json.load(f)
        data['darkmode'] = 'on'

        with open("src/cogs.json", "w") as jsonFile:
            json.dump(data, jsonFile)
        lists.config(foreground='green', background='black', selectbackground='purple')
        m.config(background='black', foreground='green', activebackground='purple')

    elif var1.get() == 0:
        root.config(theme='breeze')
        with open('src/cogs.json', 'r') as f:
            data = json.load(f)

        data['darkmode'] = 'off'

        with open("src/cogs.json", "w") as jsonFile:
            json.dump(data, jsonFile)

        lists.config(foreground='black', background='white', selectbackground='#19849E')
        m.config(background='white', foreground='black', activebackground='#19849E')


the_program_to_hide = win32gui.GetForegroundWindow()
win32gui.ShowWindow(the_program_to_hide, win32con.SW_HIDE)


def turn_cmd_off():
    if var2.get() == 1:
        win32gui.ShowWindow(the_program_to_hide, win32con.SW_HIDE)
        with open('src/cogs.json', 'r') as f:
            data = json.load(f)

        data['cmd'] = 'off'

        with open("src/cogs.json", "w") as jsonFile:
            json.dump(data, jsonFile)


    elif var2.get() == 0:
        win32gui.ShowWindow(the_program_to_hide, win32con.SW_SHOW)
        with open('src/cogs.json', 'r') as f:
            data = json.load(f)

        data['cmd'] = 'on'

        with open("src/cogs.json", "w") as jsonFile:
            json.dump(data, jsonFile)


frame = LabelFrame(
    root,
    text='Console: ',

)
frame.pack()

global text
text = Text(frame, width=69, height=8.5, background='black', foreground="green", state=DISABLED)
text.insert(END, "")
text.pack()

settings_frame = Frame(tab4)
settings_frame.pack()

var1 = IntVar()
var2 = IntVar()
var3 = IntVar()
var4 = IntVar()





global cogs
try:
    with open("src/cogs.json", 'r') as f:
        cogs = json.loads(f.read())

        if cogs["darkmode"] == "on":
            root.config(theme='equilux')
            var1.set(1)

        elif cogs["darkmode"] == "off":
            root.config(theme='breeze')
            var1.set(0)
        print(f"[Loaded Darkmode Data] ")
        if cogs["cmd"] == 'on':
            win32gui.ShowWindow(the_program_to_hide, win32con.SW_SHOW)
            var2.set(0)
        elif cogs['cmd'] == 'off':
            win32gui.ShowWindow(the_program_to_hide, win32con.SW_HIDE)
            var2.set(1)
            turn_cmd_off()
        print("[Loaded CMD Info] ")
        if cogs["pypi"] == 'on':
            win32gui.ShowWindow(the_program_to_hide, win32con.SW_SHOW)
            var4.set(0)
        elif cogs['pypi'] == 'off':
            win32gui.ShowWindow(the_program_to_hide, win32con.SW_HIDE)
            var4.set(1)
        print("[Loaded PyPI Info]")
        

    print(cogs)

except Exception as e:
    build_cogs()


def cli_mode():
    if var3.get() == 1:
        
        with open('src/cogs.json', 'r') as f:
            data = json.load(f)
        data['cli'] = 'on'

        with open("src/cogs.json", "w") as jsonFile:
            json.dump(data, jsonFile)
        
    elif var3.get() == 0:
        with open('src/cogs.json', 'r') as f:
            data = json.load(f)

        data['cli'] = 'off'

        with open("src/cogs.json", "w") as jsonFile:
            json.dump(data, jsonFile)


def pypi_off():
    if var4.get() == 1:
        
        with open('src/cogs.json', 'r') as f:
            data = json.load(f)
        data['pypi'] = 'off'

        with open("src/cogs.json", "w") as jsonFile:
            json.dump(data, jsonFile)

        
        
    elif var4.get() == 0:
        with open('src/cogs.json', 'r') as f:
            data = json.load(f)

        data['pypi'] = 'on'

        with open("src/cogs.json", "w") as jsonFile:
            json.dump(data, jsonFile)
        messagebox.showwarning(title="Performance Issues", message="The apps performance may seem slower when this is enabled. RAM will also go up to 1 GIG of usage.")


dark_mode1 = Checkbutton(settings_frame, text="Darkmode", variable=var1, onvalue=1, offvalue=0, command=dark_mode).grid(
    row=1, column=3)

cmd_off = Checkbutton(settings_frame, text="CMD Off", variable=var2, onvalue=1, offvalue=0, command=turn_cmd_off).grid(
    row=2, column=3)

cli_mode1 = Checkbutton(settings_frame, text="CLI",variable=var3, onvalue=1, offvalue=0, command=cli_mode).grid(
    row = 3, column=3)

uato_pypi = Checkbutton(settings_frame, text="Turn Off PyPI DB",variable=var4, onvalue=1, offvalue=0, command=pypi_off).grid(
    row = 4, column=3)

autoexe = Button(settings_frame, text="Auto Py to EXE", command=lambda: command("auto_py_to_exe")).grid(row=5, column=3)

app_info = Button(settings_frame, text="App Info", command=app_info).grid(row=6, column=3)



def auto_py_to_exe():
    with open("src/cogs.json", 'r') as f:
        f = json.loads(f.read())

        if f["install_auto"] == "no":
            user = messagebox.askyesnocancel(title="Auto-Py-to-EXE Installation",
                                             message="This is will install Auto-Py-to-EXE if you already have it, it will upgrade. Do you wish to proceed?")
            if user == True:
                os.system("pip install auto-py-to-exe")

                f['install_auto'] = 'yes'

                with open("src/cogs.json", "w") as jsonFile:
                    json.dump(f, jsonFile)

            else:
                print("None")

        else:
            os.system("auto-py-to-exe")
    _thread.exit()


def quick_upl(event):
    command("update_package_list")

root.bind("<Control-Key-q>", stop_all)
root.bind("<Control-Key-x>", clear_console)
root.bind("<Control-U>", quick_upl)
user.bind("<Return>", display_menu)
user.bind("<KeyRelease>", filter_package_names)




root.after(0, lambda: user.focus())

root.mainloop()
