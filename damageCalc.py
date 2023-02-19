"""This module contains the functions to calculate the damage of a skullgirls combo."""

import logging
import sys
import math
import pandas
import constants as const
import parseCombo as pc

logging.basicConfig(level=logging.DEBUG)
logger: logging.Logger = logging.getLogger(__name__)

move_name_alias_df: pandas.DataFrame = pandas.read_csv("data/moveNameAliases.csv")

full_framedata_df: pandas.DataFrame = pandas.read_csv("data/fullFrameData.csv")
# For testing the damage calc in this stage, I want to check against a folder full of csvs


def get_damage_scaling_for_hit(hit_num: int, damage: int) -> float:
    """Get the damage scaling for a hit.

    Args:
        hit_num (int): The hit number of the hit.
        damage (int): The damage of the hit.

    Returns:
        float: The damage scaling for the hit.
    """
    # attempt to convert the damage to an int
    try:
        damage = int(damage)
    except ValueError:
        logger.error("Damage is not an int")
        sys.exit(1)
    # check if the damage is 0 -0 or none
    if damage in [0, -1]:
        # return the damage scaling for the hit before, as the hit did no damage
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


def get_combo_damage(combo_frame_data_df: pandas.DataFrame) -> int:
    """Calculate the damage of a combo.

    Args:
        combo_frame_data_df (pandas.DataFrame): The dataframe containing the frame data for the combo.

            Returns:
        int: The total damage of the combo.
    """
    # undizzy values for each hit level are 15,30,40,30,0
    str_hitnum = "Hit Number"
    str_scaled_dmg = "Scaled Damage"

    table_undizzy: pandas.DataFrame = pandas.DataFrame(
        columns=["Light", "Medium", "Heavy", "Special", "Throws+Supers"]
    )
    # add the undizzy values to the table
    table_undizzy.loc[0] = [15, 30, 40, 30, 0]  # type: ignore

    # create a new table to store the damage and undizzy values for each hit
    table_undizzy_damage: pandas.DataFrame = pandas.DataFrame(
        columns=[
            const.MOVE_NAME_COLUMN,
            const.HIT_NUMBER_COLUMN,
            const.DAMAGE_COLUMN,
            const.DAMAGE_SCALING_COLUMN,
            const.SCALED_DAMAGE_COLUMN,
            const.UNDIZZY_COLUMN,
        ]
    )

    df_newhits: pandas.DataFrame = pc.parse_hits(combo_frame_data_df)

    # add the newHits table to the damageAndUndizzyTable
    table_undizzy_damage = pandas.concat(
        [table_undizzy_damage, df_newhits], ignore_index=True
    )
    # Add a column for the hit number
    # Hit number goes up for each non-zero damage hit

    for i in range(len(table_undizzy_damage)):
        if int(table_undizzy_damage.at[i, "Damage"]) > 0:
            if i == 0:
                table_undizzy_damage.at[i, str_hitnum] = 1
            else:
                table_undizzy_damage.at[i, str_hitnum] = (
                    table_undizzy_damage.at[i - 1, str_hitnum] + 1
                )

    # add the damage scaling for each hit, based on the hit number column and the damage column
    table_undizzy_damage["DamageScaling"] = table_undizzy_damage.apply(
        lambda row: get_damage_scaling_for_hit(row[str_hitnum], row["Damage"]), axis=1
    )

    # calculate the real damage for each hit rounded down
    table_undizzy_damage[str_scaled_dmg] = table_undizzy_damage.apply(
        lambda row: math.floor(float(row["Damage"]) * float(row["DamageScaling"])),
        axis=1,
    )
    # calculate the total damage for the combo for each hit by summing all previous hits
    table_undizzy_damage["Total Damage"] = table_undizzy_damage[str_scaled_dmg].cumsum()
    # set the hit number to the index of the row
    table_undizzy_damage[str_hitnum] = table_undizzy_damage.index + 1
    total_damage: int = table_undizzy_damage[str_scaled_dmg].sum()
    total_damage_for_moves(table_undizzy_damage)
    logger.info(table_undizzy_damage)
    return total_damage


def total_damage_for_moves(damage_undizzy_table: pandas.DataFrame) -> pandas.DataFrame:
    """Calculate the total damage for each move in the combo.

    Args:
        damage_undizzy_table (pandas.DataFrame): The dataframe containing the damage and undizzy values for each hit.

    Returns:
        pandas.DataFrame: The dataframe containing the damage and undizzy values for each hit with the total damage for each move added.
    """

    str_total_dmg_for_move = "Total Damage for Move"
    # add a new column to the df to store the total damage for each move
    damage_undizzy_table.at[:, str_total_dmg_for_move] = 0
    move_damage: int = 0
    # loop through each row in the df
    for hit in range(len(damage_undizzy_table)):
        move_name: str = damage_undizzy_table.at[hit, const.MOVE_NAME_COLUMN]

        # add the damage to the total damage for the move
        move_damage += damage_undizzy_table.at[hit, "Scaled Damage"]
        move_damage += 1

        # if it's not the last row and the next row has a different move name
        if (
            hit < len(damage_undizzy_table) - 1
            and move_name != damage_undizzy_table.at[hit + 1, const.MOVE_NAME_COLUMN]
        ):
            # add the total damage for the move to the damageAndUndizzyTable at the location of the first hit of the move
            damage_undizzy_table.at[hit, str_total_dmg_for_move] = move_damage

            # reset the total damage and hits for the move
            move_damage = 0

        # if it's the last row, add the total damage and hits for the last move to table
        elif hit == len(damage_undizzy_table) - 1:
            # add the total damage and hits for the last move to table
            damage_undizzy_table.at[hit, str_total_dmg_for_move] = move_damage

    return damage_undizzy_table


def skombo() -> None:
    """Temp main function.
    TODO(Aeiry): move to a UI."""
    csv_list: list[str] = pc.get_csv_list("data\\combo_csvs")

    logging.basicConfig(stream=sys.stdout, level=logging.DEBUG, format="%(message)s")

    for csv in csv_list:
        combo_input_df: pandas.DataFrame = pandas.read_csv(csv)

        expected_damage: int = pc.get_first_value_from_df(
            combo_input_df, "Expected Damage"
        )

        # Set some constants
        character_name: str = pc.get_first_value_from_df(combo_input_df, "Character")
        print(f"===========\nCharacter: {character_name}\n")

        move_column_name: str = const.MOVE_NAME_COLUMN

        # Create an empty dataframe to hold the combo data
        # Uses the same columns as tempFrameData
        combo_framedata_df: pandas.DataFrame = pc.create_df_copy_columns(
            full_framedata_df
        )

        combo_framedata_df = pc.concatenate_dataframes(
            combo_framedata_df, pc.split_columns(combo_input_df, move_column_name, " ")
        )

        # Set the character column in the comboDf to the character name
        pc.set_column_value(combo_framedata_df, "Character", character_name)

        logger.debug(f"Combo dataframe:\n{combo_framedata_df}\n")

        combo_framedata_df = pc.get_frame_data_for_combo(
            combo_framedata_df, full_framedata_df, move_name_alias_df
        )

        damage: int = get_combo_damage(combo_framedata_df)

        print(f"Calculated damage: {damage}")
        print(f"Expected damage: {expected_damage}")
        print("Difference: " + str(damage - expected_damage))
        print(
            f"Percentage difference: {round((damage - expected_damage) / expected_damage * 100, 2)}%"
        )


# main function


def main() -> None:
    """Main function."""

    skombo()


if __name__ == "__main__":
    main()
