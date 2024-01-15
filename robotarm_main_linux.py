#   robotarm_main_linux.py
#   Adjusted for 1200x800 Laptop Screen

#   RobotArm Control v1.2 Tintai

version = "1.2"
config = "" # TPARA / ROBOT_ARM_2L

import serial
import serial.tools.list_ports
import tkinter as tk
import re
import os

from cmd_history import CommandHistory
from tkinter import PhotoImage
from tkinter import filedialog
from tkinter import ttk
from tkinter import font
from tooltip import CreateToolTip
from icon_binary import icon_data

history_instance = CommandHistory()
manual_control_enabled = False
gcode_running = False
ser = None  # Global variable
auto_connect = False  # Flag for automatic connection
start_code = False
response_buffer = ""

# Create the main window
root = tk.Tk()
root.title("RobotArm Control")
root.resizable(True, True)

# Set the initial window position to the center of the screen
screen_width = root.winfo_screenwidth()
screen_height = root.winfo_screenheight()
window_width = 1140
window_height = 720

x_position = (screen_width - window_width) // 2
y_position = (screen_height - window_height) // 2
root.geometry(f"{window_width}x{window_height}+{x_position}+{y_position}")

kinematics_var = tk.StringVar()
auto_send_g92_var = tk.BooleanVar()

h0_command_var = tk.BooleanVar()
h0_command_on_var = tk.StringVar()
h0_command_off_var = tk.StringVar()

h1_command_var = tk.BooleanVar()
h1_command_on_var = tk.StringVar()
h1_command_off_var = tk.StringVar()

hb_command_var = tk.BooleanVar()
hb_command_on_var = tk.StringVar()
hb_command_off_var = tk.StringVar()

photo = PhotoImage(data=icon_data)
root.iconphoto(True, photo)

# Function for saving settings to the configuration file
def write_config():
    config_data = {
        "selected_port": port_combobox.get(),
        "baud_rate": baud_rate_combobox.get(),
        "auto_connect": auto_connect_var.get(),
        "start_code": start_code_var.get(),
        "speed": speed_entry.get(),
        "distance": distance_entry.get(),
        "adjustment": precision_entry.get(),
        "gripper_speed": gripper_speed_entry.get(),
        "gripper_dist": gripper_dist_entry.get(),
        "kinematics_type": kinematics_var.get(),
        "auto_send_g92": auto_send_g92_var.get(),
        
        "he0_command": h0_command_var.get(),
        "he0_command_on": h0_command_on_var.get(),
        "he0_command_off": h0_command_off_var.get(),
        "he1_command": h1_command_var.get(),
        "he1_command_on": h1_command_on_var.get(),
        "he1_command_off": h1_command_off_var.get(),
        "hb_command": hb_command_var.get(),
        "hb_command_on": hb_command_on_var.get(),
        "hb_command_off": hb_command_off_var.get(),
    }
    with open("config.ini", "w") as config_file:
        for key, value in config_data.items():
            config_file.write(f"{key}={value}\n")

# Function for reading settings from the configuration file
def read_config():
    try:
        with open("config.ini", "r") as config_file:
            config_data = {}
            for line in config_file:
                key, value = line.strip().split("=")
                config_data[key] = value
            return config_data
    except FileNotFoundError:
        return {}

# Function for handling the Auto Connect button
def auto_connect_handler():
    global auto_connect
    auto_connect = auto_connect_var.get()  # Fix variable read from checkbutton
    if auto_connect:
        scan_ports()
        selected_port = port_combobox.get()
        baud_rate = int(baud_rate_combobox.get())
        if selected_port and baud_rate:
            toggle_connection()

# Function for handling the Start Code checkbox
def start_code_handler():
    global start_code
    start_code = start_code_var.get()  # Fix variable read from checkbutton

# Function to execute Start Code
def execute_start_code():
    # Check if the "Start Code" checkbox is checked
    if start_code_var.get():
        file_path = "start.ini"
        if os.path.exists(file_path):
            # Open the start.ini file and read its contents
            with open(file_path, 'r') as file:
                lines = file.readlines()
                # If yes, send each line using the send_command function
                for line in lines:
                    send_command_text(line.strip(), False)

# Function for scanning available ports
def scan_ports():
    # Clear the current list of ports
    port_combobox['values'] = ()

    # Get the list of available ports
    available_ports = [port.device for port in serial.tools.list_ports.comports()]

    # Place the ports on the selection list
    port_combobox['values'] = available_ports

# Function for establishing/disconnecting the connection
def toggle_connection():
    global ser, auto_connect, response_buffer  # Add variables to the global scope
    selected_port = port_combobox.get()
    baud_rate = int(baud_rate_combobox.get())

    if ser is None:
        # Establish a connection
        try:
            ser = serial.Serial(selected_port, baud_rate, timeout=1)
            status_label['text'] = f"Connected to {selected_port} at {baud_rate} baud"
            status_label['fg'] = 'green'      
            
            connect_enable_u()            
            read_from_port()
            
            auto_connect = False  # Disable automatic connection after manual connection

            # Add this code snippet to display "Connected" in the info_text window
            info_text.configure(state='normal')
            info_text.insert(tk.END, "Connected\n", 'bold_green')
            info_text.configure(state='disabled')
            
            if auto_send_g92_var.get():
                root.after(1000, send_command_text("M114", False))
                root.after(500, send_command_text("G92", False))
            
            root.after(500, execute_start_code)

        except Exception as e:
            status_label['fg'] = 'red'
            status_label['text'] = f"Error: {str(e)}"
    else:
        # Disconnect
        ser.close()
        ser = None
        disconnect_disable_ui()
        
    update_buttons_state()
    
def disconnect_disable_ui():

    # Connection
    status_label['text'] = "Not connected"
    status_label['fg'] = 'black'
    connect_button['text'] = "Connect"
    port_combobox['state'] = 'readonly'
    scan_button['state'] = 'normal'
    baud_rate_combobox['state'] = 'readonly'
    send_button['state'] = 'disabled'

    # Position
    x_label['text'] = "X: 0.00"
    y_label['text'] = "Y: 0.00"
    z_label['text'] = "Z: 0.00"
    e_label['text'] = "E: 0.00"
    rot_label['text'] = "Rot: 0.00"
    low_label['text'] = "Low: 0.00"
    high_label['text'] = "High: 0.00"
    a_label['text'] = "A: 0.00"
    b_label['text'] = "B: 0.00"
    c_label['text'] = "C: 0.00"
    
    # Control
    gcode_disable_ui()
    
    # CMD
    stop_button['state'] = 'disabled'
    motor_on_button['state'] = 'disabled'
    motor_off_button['state'] = 'disabled'
    fan_on_button['state'] = 'disabled'
    fan_off_button['state'] = 'disabled'
    m503_button['state'] = 'disabled'
    m114_button['state'] = 'disabled'
    g92_button['state'] = 'disabled'
    g90_button['state'] = 'disabled'
    g91_button['state'] = 'disabled'

    
def connect_enable_u():
    
    # Connection
    connect_button['text'] = "Disconnect"
    port_combobox['state'] = 'disabled'
    scan_button['state'] = 'disabled'
    baud_rate_combobox['state'] = 'disabled'
    send_button['state'] = 'normal'

    # Control
    gcode_enable_ui()
    
    # CMD
    stop_button['state'] = 'normal'
    motor_on_button['state'] = 'normal'
    motor_off_button['state'] = 'normal'
    fan_on_button['state'] = 'normal'
    fan_off_button['state'] = 'normal'
    m503_button['state'] = 'normal'
    m114_button['state'] = 'normal'
    g92_button['state'] = 'normal'
    g90_button['state'] = 'normal'
    g91_button['state'] = 'normal'
    
def gcode_disable_ui():
    precision_x_plus_button['state'] = 'disabled'
    precision_x_minus_button['state'] = 'disabled'
    precision_y_plus_button['state'] = 'disabled'
    precision_y_minus_button['state'] = 'disabled'
    precision_z_plus_button['state'] = 'disabled'
    precision_z_minus_button['state'] = 'disabled'
    x_plus_button['state'] = 'disabled'
    x_minus_button['state'] = 'disabled'
    y_plus_button['state'] = 'disabled'
    y_minus_button['state'] = 'disabled'
    z_plus_button['state'] = 'disabled'
    z_minus_button['state'] = 'disabled'
    e0_plus_button['state'] = 'disabled'
    e0_minus_button['state'] = 'disabled'
    move_button['state'] = 'disabled'
    set_position_button['state'] = 'disabled'
    
def gcode_enable_ui():
    precision_x_plus_button['state'] = 'normal'
    precision_x_minus_button['state'] = 'normal'
    precision_y_plus_button['state'] = 'normal'
    precision_y_minus_button['state'] = 'normal'
    precision_z_plus_button['state'] = 'normal'
    precision_z_minus_button['state'] = 'normal'
    x_plus_button['state'] = 'normal'
    x_minus_button['state'] = 'normal'
    y_plus_button['state'] = 'normal'
    y_minus_button['state'] = 'normal'
    z_plus_button['state'] = 'normal'
    z_minus_button['state'] = 'normal'
    e0_plus_button['state'] = 'normal'
    e0_minus_button['state'] = 'normal'
    move_button['state'] = 'normal'
    set_position_button['state'] = 'normal'

# Function for reading responses from the port
def read_from_port():
    global ser, response_buffer
    if ser is not None and ser.in_waiting > 0:
        response = ser.read(ser.in_waiting).decode()
        response_buffer += response

        # Add each response line to the information window
        lines = response_buffer.split('\n')
        info_text.configure(state='normal')

        for line in lines[:-1]:  # Skip the last line as it may be incomplete
            if line.strip() != 'ok':  # Add the line only if it does not contain only "ok"
                info_text.insert(tk.END, f"{line}\n")

        response_buffer = lines[-1]  # Keep the incomplete line for future use

        update_position(lines)

        info_text.configure(state='disabled')
        info_text.yview(tk.END)  # Automatically scroll to the last entry

    # Add this call to continue reading
    root.after(100, read_from_port)

# Function for closing the program
def on_close():
    if ser is not None:
        ser.close()
    write_config()  # Save current settings before closing the program
    root.destroy()

# Function handling machine movement in X, Y, Z planes
def move_machine(direction, distance, speed):
    global ser
    if ser is not None:
        send_command_text("G91", False)
        command = f"G0 {direction}{distance} F{speed}"
        send_command_text(command, True)
        send_command_text("G90", False)
        if auto_send_g92_var.get():
            send_command_text("G92", False)

# Function handling machine movement in E planes
def move_machine_e(direction, distance, speed):
    global ser
    if kinematics_var.get() == "ROBOT_ARM_2L":
        cmd = "G0"
    else:
        cmd = "G1"
        
    if ser is not None:
        send_command_text("G91", False)
        command = f"{cmd} {direction}{distance} F{speed}"
        send_command_text(command, True)
        send_command_text("G90", False)
        if auto_send_g92_var.get():
            send_command_text("G92", False)

# Function for manual position movement
def move_position_manual():
    x_value = x_entry_manual.get()
    y_value = y_entry_manual.get()
    z_value = z_entry_manual.get()

    speed_value = speed_entry.get()
    if not speed_value or float(speed_value) == 0:
        command = f"G1 X{x_value} Y{y_value} Z{z_value}"
    else:
        command = f"G1 X{x_value} Y{y_value} Z{z_value} F{speed_value}"
    send_command_text(command, True)
    if auto_send_g92_var.get():
        send_command_text("G92", False)

# Function for adding manual position
def add_position_manual():
    x_value = x_entry_manual.get()
    y_value = y_entry_manual.get()
    z_value = z_entry_manual.get()

    speed_value = speed_entry.get()
    if not speed_value or float(speed_value) == 0:
        command = f"G1 X{x_value} Y{y_value} Z{z_value}"
    else:
        command = f"G1 X{x_value} Y{y_value} Z{z_value} F{speed_value}"
    position_listbox.insert(tk.END, command)
    
# Function for sending a command
def send_command_to_seq_entry(event=None):
    command = command_entry.get().strip()
    if command:
        command = command.upper()
        position_listbox.insert(tk.END, command)
        command_entry.delete(0, tk.END)

def send_command_entry(event=None):
    command = command_entry.get().strip()  # Remove leading and trailing whitespaces from the command

    if command:
        if command.startswith('/'):
            handle_special_command(command)
        else:
            send_command_text(command, True)
            history_instance.add_command(command)

        command_entry.delete(0, tk.END)

def handle_special_command(command):
    if command == '/clean' or command == '/clear':
        info_text.configure(state='normal')
        info_text.delete("1.0", tk.END)
        info_text.configure(state='disabled')
    #pass
    if command == '/set' or command == '/settings':
        show_settings_window()
    #pass
        
# Function to update command_entry from history
def update_entry_from_history(new_command):
    command_entry.delete(0, tk.END)
    command_entry.insert(0, new_command)

# Function for sending machine movement command
def send_command_text(command, show):
    global ser, response_buffer
    if ser is not None:
        try:
            command = command.upper()
            ser.write(command.encode() + b'\n')

            # Color, boldness, and lock settings for info_text
            if show:
                info_text.configure(state='normal')
                info_text.insert(tk.END, f"\n>>> {command}\n\n", 'bold_green')
                info_text.configure(state='disabled')

            print(f"Sending command: {command}")

        except Exception as e:
            if show:
                info_text.configure(state='normal')
                info_text.insert(tk.END, f"\nError: {str(e)}\n\n", 'bold_red')
                info_text.configure(state='disabled')
        finally:
            if show:
                info_text.yview(tk.END)

# Function for adding a tooltip to a button
def add_tooltip(widget, text):
    widget_tooltip = CreateToolTip(widget, text)

def update_labels_pos(g92_data):
    if g92_data:
        x_label['text'] = f"X: {g92_data['x_position']:.2f}" if g92_data['x_position'] is not None else x_label['text']
        y_label['text'] = f"Y: {g92_data['y_position']:.2f}" if g92_data['y_position'] is not None else y_label['text']
        z_label['text'] = f"Z: {g92_data['z_position']:.2f}" if g92_data['z_position'] is not None else z_label['text']
        e_label['text'] = f"E: {g92_data['e_position']:.2f}" if g92_data['e_position'] is not None else e_label['text']
        rot_label['text'] = f"Rot: {g92_data['rot_value']:.2f}" if g92_data['rot_value'] is not None else rot_label['text']
        low_label['text'] = f"Low: {g92_data['low_value']:.2f}" if g92_data['low_value'] is not None else low_label['text']
        high_label['text'] = f"High: {g92_data['high_value']:.2f}" if g92_data['high_value'] is not None else high_label['text']

        a_label['text'] = f"A: {g92_data['a_position']:.2f}" if g92_data['a_position'] is not None else y_label['text']
        b_label['text'] = f"B: {g92_data['b_position']:.2f}" if g92_data['b_position'] is not None else z_label['text']
        c_label['text'] = f"C: {g92_data['c_position']:.2f}" if g92_data['c_position'] is not None else e_label['text']
    else:
        pass

def update_position(lines):

    if kinematics_var.get() == "ROBOT_ARM_2L":
        match_conf1 = r'X:(-?\d+\.\d+) Y:(-?\d+\.\d+) Z:(-?\d+\.\d+) E:(-?\d+\.\d+) Count A:(-?\d+) B:(-?\d+) C:(-?\d+)'
        match_conf2 = r'ROBOT_ARM_2L rot:(-?\d+\.\d+)  low(-?\d+\.\d+) high: (-?\d+\.\d+)'
    else: # TPARA
        match_conf1 = r'X:(-?\d+\.\d+) Y:(-?\d+\.\d+) Z:(-?\d+\.\d+) E:(-?\d+\.\d+) A:(-?\d+) B:(-?\d+) C:(-?\d+)'
        match_conf2 = r'TPARA ROT: (-?\d+\.\d+) LOW: (-?\d+\.\d+) HIGH: (-?\d+\.\d+)'
    
    g92_data = { }

    for line in lines:
        try:
            match_g92 = re.match(match_conf1, line)
            if match_g92:
                g92_data['x_position'] = float(match_g92.group(1))
                g92_data['y_position'] = float(match_g92.group(2))
                g92_data['z_position'] = float(match_g92.group(3))
                g92_data['e_position'] = float(match_g92.group(4))
                g92_data['a_position'] = float(match_g92.group(5))
                g92_data['b_position'] = float(match_g92.group(6))
                g92_data['c_position'] = float(match_g92.group(7))
                continue

            match_tpara = re.match(match_conf2, line)
            if match_tpara:
                g92_data['rot_value'] = float(match_tpara.group(1))
                g92_data['low_value'] = float(match_tpara.group(2))
                g92_data['high_value'] = float(match_tpara.group(3))
                continue

        except AttributeError:
            pass

    try:
        if 'x_position' in g92_data or 'a_position' in g92_data:
            update_labels_pos(g92_data)
    except KeyError:
        pass

    print(g92_data)
    
def set_default_title():
    root.title("RobotArm Control")
  
def run_gcode(loop_var):
    global gcode_running
    delay = 0.3
    positions = position_listbox.get(0, tk.END)
    total_positions = len(positions)
    
    info_text.configure(state='normal')
    info_text.insert(tk.END, "G-Code Started\n", 'bold_green')
    info_text.insert(tk.END, f"Positions count: {total_positions}\n", 'bold_green')
    info_text.configure(state='disabled')
    info_text.yview(tk.END)

    gcode_running = [True]

    def run_next_command(index=0):
        nonlocal total_positions

        if gcode_running[0] and index < len(positions):
            position = positions[index]
            command_without_description = clean_command(position).strip()

            print(f"Running command: {command_without_description}")

            # Sending the command to the device
            send_command_text(command_without_description, True)

            # Checking if the response meets the conditions
            root.after(500, lambda: check_info_text_for_match(index + 1))
        elif loop_var.get() and gcode_running[0]:
            # If loop_var option is True and gcode_running is True, execute the entire list again
            root.after(int(delay * 1000), lambda: run_next_command(0))
        else:
            stop_gcode_execution()
            print("All commands executed.")
            
            info_text.configure(state='normal')
            info_text.insert(tk.END, "G-Code Execution Completed\n", 'bold_red')
            info_text.insert(tk.END, f"All positions executed: {total_positions}\n", 'bold_red')
            info_text.configure(state='disabled')
            info_text.yview(tk.END)
             
            root.after(0, set_default_title)

        send_command_text("G92", False)  # Optional, depending on requirements

        # Update the title with the current and total positions
        root.title(f"[{index}/{total_positions}] RobotArm Control")

    def clean_command(command):
        command = command.replace(":", "")
        command = re.sub(r'\[.*?\]', '', command)
        return command

    def check_info_text_for_match(next_index):
        global config
        if kinematics_var.get() == "ROBOT_ARM_2L":
            check_var = "ROBOT_ARM_2L"
        else:
            check_var = "[TPARA]"

        
        nonlocal total_positions

        # Get the current content of info_text
        info_text_content = info_text.get("1.0", "end-1c")

        # Check if the last line contains check_var, if not, check the second-to-last line
        if check_var in info_text_content.splitlines()[-1]:
            latest_line = info_text_content.splitlines()[-1]
        elif len(info_text_content.splitlines()) > 1:
            latest_line = info_text_content.splitlines()[-2]
        else:
            latest_line = ""

        # Check if check_var appears in the latest line of info_text
        if check_var in latest_line:
            print(f"{check_var} found in the latest line. Proceeding to the next command.")
            root.after(100, lambda: run_next_command(next_index))
        else:
            # Check again after a short period
            root.after(100, lambda: check_info_text_for_match(next_index))

    # Run the first command
    run_next_command(0)
       
def toggle_gcode_execution(loop_var):
    global gcode_running
    if gcode_running:
        stop_gcode_execution()
        info_text.configure(state='normal')
        info_text.insert(tk.END, "G-Code Execution Aborted\n", 'bold_red')
        info_text.configure(state='disabled')
        info_text.yview(tk.END)
    else:
        start_gcode_execution(loop_var)

def start_gcode_execution(loop_var):
    global gcode_running
    gcode_running = True
    run_button.config(text="STOP G-Code", fg="white", bg="red")
    run_gcode(loop_var)
    gcode_disable_ui()
    update_buttons_state()

def stop_gcode_execution():
    global gcode_running
    gcode_running = False
    run_button.config(text="START G-Code", fg="black", bg="lightgrey")
    gcode_enable_ui()
    update_buttons_state()
    root.after(0, set_default_title)
    
def reverse_positions():
    positions = position_listbox.get(0, tk.END)
    reversed_positions = list(reversed(positions))

    position_listbox.delete(0, tk.END)

    for position in reversed_positions:
        position_listbox.insert(tk.END, position)

def edit_file():
    file_path = "start.ini"

    # Check if the start.ini file exists
    if os.path.exists(file_path):
        # Open the start.ini file in the default text editor
        os.system(f"xdg-open {file_path}")
    else:
        # If the file does not exist, create and open it in the default text editor
        with open(file_path, 'w') as file:
            file.write("")
        os.system(f"xdg-open {file_path}")

def add_position():
    x_value = x_label['text'][3:]  # Get the X value from the label
    y_value = y_label['text'][3:]  # Get the Y value from the label
    z_value = z_label['text'][3:]  # Get the Z value from the label

    # Create a dialog window
    dialog_window = tk.Toplevel(root)
    dialog_window.title("Add Position")
    dialog_window.resizable(False, False)
    dialog_window.attributes("-topmost", True)
    dialog_window.grab_set()

    # Set the size and position of the dialog window
    dialog_window.geometry("300x200+{}+{}".format(root.winfo_x() + 450, root.winfo_y() + 450))

    # Dialog window elements
    prompt_label = ttk.Label(dialog_window, text="Description:")
    prompt_label.pack(pady=5)

    entry_var = tk.StringVar()
    entry = ttk.Entry(dialog_window, textvariable=entry_var)
    entry.pack(pady=5)

    speed_label = ttk.Label(dialog_window, text="Speed:")
    speed_label.pack(pady=5)

    speed_var = tk.StringVar(value=speed_entry.get())  # Default speed value
    speed_entry_dialog = ttk.Entry(dialog_window, textvariable=speed_var)
    speed_entry_dialog.pack(pady=5)

    def add_and_close(event=None):
        description = entry_var.get()
        speed = speed_var.get()

        # Create the command based on the presence of speed and description
        if description and speed:
            entry_text = f"G1 X: {x_value} Y: {y_value} Z: {z_value} F{speed} [{description}]"
        elif description:
            entry_text = f"G1 X: {x_value} Y: {y_value} Z: {z_value} [{description}]"
        elif speed:
            entry_text = f"G1 X: {x_value} Y: {y_value} Z: {z_value} F{speed}"
        else:
            entry_text = f"G1 X: {x_value} Y: {y_value} Z: {z_value}"

        position_listbox.insert(tk.END, entry_text)
        dialog_window.destroy()
        update_buttons_state()

    add_button = ttk.Button(dialog_window, text="Add", command=add_and_close)
    add_button.pack(pady=10)
    entry.bind("<Return>", add_and_close)
    speed_entry.bind("<Return>", add_and_close)
    entry.focus_set()
    
def moveto_position_fast():
    moveto_position()
    
def moveto_position():
    # Get the selected item from the list
    selected_index = position_listbox.curselection()

    if selected_index:
        selected_command = position_listbox.get(selected_index)

        # Remove colons between values and description in square brackets from the command
        command_without_colons = re.sub(r':', '', selected_command)
        command_without_description = re.sub(r'\[.*?\]', '', command_without_colons).strip()

        # Send the command for execution
        print(f"Executing command: {command_without_description}")
        send_command_text(command_without_description, True)
        if auto_send_g92_var.get():
            send_command_text("G92", False)

def save_position():
    file_path = filedialog.asksaveasfilename(defaultextension=".gcode", filetypes=[("G-Code", "*.gcode")])

    if file_path:
        with open(file_path, 'w') as file:
            for index in range(position_listbox.size()):
                file.write(position_listbox.get(index) + '\n')

def load_position():
    file_path = filedialog.askopenfilename(filetypes=[("G-Code", "*.gcode")])

    if file_path:
        # Read the content of the file into the position list
        with open(file_path, 'r') as file:
            positions = file.readlines()

        # Remove any previous positions from the listbox
        position_listbox.delete(0, tk.END)

        # Add the loaded positions to the listbox
        for position in positions:
            position_listbox.insert(tk.END, position.strip())
        update_buttons_state()

def delete_and_close():
    response = response_var.get()
    
    if response == "Yes":
        selected_index = position_listbox.curselection()
        if selected_index:
            position_listbox.delete(selected_index)

    elif response == "RemoveAll":
        position_listbox.delete(0, tk.END)

    dialog_window.destroy()
    update_buttons_state()
    
def clear_selection_listbox(event):
    position_listbox.selection_clear(0, tk.END)
    update_buttons_state()

def delete_position_fast():
    selected_index = position_listbox.curselection()
    if selected_index:
        position_listbox.delete(selected_index)
        update_buttons_state()

def delete_position(event=None):
    selected_index = position_listbox.curselection()

    if selected_index:
        description = position_listbox.get(selected_index)

        # Create a dialog window
        global dialog_window
        dialog_window = tk.Toplevel(root)
        dialog_window.title("Delete Position")
        dialog_window.resizable(False, False)
        dialog_window.attributes("-topmost", True)
        dialog_window.grab_set()

        # Set the size and position of the dialog window
        dialog_window.geometry("300x120+{}+{}".format(root.winfo_x() + 450, root.winfo_y() + 450))

        # Dialog window elements
        prompt_label = ttk.Label(dialog_window, text=f"Delete position: {description}?")
        prompt_label.pack(pady=10)

        global response_var
        response_var = tk.StringVar(value="No")
        response_var.trace("w", lambda name, index, mode, sv=response_var: delete_and_close())

        delete_button = ttk.Button(dialog_window, text="Delete", command=lambda: response_var.set("Yes"))
        delete_button.pack(side="left", padx=10)

        remove_all_button = ttk.Button(dialog_window, text="Remove All", command=lambda: response_var.set("RemoveAll"))
        remove_all_button.pack(side="left", padx=10)

        cancel_button = ttk.Button(dialog_window, text="Cancel", command=lambda: response_var.set("Cancel"))
        cancel_button.pack(side="right", padx=10)
        
        dialog_window.protocol("WM_DELETE_WINDOW", lambda: response_var.set("Cancel"))

def update_buttons_state():
    selected_index = position_listbox.curselection()
    global gcode_running
    if ser is not None and gcode_running:
        set_position_button['state'] = 'disabled'
    else:
        set_position_button['state'] = 'normal'
        
    # Update the state of buttons based on the selection in the listbox
    if selected_index:
        delete_button['state'] = 'normal'
        #set_position_button['state'] = 'normal'
    else:
        delete_button['state'] = 'disabled'
        #set_position_button['state'] = 'disabled'

    if position_listbox.size() > 0:
        save_button['state'] = 'normal'
    else:
        save_button['state'] = 'disabled'
              
    #total_positions = position_listbox.size()
    #if selected_index:
    #    selected_position = int(selected_index[0]) + 1
    #    sequence_frame.config(text=f"G-Code {selected_position} / {total_positions}")
    #else:
    #    sequence_frame.config(text=f"G-Code 0 / {total_positions}")
        
    if ser is not None and position_listbox.size() > 0:
        run_button['state'] = 'normal'
    else:
        run_button['state'] = 'disabled'

        
def toggle_manual_control():
    global manual_control_enabled
    manual_control_enabled = not manual_control_enabled
    if manual_control_enabled:
        info_text.configure(state='normal')
        info_text.insert(tk.END, "Manual control enabled\n", 'bold_green')
        info_text.insert(tk.END, "Use arrows to control X and Y. Ctrl+Arrows control Z and E\n", 'bold')
        info_text.configure(state='disabled')
        info_text.yview(tk.END)
        print("Manual control enabled")
        manual_control_button.config(bg="green", fg="white")
        precision_x_plus_button.config(bg="green", fg="white")
        precision_x_minus_button.config(bg="green", fg="white")
        precision_y_plus_button.config(bg="green", fg="white")
        precision_y_minus_button.config(bg="green", fg="white")
        precision_z_plus_button.config(bg="green", fg="white")
        precision_z_minus_button.config(bg="green", fg="white")
        e0_plus_button.config(bg="green", fg="white")
        e0_minus_button.config(bg="green", fg="white")      
    else:
        info_text.configure(state='normal')
        info_text.insert(tk.END, "Manual control disabled\n", 'bold_red')
        info_text.configure(state='disabled')
        info_text.yview(tk.END)
        print("Manual control disabled")
        manual_control_button.config(bg="lightgray", fg="black")
        precision_x_plus_button.config(bg="lightgray", fg="red")
        precision_x_minus_button.config(bg="lightgray", fg="red")
        precision_y_plus_button.config(bg="lightgray", fg="blue")
        precision_y_minus_button.config(bg="lightgray", fg="blue")
        precision_z_plus_button.config(bg="lightgray", fg="green")
        precision_z_minus_button.config(bg="lightgray", fg="green")
        e0_plus_button.config(bg="lightgray", fg="purple")
        e0_minus_button.config(bg="lightgray", fg="purple")


def on_key(event):
    if manual_control_enabled:
        if event.keysym == "Up":
            if event.state & 0x4:  # Check if Ctrl key is pressed
                move_machine("Z+", float(precision_entry.get()), float(speed_entry.get()))
            else:
                move_machine("Y+", float(precision_entry.get()), float(speed_entry.get()))
        elif event.keysym == "Down":
            if event.state & 0x4:  # Check if Ctrl key is pressed
                move_machine("Z-", float(precision_entry.get()), float(speed_entry.get()))
            else:
                move_machine("Y-", float(precision_entry.get()), float(speed_entry.get()))
        elif event.keysym == "Left":
            if event.state & 0x4:  # Check if Ctrl key is pressed
                move_machine_e("E-", float(gripper_dist_entry.get()), float(gripper_speed_entry.get()))
            else:
                move_machine("X-", float(precision_entry.get()), float(speed_entry.get()))
        elif event.keysym == "Right":
            if event.state & 0x4:  # Check if Ctrl key is pressed
                move_machine_e("E+", float(gripper_dist_entry.get()), float(gripper_speed_entry.get()))
            else:
                move_machine("X+", float(precision_entry.get()), float(speed_entry.get()))
                
def kinematics_type_update():
    global config
    if kinematics_var.get() == "ROBOT_ARM_2L":
        config = "ROBOT_ARM_2L"
    else:
        config = "TPARA"
        
    if hasattr(root, "config_label"):
        root.config_label.destroy()

    root.config_label = tk.Label(root, text=config)
    root.config_label.grid(row=2, column=1, ipadx=0, ipady=0, sticky='s')
        
    print(config)
                
def apply_settings_from_config():
    
    global h0_textbox_on, h0_textbox_off, h1_textbox_on, h1_textbox_off, hb_textbox_on, hb_textbox_off
    config_data = read_config()
    
    kinematics_var.set(config_data.get("kinematics_type", "TPARA"))
    auto_send_g92_var.set(config_data.get("auto_send_g92", False))
    
    h0_command_var.set(config_data.get("he0_command", False))    
    h1_command_var.set(config_data.get("he1_command", False))
    hb_command_var.set(config_data.get("hb_command", False))
    
    h0_command_var.set(config_data.get("he0_command", False))
    h0_command_on_var.set(config_data.get("he0_command_on", "M104 S100"))
    h0_command_off_var.set(config_data.get("he0_command_off", "M104 S0"))

    h1_command_var.set(config_data.get("he1_command", False))
    h1_command_on_var.set(config_data.get("he1_command_on", "M171 P1"))
    h1_command_off_var.set(config_data.get("he1_command_off", "M171 P0"))

    hb_command_var.set(config_data.get("hb_command", False))
    hb_command_on_var.set(config_data.get("hb_command_on", "M170 P1"))
    hb_command_off_var.set(config_data.get("hb_command_off", "M170 P0"))

    if 'h0_button_on' in globals():
        h0_button_on['state'] = 'disabled' if not h0_command_var.get() else 'normal'
    if 'h0_button_off' in globals():
        h0_button_off['state'] = 'disabled' if not h0_command_var.get() else 'normal'

    if 'h1_button_on' in globals():
        h1_button_on['state'] = 'disabled' if not h1_command_var.get() else 'normal'
    if 'h1_button_off' in globals():
        h1_button_off['state'] = 'disabled' if not h1_command_var.get() else 'normal'

    if 'hb_button_on' in globals():
        hb_button_on['state'] = 'disabled' if not hb_command_var.get() else 'normal'
    if 'hb_button_off' in globals():
        hb_button_off['state'] = 'disabled' if not hb_command_var.get() else 'normal'

    
    print(f"h0_command_var: {h0_command_var.get()}, h0_command_on_var: {h0_command_on_var.get()}, h0_command_off_var: {h0_command_off_var.get()}, h1_command_var: {h1_command_var.get()}, h1_command_on_var: {h1_command_on_var.get()}, h1_command_off_var: {h1_command_off_var.get()}, hb_command_var: {hb_command_var.get()}, hb_command_on_var: {hb_command_on_var.get()}, hb_command_off_var: {hb_command_off_var.get()}")


def show_settings_window():
        
    global h0_textbox_on; global h0_textbox_off; global h1_textbox_on; global h1_textbox_off; global hb_textbox_on; global hb_textbox_off
    global h0_command_on_var; global h0_command_off_var
    
    settings_window = tk.Toplevel(root)
    settings_window.title("Settings")
    settings_window.resizable(False, False)
    settings_window.attributes("-topmost", True)
    settings_window.grab_set()

    settings_window.geometry("300x340+{}+{}".format(root.winfo_x() + 50, root.winfo_y() + 150))

    settings_window.protocol("WM_DELETE_WINDOW", lambda: (write_config(), kinematics_type_update(), apply_settings_from_config(), settings_window.destroy()))

    # Kinematics type
    kinematics_label = ttk.Label(settings_window, text="Kinematics type:")
    kinematics_label.grid(row=0, column=0, padx=10, pady=5, sticky='w')

    kinematics_options = ["TPARA", "ROBOT_ARM_2L"]

    kinematics_dropdown = ttk.Combobox(settings_window, textvariable=kinematics_var, values=kinematics_options, state="readonly", width=15)
    kinematics_dropdown.grid(row=0, column=1, padx=5, pady=5, sticky='w')

    # Auto Send G92 checkbox
    auto_send_checkbox = ttk.Checkbutton(settings_window, text="Auto Send G92 after move", variable=auto_send_g92_var)
    auto_send_checkbox.grid(row=1, column=0, columnspan=2, padx=10, pady=5, sticky='w')
    
    separator = ttk.Separator(settings_window, orient='horizontal')
    separator.grid(row=2, column=0, columnspan=2, sticky='ew', pady=10)

    h0_checkbox = ttk.Checkbutton(settings_window, text="HE0 ON", variable=h0_command_var)
    h0_checkbox.grid(row=3, column=0, padx=10, pady=5, sticky='w')

    h0_textbox_on = ttk.Entry(settings_window, textvariable=h0_command_on_var, width=15)
    h0_textbox_on.grid(row=3, column=1, padx=10, pady=5, sticky='w')

    h0_label = ttk.Label(settings_window, text="HE0 OFF")
    h0_label.grid(row=4, column=0, padx=20, pady=5, sticky='w')

    h0_textbox_off = ttk.Entry(settings_window, textvariable=h0_command_off_var, width=15)
    h0_textbox_off.grid(row=4, column=1, padx=10, pady=5, sticky='w')

    separator = ttk.Separator(settings_window, orient='horizontal')
    separator.grid(row=5, column=0, columnspan=2, sticky='ew', pady=10)

    h1_checkbox = ttk.Checkbutton(settings_window, text="HE1 ON", variable=h1_command_var)
    h1_checkbox.grid(row=6, column=0, padx=10, pady=5, sticky='w')

    h1_textbox_on = ttk.Entry(settings_window, textvariable=h1_command_on_var, width=15)
    h1_textbox_on.grid(row=6, column=1, padx=10, pady=5, sticky='w')

    h1_label = ttk.Label(settings_window, text="HE1 OFF")
    h1_label.grid(row=7, column=0, padx=20, pady=5, sticky='w')

    h1_textbox_off = ttk.Entry(settings_window, textvariable=h1_command_off_var, width=15)
    h1_textbox_off.grid(row=7, column=1, padx=10, pady=5, sticky='w')
    
    separator = ttk.Separator(settings_window, orient='horizontal')
    separator.grid(row=8, column=0, columnspan=2, sticky='ew', pady=10)

    hb_checkbox = ttk.Checkbutton(settings_window, text="HB ON", variable=hb_command_var)
    hb_checkbox.grid(row=9, column=0, padx=10, pady=5, sticky='w')

    hb_textbox_on = ttk.Entry(settings_window, textvariable=hb_command_on_var, width=15)
    hb_textbox_on.grid(row=9, column=1, padx=10, pady=5, sticky='w')

    hb_label = ttk.Label(settings_window, text="HB OFF")
    hb_label.grid(row=10, column=0, padx=20, pady=5, sticky='w')

    hb_textbox_off = ttk.Entry(settings_window, textvariable=hb_command_off_var, width=15)
    hb_textbox_off.grid(row=10, column=1, padx=10, pady=5, sticky='w')
    
def mosfet_control(mosfet, state):
    command_mapping = {
        "h0": {
            0: h0_command_off_var.get(),
            1: h0_command_on_var.get()
        },
        "h1": {
            0: h1_command_off_var.get(),
            1: h1_command_on_var.get()
        },
        "hb": {
            0: hb_command_off_var.get(),
            1: hb_command_on_var.get()
        }
    }

    if mosfet in command_mapping:
        if state in command_mapping[mosfet]:
            command = command_mapping[mosfet][state]
            send_command_text(command, True)
            print(command)

        
apply_settings_from_config()

root.bind("<KeyPress>", on_key)

# Bind the on_close() function to the window close event
root.protocol("WM_DELETE_WINDOW", on_close)

# Additional frame for grouping controls related to connection
connection_frame = ttk.LabelFrame(root, text="Connection")
connection_frame.grid(row=0, column=0, pady=0, padx=10, sticky='w')

# Button for scanning ports
scan_button = tk.Button(connection_frame, text="Scan Ports", command=scan_ports)
scan_button.grid(row=0, column=0, pady=10, padx=10, sticky='w')

# Dropdown list with available ports
port_combobox = ttk.Combobox(connection_frame, state="readonly", width=11)
port_combobox.grid(row=0, column=1, pady=10, sticky='w')

# Dropdown list with baud rates
baud_rate_combobox = ttk.Combobox(connection_frame, values=[2400, 9600, 19200, 38400, 57600, 115200, 250000], state="readonly", width=7)
baud_rate_combobox.set(115200)  # Default baud rate
baud_rate_combobox.grid(row=0, column=2, pady=10, padx=10, sticky='w')

# Button for connecting/disconnecting
connect_button = tk.Button(connection_frame, text="Connect", command=toggle_connection, width=7)
connect_button.grid(row=0, column=3, pady=10, padx=3, sticky='w')

# Checkbutton for auto-connect
auto_connect_var = tk.BooleanVar()
auto_connect_checkbox = tk.Checkbutton(connection_frame, text="Auto Connect", variable=auto_connect_var, width=10)
auto_connect_checkbox.grid(row=0, column=4, pady=10, padx=1, sticky='w')

# Additional frame for grouping controls related to communication
communication_frame = ttk.LabelFrame(root, text="Communication")
communication_frame.grid(row=1, column=0, pady=0, padx=10, sticky='w')

# Frame for G-Code controls
sequence_frame = ttk.LabelFrame(root, text="G-Code", height=10)
sequence_frame.grid(row=2, column=0, padx=10, pady=0, sticky="w")

sequence_frame_buttons = ttk.LabelFrame(sequence_frame, width=8, height=8)
sequence_frame_buttons.grid(row=0, column=1, padx=0, pady=0, sticky="n")

# Create the manual_position group
manual_position = ttk.LabelFrame(sequence_frame, width=7, height=10)
manual_position.grid(row=0, column=2, padx=10, pady=0, sticky="ne")

# Create labels and numeric fields for X, Y, Z
x_label_manual = tk.Label(manual_position, text="X:", foreground="red", font=('Arial', 12, 'bold'))
x_label_manual.grid(row=0, column=0, padx=5, pady=5, sticky="n")
x_entry_manual = tk.Entry(manual_position, width=5)
x_entry_manual.grid(row=0, column=1, padx=5, pady=5)
x_entry_manual.insert(0, "0")

y_label_manual = tk.Label(manual_position, text="Y:", foreground="blue", font=('Arial', 12, 'bold'))
y_label_manual.grid(row=2, column=0, padx=5, pady=5, sticky="n")
y_entry_manual = tk.Entry(manual_position, width=5)
y_entry_manual.grid(row=2, column=1, padx=5, pady=5)
y_entry_manual.insert(0, "180")

z_label_manual = tk.Label(manual_position, text="Z:", foreground="green", font=('Arial', 12, 'bold'))
z_label_manual.grid(row=3, column=0, padx=5, pady=5, sticky="n")
z_entry_manual = tk.Entry(manual_position, width=5)
z_entry_manual.grid(row=3, column=1, padx=5, pady=5)
z_entry_manual.insert(0, "180")

# Create MOVE and ADD buttons
move_button = tk.Button(manual_position, text=">", command=move_position_manual, font=('Arial', 12, 'bold'))
move_button.grid(row=4, column=1, columnspan=1, pady=0, padx=0)

add_button = tk.Button(manual_position, text="<", command=add_position_manual, font=('Arial', 12, 'bold'))
add_button.grid(row=4, column=0, columnspan=1, pady=0, padx=0)

# Text field for movement sequences
button_frame = tk.Frame(sequence_frame)
button_frame.grid(row=0, column=0, padx=0, pady=0, sticky="w")

loop_var = tk.BooleanVar()
loop_checkbox = tk.Checkbutton(button_frame, text="Loop", variable=loop_var)
loop_checkbox.grid(row=0, column=1, pady=5, sticky="nw")

run_button = tk.Button(button_frame, text="START G-Code", command=lambda: toggle_gcode_execution(loop_var), bg="lightgrey", font=('Arial', 8, 'bold'))
run_button.grid(row=0, column=0, padx=10, pady=1, sticky="ne")
run_button.grid(row=0, column=0, padx=10, pady=1, sticky="new")
run_button['state'] = tk.DISABLED  # Initially disabled

reverse_button = tk.Button(button_frame, text="Reverse", command=reverse_positions, width=10)
reverse_button.grid(row=0, column=1, padx=20, pady=1, sticky="n")

position_listbox = tk.Listbox(button_frame, height=7, width=50)
position_listbox.grid(row=1, column=0, columnspan=2, padx=10, pady=1, sticky="w")

scrollbar_position = tk.Scrollbar(button_frame, command=position_listbox.yview)
scrollbar_position.grid(row=1, column=2, pady=1, padx=(0, 10), sticky='nsew')
position_listbox['yscrollcommand'] = scrollbar_position.set

position_listbox.bind('<Double-1>', lambda event: moveto_position_fast())
position_listbox.bind('<Delete>', lambda event: delete_position_fast())
#position_listbox.bind('<FocusOut>', clear_selection_listbox)

# Start Code checkbox
start_code_var = tk.BooleanVar()
start_code_checkbox = tk.Checkbutton(connection_frame, text="Start Code", variable=start_code_var)
start_code_checkbox.grid(row=0, column=5, sticky='n', padx=1, pady=1)

# Edit Start Code button
start_code_edit_button = tk.Button(connection_frame, text="Edit", command=edit_file, width=7)
start_code_edit_button.grid(row=0, column=5, sticky='s', padx=10, pady=1)

info_frame = ttk.LabelFrame(root, text="", padding=(30, 15))
info_frame.grid(row=2, column=1, pady=1, padx=5, sticky='wn')

# Add Position button
add_position_button = tk.Button(sequence_frame_buttons, text="< ADD POS", command=add_position, width=10)
add_position_button.grid(row=0, column=2, padx=1, pady=1)

set_position_button = tk.Button(sequence_frame_buttons, text="MOVE >", command=moveto_position, width=10)
set_position_button.grid(row=1, column=2, padx=1, pady=1)
set_position_button['state'] = tk.DISABLED  # Initially disabled

# SAVE button
save_button = tk.Button(sequence_frame_buttons, text="SAVE", command=save_position, width=10)
save_button.grid(row=2, column=2, padx=1, pady=1)
save_button['state'] = tk.DISABLED  # Initially disabled

# LOAD button
load_button = tk.Button(sequence_frame_buttons, text="LOAD", command=load_position, width=10)
load_button.grid(row=3, column=2, padx=1, pady=1)

# REMOVE button
delete_button = tk.Button(sequence_frame_buttons, text="REMOVE", command=delete_position, width=10)
delete_button.grid(row=4, column=2, padx=1, pady=1)
delete_button['state'] = tk.DISABLED  # Initially disabled

# Assign functions to the selection change event
run_button.bind('<Button-1>', update_buttons_state())
save_button.bind('<Button-1>', update_buttons_state())
delete_button.bind('<Button-1>', update_buttons_state())
set_position_button.bind('<Button-1>', update_buttons_state())
#position_listbox.bind('<<ListboxList>>', lambda event: update_buttons_state())
position_listbox.bind('<<ListboxSelect>>', lambda event: update_buttons_state())

# Labels for machine status
x_label = tk.Label(info_frame, text="X: 0.00", font=('Arial', 12, 'bold'))
x_label.grid(row=3, column=0, pady=10, padx=5, sticky='w')

y_label = tk.Label(info_frame, text="Y: 0.00", font=('Arial', 12, 'bold'))
y_label.grid(row=3, column=1, pady=10, padx=5, sticky='w')

z_label = tk.Label(info_frame, text="Z: 0.00", font=('Arial', 12, 'bold'))
z_label.grid(row=3, column=2, pady=10, padx=5, sticky='w')

e_label = tk.Label(info_frame, text="E: 0.00", font=('Arial', 12, 'bold'))
e_label.grid(row=3, column=3, pady=10, padx=5, sticky='w')

# Labels for rotation, low, and high arm angles
rot_label = tk.Label(info_frame, text="Rot: 0.00", font=('Arial', 12, 'bold'))
rot_label.grid(row=4, column=0, pady=10, padx=5, sticky='w')

low_label = tk.Label(info_frame, text="Low: 0.00", font=('Arial', 12, 'bold'))
low_label.grid(row=4, column=1, pady=10, padx=5, sticky='w')

high_label = tk.Label(info_frame, text="High: 0.00", font=('Arial', 12, 'bold'))
high_label.grid(row=4, column=2, pady=10, padx=5, sticky='w')

a_label = tk.Label(info_frame, text="A: 0.00", font=('Arial', 12, 'bold'))
a_label.grid(row=5, column=0, pady=10, padx=3, sticky='w')

b_label = tk.Label(info_frame, text="B: 0.00", font=('Arial', 12, 'bold'))
b_label.grid(row=5, column=1, pady=10, padx=3, sticky='w')

c_label = tk.Label(info_frame, text="C: 0.00", font=('Arial', 12, 'bold'))
c_label.grid(row=5, column=2, pady=10, padx=3, sticky='w')

# Set colors for each axis
x_label.config(fg="red")
y_label.config(fg="blue")
z_label.config(fg="green")
e_label.config(fg="purple")
rot_label.config(fg="brown")
low_label.config(fg="brown")
high_label.config(fg="brown")
a_label.config(fg="darkgray")
b_label.config(fg="darkgray")
c_label.config(fg="darkgray")

# Entry field for entering commands
command_entry = tk.Entry(communication_frame, width=40)
command_entry.grid(row=0, column=0, columnspan=3, pady=10, padx=10, sticky='w')
command_entry.bind("<Return>", send_command_entry)
command_entry.bind("<Shift-Return>", send_command_to_seq_entry)
command_entry.bind("<Up>", lambda event: update_entry_from_history(history_instance.get_previous_command()))
command_entry.bind("<Down>", lambda event: update_entry_from_history(history_instance.get_next_command()))

# Button for sending commands
send_button = tk.Button(communication_frame, text="Send Command", command=send_command_entry)
send_button.grid(row=0, column=5, pady=10, padx=10, sticky='e')
send_button['state'] = 'disabled'

stop_button = tk.Button(communication_frame, text="STOP", command=lambda: send_command_text("M112", True), width=8, bg="red", fg="white")
stop_button.grid(row=0, column=6, padx=5, pady=0, sticky='w')
add_tooltip(stop_button, "Emergency Stop")

# Information feedback window
info_text = tk.Text(communication_frame, wrap="word", height=20, width=58)
info_text.grid(row=1, column=0, columnspan=6, pady=10, padx=10, sticky='w')
info_text['state'] = 'disabled'

# Styling configuration for coloring and boldening
info_text.tag_configure('bold_green', foreground='green', font=('Arial', 10, 'bold'))
info_text.tag_configure('bold_red', foreground='red', font=('Arial', 10, 'bold'))

scrollbar_info = tk.Scrollbar(communication_frame, command=info_text.yview)
scrollbar_info.grid(row=1, column=5, pady=1, padx=(0, 0), sticky='nse')
info_text['yscrollcommand'] = scrollbar_info.set

# Connection status label
status_label = tk.Label(root, text="Not connected", fg="black")
status_label.grid(row=0, column=0, pady=0, sticky='n')

# Additional grouped windows
control_frame = ttk.LabelFrame(root, text="Control")
control_frame.grid(row=0, column=1, rowspan=2, pady=10, padx=0, sticky='nsew')

control_frame_set = ttk.LabelFrame(root, text="Control Settings")
control_frame_set.grid(row=0, column=1, rowspan=2, pady=20, padx=5, sticky='ws')

gripper_frame = ttk.LabelFrame(root, text="Tool")
gripper_frame.grid(row=0, column=1, rowspan=2, pady=10, padx=1, sticky='se')

gripper_frame_buttons = ttk.LabelFrame(gripper_frame)
gripper_frame_buttons.grid(row=6, column=0, rowspan=2, pady=0, padx=1, sticky='se')

gripper_frame_set = ttk.LabelFrame(gripper_frame, text="")
gripper_frame_set.grid(row=6, column=5, rowspan=2, pady=1, padx=1, sticky='se')

# Create a bold font object
bold_font = font.Font(weight='bold')

# Machine movement control buttons
x_plus_button = tk.Button(control_frame, text="X+", command=lambda: move_machine("X+", float(distance_entry.get()), float(speed_entry.get())), fg="red", font=bold_font)
x_minus_button = tk.Button(control_frame, text="X-", command=lambda: move_machine("X-", float(distance_entry.get()), float(speed_entry.get())), fg="red", font=bold_font)
y_plus_button = tk.Button(control_frame, text="Y+", command=lambda: move_machine("Y+", float(distance_entry.get()), float(speed_entry.get())), fg="blue", font=bold_font, width=1, height=1)
y_minus_button = tk.Button(control_frame, text="Y-", command=lambda: move_machine("Y-", float(distance_entry.get()), float(speed_entry.get())), fg="blue", font=bold_font, width=1, height=1)
z_plus_button = tk.Button(control_frame, text="Z+", command=lambda: move_machine("Z+", float(distance_entry.get()), float(speed_entry.get())), fg="green", font=bold_font, width=1, height=1)
z_minus_button = tk.Button(control_frame, text="Z-", command=lambda: move_machine("Z-", float(distance_entry.get()), float(speed_entry.get())), fg="green", font=bold_font, width=1, height=1)

e0_plus_button = tk.Button(gripper_frame_buttons, text="E+", command=lambda: move_machine_e("E+", float(gripper_dist_entry.get()), float(gripper_speed_entry.get())), fg="purple", font=bold_font, width=5, height=1)
e0_minus_button = tk.Button(gripper_frame_buttons, text="E-", command=lambda: move_machine_e("E-", float(gripper_dist_entry.get()), float(gripper_speed_entry.get())), fg="purple", font=bold_font, width=5, height=1)

h0_button_on = tk.Button(gripper_frame_buttons, text="H0 On", fg="green", command=lambda: mosfet_control("h0", 1), font=bold_font, width=5, height=1)
h0_button_off = tk.Button(gripper_frame_buttons, text="H0 Off", fg="red", command=lambda: mosfet_control("h0", 0), font=bold_font, width=5, height=1)

h1_button_on = tk.Button(gripper_frame_buttons, text="H1 On", fg="green", command=lambda: mosfet_control("h1", 1), font=bold_font, width=5, height=1)
h1_button_off = tk.Button(gripper_frame_buttons, text="H1 Off", fg="red", command=lambda: mosfet_control("h1", 0), font=bold_font, width=5, height=1)

hb_button_on = tk.Button(gripper_frame_buttons, text="HB On", fg="green", command=lambda: mosfet_control("hb", 1), font=bold_font, width=5, height=1)
hb_button_off = tk.Button(gripper_frame_buttons, text="HB Off", fg="red", command=lambda: mosfet_control("hb", 0), font=bold_font, width=5, height=1)

# Precision movement buttons
precision_x_plus_button = tk.Button(control_frame, text="+", command=lambda: move_machine("X+", float(precision_entry.get()), float(speed_entry.get())), bg="lightgray", fg="red", font=bold_font)
precision_x_minus_button = tk.Button(control_frame, text="-", command=lambda: move_machine("X-", float(precision_entry.get()), float(speed_entry.get())), bg="lightgray", fg="red", font=bold_font)
precision_y_plus_button = tk.Button(control_frame, text="+", command=lambda: move_machine("Y+", float(precision_entry.get()), float(speed_entry.get())), bg="lightgray", fg="blue", font=bold_font)
precision_y_minus_button = tk.Button(control_frame, text="-", command=lambda: move_machine("Y-", float(precision_entry.get()), float(speed_entry.get())), bg="lightgray", fg="blue", font=bold_font)
precision_z_plus_button = tk.Button(control_frame, text="+", command=lambda: move_machine("Z+", float(precision_entry.get()), float(speed_entry.get())), bg="lightgray", fg="green", font=bold_font)
precision_z_minus_button = tk.Button(control_frame, text="-", command=lambda: move_machine("Z-", float(precision_entry.get()), float(speed_entry.get())), bg="lightgray", fg="green", font=bold_font)

manual_control_button = tk.Button(control_frame, text="M", command=toggle_manual_control, font=bold_font)

# Distance entry for machine movement
distance_entry_label = tk.Label(control_frame_set, text="Distance:")
distance_entry_label.grid(row=7, column=1, pady=1, padx=1, sticky='w')
distance_entry = tk.Entry(control_frame_set, width=8)
distance_entry.grid(row=7, column=2, pady=10, padx=5, sticky='w')
distance_entry.insert(0, "10")  # Default distance

# Precision movement distance entry
precision_entry_label = tk.Label(control_frame_set, text="Adjustment:")
precision_entry_label.grid(row=8, column=1, pady=1, padx=1, sticky='w')
precision_entry = tk.Entry(control_frame_set, width=8)
precision_entry.grid(row=8, column=2, pady=10, padx=5, sticky='w')
precision_entry.insert(0, "1")  # Default precision distance

# Speed entry for machine movement
speed_entry_label = tk.Label(control_frame_set, text="Speed:")
speed_entry_label.grid(row=9, column=1, pady=1, padx=1, sticky='w')
speed_entry = tk.Entry(control_frame_set, width=8)
speed_entry.grid(row=9, column=2, pady=10, padx=5, sticky='w')
speed_entry.insert(0, "800")  # Default speed

# Distance entry for gripper movement
gripper_dist_entry_label = tk.Label(gripper_frame_set, text="Distance:")
gripper_dist_entry_label.grid(row=7, column=5, pady=1, padx=1, sticky='w')
gripper_dist_entry = tk.Entry(gripper_frame_set, width=10)
gripper_dist_entry.grid(row=8, column=5, pady=1, padx=1, sticky='w')
gripper_dist_entry.insert(0, "15")  # Default distance for gripper movement

# Speed entry for gripper movement
gripper_speed_entry_label = tk.Label(gripper_frame_set, text="Speed:")
gripper_speed_entry_label.grid(row=9, column=5, pady=1, padx=1, sticky='w')
gripper_speed_entry = tk.Entry(gripper_frame_set, width=10)
gripper_speed_entry.grid(row=10, column=5, pady=10, padx=1, sticky='w')
gripper_speed_entry.insert(0, "300")  # Default speed for gripper movement

# Event bindings for saving configuration on focus out
speed_entry.bind("<FocusOut>", lambda event: write_config())
distance_entry.bind("<FocusOut>", lambda event: write_config())
precision_entry.bind("<FocusOut>", lambda event: write_config())
gripper_speed_entry.bind("<FocusOut>", lambda event: write_config())
gripper_dist_entry.bind("<FocusOut>", lambda event: write_config())

# Additional frame for grouping motor and fan buttons
cmd_frame = ttk.LabelFrame(communication_frame, text="Command")
cmd_frame.grid(row=1, column=6, columnspan=4, pady=0, padx=5, sticky='n')

# Motor and fan control buttons
motor_on_button = tk.Button(cmd_frame, text="Motor On", command=lambda: send_command_text("M17", True), width=8)
motor_on_button.grid(row=0, column=0, padx=5, pady=3, sticky='w')

motor_off_button = tk.Button(cmd_frame, text="Motor Off", command=lambda: send_command_text("M18", True), width=8)
motor_off_button.grid(row=1, column=0, padx=5, pady=3, sticky='w')

fan_on_button = tk.Button(cmd_frame, text="Fan On", command=lambda: send_command_text("M106", True), width=8)
fan_on_button.grid(row=2, column=0, padx=5, pady=3, sticky='w')

fan_off_button = tk.Button(cmd_frame, text="Fan Off", command=lambda: send_command_text("M107", True), width=8)
fan_off_button.grid(row=3, column=0, padx=5, pady=3, sticky='w')

# Tooltip buttons
m503_button = tk.Button(cmd_frame, text="M503", command=lambda: send_command_text("M503", True), width=8)
m503_button.grid(row=4, column=0, padx=5, pady=3, sticky='w')
add_tooltip(m503_button, "Report Settings (M503)")

m114_button = tk.Button(cmd_frame, text="M114", command=lambda: send_command_text("M114", True), width=8)
m114_button.grid(row=5, column=0, padx=5, pady=3, sticky='w')
add_tooltip(m114_button, "Get Machine Position (M114)")

g92_button = tk.Button(cmd_frame, text="G92", command=lambda: send_command_text("G92", True), width=8)
g92_button.grid(row=6, column=0, padx=5, pady=3, sticky='w')
add_tooltip(g92_button, "Check Position With Angles (G92)")

g90_button = tk.Button(cmd_frame, text="G90", command=lambda: send_command_text("G90", True), width=8)
g90_button.grid(row=7, column=0, padx=5, pady=3, sticky='w')
add_tooltip(g90_button, "Set to Absolute Position (G90)")

g91_button = tk.Button(cmd_frame, text="G91", command=lambda: send_command_text("G91", True), width=8)
g91_button.grid(row=8, column=0, padx=5, pady=3, sticky='w')
add_tooltip(g91_button, "Set to Relative Position (G91)")

# Precision movement buttons layout
precision_y_plus_button.grid(row=0, column=2, padx=1, pady=2, ipadx=20, ipady=2)
precision_y_minus_button.grid(row=5, column=2, padx=1, pady=2, ipadx=22, ipady=2)
precision_x_plus_button.grid(row=2, column=4, padx=1, pady=1, ipadx=4, ipady=18)
precision_x_minus_button.grid(row=2, column=0, padx=1, pady=1, ipadx=4, ipady=18)
precision_z_plus_button.grid(row=0, column=5, padx=1, pady=1, ipadx=20, ipady=2)
precision_z_minus_button.grid(row=5, column=5, padx=1, pady=1, ipadx=22, ipady=2)

buttons = [
    (e0_plus_button, 6, 4), (e0_minus_button, 6, 3),
    (h0_button_on, 7, 4), (h0_button_off, 7, 3),
    (h1_button_on, 8, 4), (h1_button_off, 8, 3),
    (hb_button_on, 9, 4), (hb_button_off, 9, 3)
]
for button, row, column in buttons:
    button.grid(row=row, column=column, padx=0, pady=0, ipadx=0, ipady=0, sticky='s')

manual_control_button.grid(row=2, column=2, ipadx=15, ipady=15)

# Layout for machine movement buttons
y_plus_button.grid(row=1, column=2, padx=1, pady=1, ipadx=20, ipady=18)
y_minus_button.grid(row=4, column=2, padx=1, pady=1, ipadx=20, ipady=18)
x_plus_button.grid(row=2, column=3, padx=1, pady=1, ipadx=20, ipady=18)
x_minus_button.grid(row=2, column=1, padx=1, pady=1, ipadx=20, ipady=18)
z_plus_button.grid(row=1, column=5, padx=1, pady=1, ipadx=20, ipady=18)
z_minus_button.grid(row=4, column=5, padx=1, pady=1, ipadx=20, ipady=18)

version_label = tk.Label(root, text=f"Version: {version} @Tintai")
version_label.grid(row=2, column=1, ipadx=50, ipady=0, sticky='se')

# Call the function to scan ports at program start
config_data = read_config()
if config_data:
    port_combobox.set(config_data.get("selected_port", ""))
    baud_rate_combobox.set(config_data.get("baud_rate", ""))
    auto_connect_var.set(config_data.get("auto_connect", False))
    start_code_var.set(config_data.get("start_code", False))

    # Set values for Entry fields after reading the configuration
    speed_entry.delete(0, tk.END)
    speed_entry.insert(0, config_data.get("speed", "800"))

    distance_entry.delete(0, tk.END)
    distance_entry.insert(0, config_data.get("distance", "10"))

    precision_entry.delete(0, tk.END)
    precision_entry.insert(0, config_data.get("adjustment", "1"))

    gripper_speed_entry.delete(0, tk.END)
    gripper_speed_entry.insert(0, config_data.get("gripper_speed", "300"))

    gripper_dist_entry.delete(0, tk.END)
    gripper_dist_entry.insert(0, config_data.get("gripper_dist", "15"))

kinematics_type_update()
apply_settings_from_config()

# Start the main event loop
scan_ports()  # Added port scanning before the main loop
if auto_connect_var.get():
    auto_connect_handler()  # Call the auto-connect function if the Auto Connect option is checked
root.after(100, read_from_port)
root.mainloop()
