class CommandHistory:
    history = []
    current_index = -1
        
    def __init__(self):
        self.history = []
        self.current_index = -1

    def add_command(self, command):
        self.history.append(command)
        self.current_index = len(self.history) - 1

    def get_previous_command(self):
        if self.current_index >= 0:
            command = self.history[self.current_index]
            self.current_index -= 1
            return command
        else:
            return ""

    def get_next_command(self):
        if self.current_index < len(self.history) - 1:
            self.current_index += 1
            return self.history[self.current_index]
        else:
            return ""