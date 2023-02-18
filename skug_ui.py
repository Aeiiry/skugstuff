"""UI???"""

# main function
import logging

import os
import tkinter as tk
import pyglet
from fontTools import ttLib

# initialise logging
logging.basicConfig(level=logging.DEBUG)


def main() -> None:
    """Main function"""

    window: tk.Tk = create_window()
    canvas: tk.Canvas = create_canvas(window)
    skug_font: str = create_font("data/fonts/setznick-nf", "SelznickRemixNF.ttf")
    label: tk.Label = create_label(window, skug_font, "Skug test COMBINOS bombino mama-mia", 100)

    label.place(x=100, y=100)

    # run the main loop
    window.mainloop()


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
    pyglet.font.add_file(font_file)

    # find the font name
    font_facing_name: str = get_font_name(font_file)[0]

    # return the font name
    return font_facing_name


def get_font_name(font_file) -> tuple[str, str]:
    """Get the font name"""

    font: ttLib.TTFont = ttLib.TTFont(font_file)
    font_family_name = font["name"].getDebugName(1)  # type: ignore
    font_full_name = font["name"].getDebugName(4)  # type: ignore
    return font_family_name, font_full_name


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


if __name__ == "__main__":
    main()
