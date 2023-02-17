import math
import os
import random
import sys
from PyQt5 import QtGui, QtWidgets
from PyQt5.QtCore import Qt


def create_window(title) -> QtWidgets.QMainWindow:
    window: QtWidgets.QMainWindow = QtWidgets.QMainWindow()
    window.setWindowTitle(title)

    return window


# Import font from .ttf file


def import_font(font_path, size=20) -> QtGui.QFont:
    font_id: int = QtGui.QFontDatabase.addApplicationFont(font_path)
    imported_font: str = QtGui.QFontDatabase.applicationFontFamilies(font_id)[0]
    font: QtGui.QFont = QtGui.QFont(imported_font, size)
    return font


def create_icon_button(icon_path) -> QtWidgets.QPushButton:
    # create a button with an icon
    button: QtWidgets.QPushButton = QtWidgets.QPushButton()
    button.setIcon(QtGui.QIcon(icon_path))
    return button


def create_push_button(text) -> QtWidgets.QPushButton:
    # create a button with the text
    button: QtWidgets.QPushButton = QtWidgets.QPushButton(text)
    # set the font of the button to the skugfont

    return button


def create_window_layout(window: QtWidgets.QMainWindow) -> QtWidgets.QGridLayout:
    # create a grid layout
    grid: QtWidgets.QGridLayout = QtWidgets.QGridLayout()
    # set the grid layout to the window
    window.setLayout(grid)
    return grid


# function to import a stylesheet


def import_style_sheet(style_path) -> str:
    # check if the stylesheet exists
    if os.path.exists(style_path):
        # open the stylesheetQGridLayout
        with open(style_path, "r", encoding="utf_8") as file:
            # read the stylesheet
            style: str = file.read()
            # return the stylesheet
            return style
    else:
        # stylesheet does not exist, so return an empty string
        return ""


def set_random_window_icon(window: QtWidgets.QMainWindow) -> str:

    icon_list: list[str] = os.listdir("data/program_icons")

    if len(icon_list) == 0:

        window.setWindowIcon(QtGui.QIcon("data/program_icons/default.png"))
        iconstr: str = "default.png"

    else:

        iconstr = icon_list[math.floor(random.random() * len(icon_list))]

        window.setWindowIcon(QtGui.QIcon("data/program_icons/" + iconstr))
    return iconstr


# main function
def main() -> None:
    # Initialise the application
    skombo_app: QtWidgets.QApplication = QtWidgets.QApplication(sys.argv)
    # Create a new window
    main_window: QtWidgets.QMainWindow = create_window("skombo")
    # Import a custom font from the data/fonts folder
    skug_font: QtGui.QFont = import_font(
        "data/fonts/setznick-nf/SelznickRemixNF.ttf", 20
    )
    # Set a random icon for the window and store the icon name in a variable
    random_icon: str = set_random_window_icon(main_window)
    # Import a custom stylesheet from the data folder
    style: str = import_style_sheet("data/style_sheet.qss")
    # Set the stylesheet for the application
    skombo_app.setStyleSheet(style)
    # Set the font for the application
    skombo_app.setFont(skug_font)
    # Resize the window
    main_window.resize(1200, 1000)
    # Import the alignment flag from the Qt library for easier reference
    alignment_flag: Qt.AlignmentFlag = Qt.AlignmentFlag()

    # create a menu bar
    menu_bar: QtWidgets.QMenuBar = QtWidgets.QMenuBar()
    # add the menu bar to the window
    main_window.setMenuBar(menu_bar)
    # create a tool bar
    toolbar: QtWidgets.QToolBar = QtWidgets.QToolBar()
    # add the tool bar to the window
    main_window.addToolBar(toolbar)
    # create a dock widget
    dock_widget: QtWidgets.QDockWidget = QtWidgets.QDockWidget()
    # add the dock widget to the window
    main_window.addDockWidget(Qt.LeftDockWidgetArea, dock_widget)
    # create a central widget
    central_widget: QtWidgets.QWidget = QtWidgets.QWidget()
    # add the central widget to the window
    main_window.setCentralWidget(central_widget)
    # create a status bar
    status_bar: QtWidgets.QStatusBar = QtWidgets.QStatusBar()
    # add the status bar to the window
    main_window.setStatusBar(status_bar)

    main_window.show()
    sys.exit(skombo_app.exec_())


if __name__ == "__main__":
    main()
