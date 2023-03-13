"""Skug combo constants."""
from typing import Literal
import logging

# flake8: noqa: E501

# Column names
CHARACTER_NAME: Literal["Character"] = "Character"
MOVE_NAME: Literal["MoveName"] = "MoveName"
ALT_NAMES: Literal["AltNames"] = "AltNames"
DAMAGE: Literal["Damage"] = "Damage"

EXPECTED_DAMAGE: Literal["ExpectedDamage"] = "ExpectedDamage"

# Column names for combo data
HIT_NUMBER: Literal["HitNumber"] = "HitNumber"
DAMAGE_SCALING: Literal["DamageScaling"] = "DamageScaling"
SCALED_DAMAGE: Literal["ScaledDamage"] = "ScaledDamage"
UNDIZZY: Literal["Undizzy"] = "Undizzy"
TOTAL_DAMAGE_FOR_MOVE: Literal["TotalDamageForMove"] = "TotalDamageForMove"
TOTAL_DAMAGE_FOR_COMBO: Literal["TotalDamageForCombo"] = "TotalDamageForCombo"

# Floats for combo damage calculations
DAMAGE_SCALING_MIN: float = 0.2
DAMAGE_SCALING_MIN_ABOVE_1K: float = 0.275
DAMAGE_SCALING_FACTOR: float = 0.875

# Undizzy Dictionary
# Columns: MoveType, Undizzy
# MoveType: Light, Medium, Heavy, Special, Throws+Supers
# Undizzy: 15, 30, 40, 30, 0
UNDIZZY_DICT: dict[str, int] = {
    "Light": 15,
    "Medium": 30,
    "Heavy": 40,
    "Special": 30,
    "Throws+Supers": 0,
}



# Move names to automatically ignore
IGNORED_MOVES: list[str] = [
    "adc",
    "air dash cancel",
    "air dash",
    "delay",
    "delayed",
    "delaying",
    "jc",
    "jump cancel",
    "jump",
    "otg",
    "dash",
    "66",
    "restand",
]

SEARCH_STATES: dict[str, bool] = {
    "character_specific": False,
    "repeat": False,
    "start": False,
    "follow_up": False,
    "alias": False,
    "generic": False,
    "no_strength": False,
    "not_found": False,
}

ANNIE_DIVEKICK: str = "RE ENTRY"

LOG_LEVEL_CONSOLE: int = logging.INFO
LOG_LEVEL_FILE: int = logging.DEBUG
def logger_setup() -> logging.Logger:
    """Set up the logger."""

    # Log formats
    file_format: logging.Formatter = logging.Formatter(
        "[%(relativeCreated)dms] %(filename)s:%(lineno)d:%(funcName)s | %(levelname)s | %(message)s"
    )

    console_format: logging.Formatter = logging.Formatter("%(levelname)s | %(message)s")

    # Console handler
    console_handler = logging.StreamHandler()
    console_handler.setFormatter(console_format)
    console_handler.setLevel(LOG_LEVEL_CONSOLE)

    # Verbose log handler
    verbose_log_handler: logging.FileHandler = logging.FileHandler(
        "skug_combo.log", mode="w"
    )

    verbose_log_handler.setFormatter(file_format)
    verbose_log_handler.setLevel(LOG_LEVEL_FILE)

    # Info log handler
    info_log_handler: logging.FileHandler = logging.FileHandler(
        "skug_combo_info.log", mode="w"
    )

    info_log_handler.setFormatter(file_format)
    info_log_handler.setLevel(logging.INFO)

    # Logger

    logger: logging.Logger = logging.getLogger(__name__)
    logger.setLevel(logging.DEBUG)

    logger.addHandler(console_handler)
    logger.addHandler(verbose_log_handler)
    logger.addHandler(info_log_handler)

    return logger


logger: logging.Logger = logger_setup()
