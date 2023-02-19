"""UI???"""

# main function
import logging
import sys
import os
import tkinter as tk
from typing import Literal
import pyglet
from fontTools import ttLib

# initialise logging
logging.basicConfig(level=logging.DEBUG)

FONT_SPECIFIER_NAME_ID: Literal[4] = 4
FONT_SPECIFIER_FAMILY_ID: Literal[1] = 1


def create_window() -> tk.Tk:
    """Create the window"""

    # create the window
    window: tk.Tk = tk.Tk()
    window.title("SKUG")
    window.geometry("800x600")
    window.configure(bg="white")

    # return the window
    return window


def create_canvas(window: tk.Tk) -> tk.Canvas:
    """Create the canvas"""

    # create the canvas
    canvas: tk.Canvas = tk.Canvas(window, width=800, height=600, bg="white")
    canvas.pack()

    # return the canvas
    return canvas


def create_font(path: str, font_name: str) -> str:
    """Create the font"""

    # import the font from the given relative path str
    font_file: str = os.path.join(path, font_name)
    try:
        pyglet.font.add_file(font_file)  # type: ignore
    except OSError:
        logging.error("Font file not found")
        sys.exit(1)

    # find the font name
    font_facing_name: str = get_font_name(font=ttLib.TTFont(font_file))[0]

    # return the font name
    return font_facing_name


def get_font_name(font: ttLib.TTFont) -> tuple[str, str]:
    """Get the short name from the font's names table"""
    # Initialize variables to hold the name and family
    name: str = ""
    family: str = ""
    # Iterate over the font's name records
    for record in font["name"].names:  # type: ignore
        # Decode the name string from UTF-16 or UTF-8
        if b"\x00" in record.string:
            decoded_string: str = record.string.decode("utf-16-be")
        else:
            decoded_string = record.string.decode("utf-8")

        # If the name record is the short name and we haven't found
        # the short name yet, set the name to the decoded string
        if record.nameID == FONT_SPECIFIER_NAME_ID and not name:
            name = decoded_string

        # If the name record is the family and we haven't found
        # the family yet, set the family to the decoded string
        elif record.nameID == FONT_SPECIFIER_FAMILY_ID and not family:
            family = decoded_string

        # If we have found both names, stop iterating
        if name and family:
            break

    # Return both names as a tuple
    return name, family


def create_label(window: tk.Tk, skug_font: str, text: str, font_size: int) -> tk.Label:
    """Create the label"""

    # create the label
    label: tk.Label = tk.Label(
        window,
        text=text,
        font=(skug_font, font_size),
        bg="white",
        fg="black",
    )

    # return the label
    return label


def main() -> None:
    """Main function"""

    window: tk.Tk = create_window()
    canvas: tk.Canvas = create_canvas(window)
    skug_font: str = create_font("data/fonts/setznick-nf", "SelznickRemixNF.ttf")
    label: tk.Label = create_label(
        window, skug_font, "Skug test COMBINOS bombino mama-mia", 100
    )

    label.place(x=100, y=100)

    # run the main loop
    window.mainloop()


if __name__ == "__main__":
    main()
