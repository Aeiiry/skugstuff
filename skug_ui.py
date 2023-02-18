"""UI???"""

# main function
import logging

import os
import tkinter as tk
import pyglet

# initialise logging
logging.basicConfig(level=logging.DEBUG)


def main() -> None:
    """Main function"""

    # create the window
    window: tk.Tk = tk.Tk()
    window.title("SKUG")
    window.geometry("800x600")
    window.configure(bg="white")

    # create the canvas
    canvas: tk.Canvas = tk.Canvas(window, width=800, height=600, bg="white")
    canvas.pack()

    # import the font from data\fonts\setznick-nf\SelznickRemixNF.ttf  using pyglet
    pyglet.font.add_file(  # type: ignore
        os.path.join("data", "fonts", "setznick-nf", "SelznickRemixNF.ttf")
    )
    pyglet.font.load("Selznick Remix NF")  # type: ignore
    skug_font: str = "Selznick Remix NF"

    # create the label
    label: tk.Label = tk.Label(window, text="SKUG", font=(skug_font, 25))
    label.place(x=400, y=300, anchor="center")

    # run the main loop
    window.mainloop()


if __name__ == "__main__":
    main()
