#!/usr/bin/env python3
# -*- coding: utf-8 -*-

import tkinter as tk
from tkinter import messagebox, font
import subprocess
import glob
import os

# --- Configuration ---
WINDOW_TITLE = "ASUS Battery Charge Limiter"
WINDOW_WIDTH = 400
WINDOW_HEIGHT = 200
# Path to the charge control file. The wildcard '*' handles BAT0, BAT1, etc.
CHARGE_THRESHOLD_FILE_PATH = "/sys/class/power_supply/BAT*/charge_control_end_threshold"
# --- End Configuration ---

class Application(tk.Frame):
    """A simple GUI application to set the ASUS battery charge threshold."""

    def __init__(self, master=None):
        super().__init__(master)
        self.master = master
        self.battery_path = self.find_battery_path()
        self.create_widgets()
        self.load_current_threshold()

    def find_battery_path(self):
        """Finds the correct battery charge threshold file."""
        try:
            # Use glob to find the file, as it could be BAT0, BAT1, etc.
            paths = glob.glob(CHARGE_THRESHOLD_FILE_PATH)
            if not paths:
                messagebox.showerror(
                    "Error",
                    "Could not find the battery charge control file.\n"
                    f"Searched for: {CHARGE_THRESHOLD_FILE_PATH}\n\n"
                    "This script may not be compatible with your device."
                )
                self.master.quit()
                return None
            # Return the first match found
            return paths[0]
        except Exception as e:
            messagebox.showerror("Error", f"An error occurred while finding the battery path: {e}")
            self.master.quit()
            return None

    def load_current_threshold(self):
        """Reads the current threshold value and updates the UI."""
        if not self.battery_path or not os.path.exists(self.battery_path):
            self.current_value_label.config(text="Current value: Not Found")
            return

        try:
            # We don't need sudo to read the file, only to write.
            with open(self.battery_path, 'r') as f:
                current_value = f.read().strip()
                self.current_value_label.config(text=f"Current value: {current_value}%")
        except (IOError, PermissionError) as e:
            self.current_value_label.config(text="Current value: Read Error")
            print(f"Error reading threshold value: {e}")
        except Exception as e:
            self.current_value_label.config(text="Current value: Unknown Error")
            print(f"An unexpected error occurred: {e}")


    def set_new_threshold(self):
        """Sets the new battery charge threshold using pkexec."""
        new_value = self.entry.get()
        try:
            # Validate that the input is an integer between 20 and 100
            val_int = int(new_value)
            if not 20 <= val_int <= 100:
                raise ValueError
        except ValueError:
            messagebox.showwarning("Invalid Input", "Please enter a whole number between 20 and 100.")
            return

        if not self.battery_path:
            messagebox.showerror("Error", "Cannot set threshold because battery path is not defined.")
            return

        # This is the core command. We use 'pkexec' to request administrator
        # privileges for just this one command. This is more secure than
        # running the entire script with sudo.
        command = [
            "pkexec",
            "/bin/bash",
            "-c",
            f"echo {val_int} > {self.battery_path}"
        ]

        try:
            # Execute the command
            subprocess.run(command, check=True, capture_output=True, text=True)
            messagebox.showinfo("Success", f"Battery charge threshold successfully set to {val_int}%.")
            # Refresh the displayed value
            self.load_current_threshold()
        except subprocess.CalledProcessError as e:
            # This error typically occurs if the user cancels the password prompt
            # or if there's an issue with permissions/Polkit rules.
            error_message = e.stderr.strip() if e.stderr else "The command was rejected or failed."
            messagebox.showerror(
                "Execution Failed",
                f"Failed to set the new threshold.\n\n"
                f"Reason: {error_message}\n\n"
                "Please ensure you have administrative privileges and entered the correct password."
            )
        except FileNotFoundError:
             messagebox.showerror(
                "Error",
                "The 'pkexec' command was not found.\n"
                "Please ensure Polkit is installed on your system."
            )
        except Exception as e:
            messagebox.showerror("An Unexpected Error Occurred", f"Details: {e}")


    def create_widgets(self):
        """Creates and arranges the GUI elements in the window."""
        self.pack(padx=20, pady=15, fill="both", expand=True)

        # --- Current Value Display ---
        self.current_value_label = tk.Label(self, text="Current value: Loading...", font=font.Font(size=12))
        self.current_value_label.pack(pady=(0, 20))

        # --- Input Frame ---
        input_frame = tk.Frame(self)
        input_frame.pack(fill="x", pady=5)

        label = tk.Label(input_frame, text="Set Threshold (20-100):")
        label.pack(side="left", padx=(0, 10))

        self.entry = tk.Entry(input_frame, width=10)
        self.entry.pack(side="left", fill="x", expand=True)

        # --- Button ---
        self.set_button = tk.Button(self, text="Apply New Threshold", command=self.set_new_threshold)
        self.set_button.pack(pady=10, fill="x")

# --- Main execution block ---
if __name__ == "__main__":
    root = tk.Tk()
    root.title(WINDOW_TITLE)
    root.geometry(f"{WINDOW_WIDTH}x{WINDOW_HEIGHT}")
    # Center the window on the screen
    root.eval('tk::PlaceWindow . center')
    app = Application(master=root)
    app.mainloop()
