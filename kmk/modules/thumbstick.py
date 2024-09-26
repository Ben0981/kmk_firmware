from kmk.modules import Module
from analogio import AnalogIn
from digitalio import DigitalInOut, Direction, Pull
import math


class Thumbstick(Module):
    def __init__(
        self,
        x_pin,
        y_pin,
        button_pin,
        directional_inputs,
        button_input,
        center_threshold=10000,
        angle_threshold=3,
    ):
        if len(directional_inputs) == 0:
            raise ValueError('At least one input must be provided')
        self.x_axis = AnalogIn(x_pin)
        self.y_axis = AnalogIn(y_pin)

        self.use_button = button_input != None and button_pin != None

        if self.use_button:
            self.button = DigitalInOut(button_pin)
            self.button.direction = Direction.INPUT
            self.button.pull = Pull.UP

        self.prev_press = None
        self.center_threshold = center_threshold  # Threshold for the center deadzone
        self.angle_threshold = (
            angle_threshold  # Threshold to remove jitter on the border between inputs
        )
        self.num_directions = len(directional_inputs)  # Number of directions

        self.current_direction = 0

        self.inputs = [button_input] + directional_inputs[: self.num_directions]

    def during_bootup(self, keyboard):
        pass

    def before_matrix_scan(self, keyboard):
        pass

    def before_hid_send(self, keyboard):
        pass

    def after_hid_send(self, keyboard):
        pass

    def on_powersave_enable(self, keyboard):
        pass

    def on_powersave_disable(self, keyboard):
        pass

    def after_matrix_scan(self, keyboard):
        self.process(keyboard)

    def get_direction(self, x, y):
        # Normalize the input values to center at 0
        x_normalized = x - 32768
        y_normalized = y - 32768

        # Check if the thumbstick is within the center threshold (deadzone)
        if (
            abs(x_normalized) < self.center_threshold
            and abs(y_normalized) < self.center_threshold
        ):
            return 0

        # Calculate the angle in degrees
        angle = math.atan2(y_normalized, x_normalized) * 180.0 / math.pi
        if angle < 0:
            angle += 360

        # Size of each section
        section_size = 360 / self.num_directions

        # Shift the angle so that 0 degrees is the center of the first section
        shifted_angle = (angle + section_size / 2) % 360

        # Find the section number
        direction = int(shifted_angle // section_size) + 1

        # Check if a neighbouring section was entered (by rotating the thumbstick)
        if self.current_direction != 0 and abs(direction - self.current_direction) == 1:
            # Check if new angle is within a smaller section of the entered section to prevent jitter at the section borders
            min_angle = ((direction - 1) * section_size) + self.angle_threshold
            max_angle = (
                ((direction - 1) * section_size) + section_size - self.angle_threshold
            )
            # The new angle is too close at the border which could cause jitter due to noise
            if not (shifted_angle > min_angle and shifted_angle < max_angle):
                direction = self.current_direction

        return direction

    def process(self, keyboard):
        x = self.x_axis.value
        y = self.y_axis.value

        direction = self.get_direction(x, y)
        key_to_press = self.inputs[direction]

        self.current_direction = direction

        # Handle key press/release for direction
        if key_to_press != self.prev_press:
            if self.prev_press:
                keyboard.process_key(self.prev_press, False)

        if direction != 0:
            keyboard.process_key(key_to_press, True)

            self.prev_press = key_to_press

        # Handle button press if configured
        if self.use_button:
            pressed = not self.button.value  # Button is active-low
            if pressed:
                keyboard.process_key(self.inputs[0], True)
            else:
                keyboard.process_key(self.inputs[0], False)

        return keyboard
