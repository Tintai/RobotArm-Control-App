# RobotArm Control

## Overview

RobotArm Control is a user-friendly graphical interface for controlling TPARA/SCARA robots using Marlin firmware. This application simplifies the process of managing and commanding your robot, providing an intuitive interface for users at all skill levels.

---

<p align="center">
  <img src="/icon.png?raw=true" width="300" height="300">
</p>

---

## Features

- **User-Friendly Interface:** The graphical user interface is designed for simplicity, making it easy for both beginners and experienced users to control their TPARA/SCARA robots.

- **Real-Time Monitoring:** Monitor real-time robot status, including position, speed, and other relevant parameters.

- **Intuitive Control:** Easily command the robot's movement using the keyboard or by specifying specific coordinates.

- **Configurable Settings:** Adjust various settings such as speed, acceleration, and step size to customize the robot's behavior according to your needs.

## Getting Started

1. **Prerequisites:**
   - Ensure that your TPARA/SCARA robot is equipped with Marlin firmware.
   - [Marlin-2.0.9.7-TPARA](https://github.com/Tintai/Marlin-2.0.9.7-TPARA), [Marlin-2.0.7.2-ROBOT_ARM_2L](https://github.com/Tintai/Marlin-2.0.7.2-ROBOT_ARM_2L), [2L-Robot-Arm-Marlin](https://github.com/LeandroLoiacono/2L-Robot-Arm-Marlin)

2. **Download and Install:**
   - Clone this repository to your local machine.
   - Build using: `pyinstaller --onefile --noconsole --icon=icon.ico robotarm_main.py`
   - Or download latest [Release](https://github.com/Tintai/RobotArm-Control-App/releases)
     
## Hardware & Wirning
  - Creality v2.2 Silent Board (RAMPS 1.4 with MEGA2560) or any other controller
  - `X` - rotation, `Y` - lower shank, `Z` - higher shank, `E1` - gripper
  - Addnotional On/Off devices like electromagnet tool or LED connect to **HE0**, **HE1** or **HB**

## Commands & Info
There are special commands available for use in the command input field.

- `/clean` or `/clear` - Clears the log text
- `/set` or `/settings` - Opens the settings menu
  
</br>

- `M104 S100` & `M104 S0` - On/Off HE0, like heater
- `M171 P1` & `M171 P0` - On/Off HE1
- `M170 P1` & `M170 P0` - On/Off HB

</br>

- `Shift + Enter` - Sends command to G-Code list
</br>
  
To activate manual control mode, press the "M" button at the center.</br>

- Use arrows to control X and Y. Ctrl+Arrows control Z and E
  
---

## Screenshots
<details>
  
![Screenshot 1](/dist/screen1.png?raw=true)
![Screenshot 2](/dist/screen2.png?raw=true)
  
</details>

## Contributing

If you find any issues or have suggestions for improvement, please feel free to open an issue or submit a pull request. Contributions are welcome!

## License

This project is licensed under the [MIT License](LICENSE).

---
