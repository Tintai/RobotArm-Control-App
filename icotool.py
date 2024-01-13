icon_path = "icon.png"

with open(icon_path, "rb") as f:
    icon_data = f.read()

with open("icon_binary.py", "wb") as f:
    f.write(b'icon_data = ' + repr(icon_data).encode())