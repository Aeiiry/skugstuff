"""UI???"""

# main function
import logging
import sys
import os
import tkinter as tk
from tkinter import font
from typing import Any, Literal
import pyglet
from pyglet.font.base import Font
import fontTools.ttLib as ttLib

# initialise logging
logging.basicConfig(level=logging.DEBUG)

FONT_SPECIFIER_NAME_ID: Literal[4] = 4
FONT_SPECIFIER_FAMILY_ID: Literal[1] = 1


def create_font(path: str, font_name: str) -> Font:
    """Create the font"""

    # import the font from the given relative path str
    font_file: str = os.path.join(path, font_name)
    try:
        pyglet.font.add_file(font_file)  # type: ignore
    except OSError:
        logging.error("Font file not found")
        sys.exit(1)

    # find the font name
    font_facing_name = get_font_name(font=ttLib.TTFont(font_file))[1]

    font: Font = pyglet.font.load(font_facing_name)

    # return the font name
    return font


def get_font_name(font: ttLib.TTFont) -> tuple[str, str]:
    """Get the short name from the font's names table"""
    # Initialize variables to hold the name and family
    name: str = ""
    family: str = ""

    for record in font["name"].names:  # type: ignore
        # Decode the name string from UTF-16 or UTF-8
        if b"\x00" in record.string:
            decoded_string: bytes = record.string.decode("utf-16-be")
        else:
            decoded_string = record.string.decode("utf-8", errors="replace").encode(
                "utf-8"
            )

        # If the name record is the short name and we haven't found
        # the short name yet, set the name to the decoded string
        if record.nameID == FONT_SPECIFIER_NAME_ID and not name:
            name = decoded_string.decode("utf-8")

        # If the name record is the family and we haven't found
        # the family yet, set the family to the decoded string
        elif record.nameID == FONT_SPECIFIER_FAMILY_ID and not family:
            family = decoded_string.decode("utf-8")

        # If we have found both names, stop iterating
        if name and family:
            break

    # Return both names as a tuple
    return name, family


def create_home_canvas(window: tk.Tk) -> tk.Canvas:
    home_canvas: tk.Canvas = tk.Canvas(window, bg="white", borderwidth=2)

    # create the home screen frames
    home_info_frame: tk.Frame = tk.Frame(
        home_canvas,
        borderwidth=2,
    )
    home_buttons_frame: tk.Frame = tk.Frame(
        home_canvas,
        borderwidth=2,
    )

    # set the font of the button frame to the skug font

    # create the home screen label
    home_main_label: tk.Label = tk.Label(window, text="Select combo input type")

    # create the home screen buttons
    # set variables for the buttons

    buttons_strings: list[str] = ["Visual", "Manual", "File"]

    # create the buttons
    for button_string in buttons_strings:
        # create the button
        button: tk.Button = tk.Button(
            home_buttons_frame,
            text=button_string,
        )

        # pack the button
        button.pack(side="left", padx=5, pady=5, expand=True)

    # pack the label
    home_main_label.pack()

    # pack the frames
    home_info_frame.pack()
    home_buttons_frame.pack()

    # pack the canvas
    home_canvas.pack()

    # return the home screen canvas
    return home_canvas


def main() -> None:
    """Main function"""

    """Current plan:
    First screen:
    Select combo input type: visual, manual text input, file input

    Each combo input type has a different screen """

    # create the window
    window: tk.Tk = tk.Tk()

    # default dimensions
    # window.geometry("800x600")

    # import skug font
    skug_font = create_font(
        path="data/fonts/setznick-nf", font_name="SelznickRemixNF.ttf"
    )

    readable_font = create_font(
        path="data/fonts/AtkinsonHyperlegible/Web Fonts/TTF",
        font_name="Atkinson-Hyperlegible-Regular-102.ttf",
    )

    # set default style and size for fonts
    readable_font = (readable_font.name, 30)
    skug_font = (skug_font.name, 30)

    # add the fonts to the window
    window.option_add("*Font", skug_font)
    window.option_add("*Button.Font", readable_font)

    # create the home screen canvas
    create_home_canvas(window)

    # run the main loop
    window.mainloop()


if __name__ == "__main__":
    main()
