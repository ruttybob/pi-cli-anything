#!/usr/bin/env python3
"""Simple Calculator GUI Application using tkinter.

This is a basic calculator with:
- Standard arithmetic operations (+, -, *, /)
- Memory functions (M+, M-, MR, MC)
- History of calculations
- Percentage and square root
- Clear and backspace

The core calculation engine is in calculator_engine.py.
"""

import tkinter as tk
from tkinter import messagebox
from calculator_engine import CalculatorEngine


class CalculatorGUI:
    """A simple calculator GUI built with tkinter."""

    def __init__(self, root):
        self.root = root
        self.root.title("Simple Calculator")
        self.root.geometry("320x480")
        self.root.resizable(False, False)
        self.root.configure(bg="#2b2b2b")

        self.engine = CalculatorEngine()

        self._build_display()
        self._build_buttons()
        self._bind_keys()

    def _build_display(self):
        """Build the display area."""
        display_frame = tk.Frame(self.root, bg="#2b2b2b", pady=10, padx=10)
        display_frame.pack(fill=tk.X)

        # Expression display (smaller, shows the expression)
        self.expr_var = tk.StringVar(value="")
        expr_label = tk.Label(
            display_frame,
            textvariable=self.expr_var,
            font=("Courier", 12),
            bg="#2b2b2b",
            fg="#888888",
            anchor="e",
        )
        expr_label.pack(fill=tk.X)

        # Main display
        self.display_var = tk.StringVar(value="0")
        display_label = tk.Label(
            display_frame,
            textvariable=self.display_var,
            font=("Courier", 28, "bold"),
            bg="#2b2b2b",
            fg="#ffffff",
            anchor="e",
        )
        display_label.pack(fill=tk.X)

        # Memory indicator
        self.mem_var = tk.StringVar(value="")
        mem_label = tk.Label(
            display_frame,
            textvariable=self.mem_var,
            font=("Courier", 10),
            bg="#2b2b2b",
            fg="#4fc3f7",
            anchor="w",
        )
        mem_label.pack(fill=tk.X)

    def _build_buttons(self):
        """Build the button grid."""
        btn_frame = tk.Frame(self.root, bg="#2b2b2b", padx=5, pady=5)
        btn_frame.pack(fill=tk.BOTH, expand=True)

        # Button layout
        buttons = [
            [("MC", "#555"), ("MR", "#555"), ("M+", "#555"), ("M-", "#555")],
            [("C", "#d32f2f"), ("CE", "#d32f2f"), ("<-", "#555"), ("/", "#ff9800")],
            [("7", "#424242"), ("8", "#424242"), ("9", "#424242"), ("*", "#ff9800")],
            [("4", "#424242"), ("5", "#424242"), ("6", "#424242"), ("-", "#ff9800")],
            [("1", "#424242"), ("2", "#424242"), ("3", "#424242"), ("+", "#ff9800")],
            [("%", "#555"), ("0", "#424242"), (".", "#424242"), ("=", "#4caf50")],
        ]

        for r, row in enumerate(buttons):
            btn_frame.grid_rowconfigure(r, weight=1)
            for c, (text, color) in enumerate(row):
                btn_frame.grid_columnconfigure(c, weight=1)
                btn = tk.Button(
                    btn_frame,
                    text=text,
                    font=("Courier", 16, "bold"),
                    bg=color,
                    fg="white",
                    activebackground="#666",
                    activeforeground="white",
                    relief=tk.FLAT,
                    bd=0,
                    command=lambda t=text: self._on_button(t),
                )
                btn.grid(row=r, column=c, sticky="nsew", padx=2, pady=2)

    def _bind_keys(self):
        """Bind keyboard shortcuts."""
        self.root.bind("<Key>", self._on_key)
        self.root.bind("<Return>", lambda e: self._on_button("="))
        self.root.bind("<BackSpace>", lambda e: self._on_button("<-"))
        self.root.bind("<Escape>", lambda e: self._on_button("C"))

    def _on_key(self, event):
        """Handle keyboard input."""
        char = event.char
        if char in "0123456789.+-*/":
            self._on_button(char)
        elif char == "%":
            self._on_button("%")

    def _on_button(self, text):
        """Handle button press."""
        if text in "0123456789":
            result = self.engine.input_digit(text)
        elif text == ".":
            result = self.engine.input_decimal()
        elif text in "+-*/":
            result = self.engine.input_operator(text)
        elif text == "=":
            result = self.engine.calculate()
        elif text == "C":
            result = self.engine.clear()
        elif text == "CE":
            result = self.engine.clear_entry()
        elif text == "<-":
            result = self.engine.backspace()
        elif text == "%":
            result = self.engine.percentage()
        elif text == "MC":
            result = self.engine.memory_clear()
        elif text == "MR":
            result = self.engine.memory_recall()
        elif text == "M+":
            result = self.engine.memory_add()
        elif text == "M-":
            result = self.engine.memory_subtract()
        else:
            return

        self._update_display(result)

    def _update_display(self, result):
        """Update the display with engine state."""
        self.display_var.set(result["display"])
        self.expr_var.set(result.get("expression", ""))
        if self.engine.memory != 0:
            self.mem_var.set(f"M = {self.engine.memory}")
        else:
            self.mem_var.set("")


def main():
    root = tk.Tk()
    app = CalculatorGUI(root)
    root.mainloop()


if __name__ == "__main__":
    main()
