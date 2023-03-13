# %%
"""
Calculate the damage of a combo.
"""
from __future__ import annotations

import os
import math
from typing import Any

import pandas as pd
import numpy as np  # type: ignore
import matplotlib as mpl  # type: ignore
import matplotlib.pyplot as plt  # type: ignore
from pandas import DataFrame, Series

import parseCombo
import constants as const
from constants import logger

# flake8: noqa: E501
# pylance: reportUnknownMemberType=false

# attempt to get the data directory it is in the parent directory
try:
    data_dir: str = os.path.join(os.path.dirname(__file__), "..", "data")
except NameError:
    data_dir: str = os.path.join(os.getcwd(), "..", "data")

move_name_alias_df: DataFrame = pd.read_csv(f"{data_dir}\\moveNameAliases.csv")
full_framedata_df: DataFrame = pd.read_csv(f"{data_dir}\\fullFrameData.csv")


# %%
def remove_whitespace_from_column_names(df: DataFrame) -> DataFrame:
    """Remove whitespace from column names in a dataframe."""
    df.columns = df.columns.str.replace(" ", "")
    return df


def get_damage_scaling_for_hit(hit_num: int, damage: int) -> float:  # type: ignore
    """Get the damage scaling for a hit."""

    damage: int = int(damage)

    # check if the damage is 0 -0 or none
    if damage in [0, -1]:
        # return the damage scaling for the hit before
        return max(
            const.DAMAGE_SCALING_MIN, const.DAMAGE_SCALING_FACTOR ** (hit_num - 4)
        )

    if hit_num <= 3:
        return 1
    # check if the damage is greater than 1000
    if damage >= 1000:
        scaling: float = max(
            const.DAMAGE_SCALING_MIN_ABOVE_1K,
            const.DAMAGE_SCALING_FACTOR ** (hit_num - 3),
        )
    else:
        scaling = max(
            const.DAMAGE_SCALING_MIN, const.DAMAGE_SCALING_FACTOR ** (hit_num - 3)
        )

    # round the damage scaling to 3 decimal places
    # scaling: float = round(scaling, 3)
    return scaling


def get_combo_damage(combo_frame_data_df: DataFrame) -> DataFrame:
    """Calculate the damage of a combo"""
    # add columns for the damage scaling and scaled damage
    table_undizzy_damage: DataFrame = DataFrame(
        columns=[
            const.MOVE_NAME,
            const.DAMAGE,
            const.HIT_NUMBER,
            const.DAMAGE_SCALING,
            const.SCALED_DAMAGE,
            const.UNDIZZY,
            const.TOTAL_DAMAGE_FOR_MOVE,
            const.TOTAL_DAMAGE_FOR_COMBO,
        ],
        index=None,
    )

    df_newhits: DataFrame = parseCombo.parse_hits(combo_frame_data_df)

    # add the newHits table to the damageAndUndizzyTable
    table_undizzy_damage = pd.concat(
        [table_undizzy_damage, df_newhits], ignore_index=True
    )
    # Add a column for the hit number
    # Hit number goes up for each non-zero damage hit

    # Create a new column that will contain the number of hits
    table_undizzy_damage[const.HIT_NUMBER] = 0
    # Loop through all rows in the table
    row: Series[Any]
    for row in table_undizzy_damage.itertuples():
        move: Series[Any] = row
        # Check if the damage is 0
        if int(move.Damage) == 0:
            # If it is 0, set the hit number to 0
            table_undizzy_damage.at[move[0], const.HIT_NUMBER] = 0
        else:
            # If it is not 0, increment the hit number by 1
            # Account for the fact that the index starts at 0 and avoid index out of range errors
            if move[0] == 0:
                table_undizzy_damage.at[move[0], const.HIT_NUMBER] = 1
            else:
                table_undizzy_damage.at[move[0], const.HIT_NUMBER] = (
                    table_undizzy_damage.at[move[0] - 1, const.HIT_NUMBER] + 1
                )

    # add the damage scaling for each hit, based on the hit number column and the damage column
    table_undizzy_damage[const.DAMAGE_SCALING] = table_undizzy_damage.apply(
        lambda row: get_damage_scaling_for_hit(
            row[const.HIT_NUMBER], row[const.DAMAGE]
        ),
        axis=1,
    )

    # calculate the real damage for each hit rounded down
    table_undizzy_damage[const.SCALED_DAMAGE] = table_undizzy_damage.apply(
        lambda row: math.floor(
            float(row[const.DAMAGE]) * float(row[const.DAMAGE_SCALING])
        ),
        axis=1,
    )
    # calculate the total damage for the combo for each hit by summing all previous hits
    table_undizzy_damage[const.TOTAL_DAMAGE_FOR_COMBO] = table_undizzy_damage[
        const.SCALED_DAMAGE
    ].cumsum()
    # set the hit number to the index of the row
    table_undizzy_damage[const.HIT_NUMBER] = table_undizzy_damage.index + 1
    total_damage_for_moves(table_undizzy_damage)
    # Print just the name, damage, scaled damage columns

    return table_undizzy_damage


def total_damage_for_moves(damage_undizzy_table: DataFrame) -> DataFrame:
    """Calculate the total damage for each move in the combo."""
    # add a new column to the df to store the total damage for each move
    damage_undizzy_table[const.TOTAL_DAMAGE_FOR_MOVE] = 0
    move_damage: int = 0
    # loop through each row in the df
    for hit in range(len(damage_undizzy_table)):
        # add the damage to the total damage for the move
        move_damage += damage_undizzy_table.at[hit, const.SCALED_DAMAGE]

        # if it's not the last row
        if hit < len(damage_undizzy_table) - 1:
            damage_undizzy_table.at[hit, const.TOTAL_DAMAGE_FOR_MOVE] = move_damage

            # if the next hit is a different move
            if (
                damage_undizzy_table.at[hit, const.MOVE_NAME]
                != damage_undizzy_table.at[hit + 1, const.MOVE_NAME]
            ):
                move_damage = 0
        else:
            damage_undizzy_table.at[hit, const.TOTAL_DAMAGE_FOR_MOVE] = move_damage

    return damage_undizzy_table


def set_up_pandas_options() -> None:
    """Set up pandas options."""
    # set the max number of rows to display
    pd.set_option("display.max_rows", 100)
    # set the max number of columns to display
    pd.set_option("display.max_columns", 10)
    # set the max width of each column
    pd.set_option("display.width", 100)
    # set the max number of characters to display for each cell
    pd.set_option("max_colwidth", 100)
    # set precision for floats
    pd.set_option("display.precision", 2)


def process_combo(
    combo_input_df: DataFrame, character_name: str, combo_framedata_df_input: DataFrame
) -> DataFrame:
    """Process the combo input and return a dataframe with the combo data."""
    combo_framedata_df = pd.concat(
        [
            combo_framedata_df_input,
            parseCombo.split_columns(combo_input_df, const.MOVE_NAME, " "),
        ]
    )
    combo_framedata_df[const.CHARACTER_NAME] = character_name

    combo_framedata_df = parseCombo.get_frame_data_for_combo(
        combo_framedata_df, full_framedata_df, move_name_alias_df
    )
    combo_framedata_df: DataFrame = get_combo_damage(combo_framedata_df)

    # remove the columns that contain only missing data
    combo_framedata_df.dropna(axis=1, how="all", inplace=True)

    return combo_framedata_df


# %%


def skombo() -> None:
    """Temp main function.
    TODO(Aeiry): move to a UI."""

    set_up_pandas_options()

    for df in [move_name_alias_df, full_framedata_df]:
        remove_whitespace_from_column_names(df)
    csv_list: list[str] = parseCombo.get_csv_list(f"{data_dir}/combo_csvs")

    combo_process_summary: list[Any] = []

    for csv in csv_list:
        csv_filename: str = csv.split("\\")[-1].split(".")[0]

        combo_input_df: DataFrame = pd.read_csv(csv)
        """DataFrame Containing the combo input"""

        # Get the expected damage from the csv
        expected_damage: int = combo_input_df.at[0, const.EXPECTED_DAMAGE]
        character_name: str = combo_input_df.at[0, const.CHARACTER_NAME]
        combo_framedata_df: DataFrame = DataFrame(columns=full_framedata_df.columns)

        combo_framedata_df = process_combo(
            combo_input_df, character_name, combo_framedata_df
        )

        damage: int = combo_framedata_df[const.SCALED_DAMAGE].sum()
        # plot as a log scale
        logger.debug(combo_framedata_df.columns)
        logger.debug(f"Combo dataframe:\n{combo_framedata_df.to_string()}\n")

        logger.debug(f"Calculated damage: {damage}")
        logger.debug(f"Expected damage: {expected_damage}")
        logger.debug("Difference: " + str(damage - expected_damage))
        logger.debug(
            f"Percentage difference: {round((damage - expected_damage) / expected_damage * 100, 2)}%"
        )

        summary: dict[str, Any] = {
            "Character": character_name,
            "Combo": csv_filename,
            "ExpectedDamage": round(expected_damage),
            "CalculatedDamage": round(damage),
            "Difference": damage - round(expected_damage),
            "PercentageDifference": f"{round((damage - expected_damage) / expected_damage * 100)}%",
        }
        # Add the combo to the output
        combo_process_summary.append(summary)

    # Create a dataframe from the output
    output_df: DataFrame = DataFrame(combo_process_summary)

    for combo, pct_diff in zip(  # type: ignore
        output_df["Combo"], output_df["PercentageDifference"]  # type: ignore
    ):
        if pct_diff != "0%":
            logger.info(f"{combo} has a {pct_diff} difference")

    logger.info("Done")


def main() -> None:
    """Main function."""

    skombo()


if __name__ == "__main__":
    main()
