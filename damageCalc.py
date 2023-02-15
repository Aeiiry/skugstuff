
from asyncio.log import logger
import math
from os import stat
from random import choice
import re
from shutil import move
import pandas
import inspect
import numpy
import re as regex
import logging
import sys
import typing

logging.basicConfig(stream=sys.stdout,
                    level=logging.DEBUG,
                    format="%(message)s")


comboInputDf: pandas.DataFrame = pandas.read_csv("data/testcombo1.csv")

logger.debug(f"Combo input CSV:\n{comboInputDf}\n")

character_reference_df: pandas.DataFrame = pandas.read_csv(
    "data/characters.csv")
move_name_alias_df: pandas.DataFrame = pandas.read_csv("data/alias.csv")
full_framedata_df: pandas.DataFrame = pandas.read_csv("data/frameData.csv")


def create_df_copy_columns(df: pandas.DataFrame) -> pandas.DataFrame:
    """Creates a copy of a dataframe with the same columns"""
    copy_df: pandas.DataFrame = pandas.DataFrame(columns=df.columns)
    return copy_df


def get_character_name() -> str:
    return comboInputDf.iloc[0]["Character"]


# get the expected damage for the combo, first value in the third column of the combo csv
def get_expected_damage() -> int:
    return comboInputDf.iloc[0]["Expected Damage"]


expected_damage: int = get_expected_damage()

# Set some constants
character_name: str = get_character_name()
move_column_name: str = "Move Name"

# Set the character column in the comboDf to the character name


def set_column_value(df: pandas.DataFrame, column: str, value: str) -> None:
    logger.debug(f"Setting {column} to {value}")
    df[column] = value


# Create an empty dataframe to hold the combo data
# Uses the same columns as tempFrameData
combo_framedata_df: pandas.DataFrame = create_df_copy_columns(
    full_framedata_df)


def split_columns(df: pandas.DataFrame, column_name,
                  seperator) -> pandas.DataFrame:
    splitdf = df.copy()
    # split the values in a column on a given seperator
    logger.debug(f'Splitting {column_name} on "{seperator}"')
    splitdf[column_name] = splitdf[column_name].str.split(seperator)
    # explode the column so that each value is on a row
    splitdf: pandas.DataFrame = splitdf.explode(column_name)
    return splitdf


def concatenate_dataframes(df, inputdf) -> pandas.DataFrame:
    # Concatenates two dataframes
    return pandas.concat([df, inputdf], ignore_index=True)


combo_framedata_df = concatenate_dataframes(
    combo_framedata_df, split_columns(comboInputDf, move_column_name, " "))

# Set the character column in the comboDf to the character name
set_column_value(combo_framedata_df, "Character", character_name)

logger.debug(f"Combo dataframe:\n{combo_framedata_df}\n")


def find_move_from_name_and_character(
        move_name: str, character_name: str,
        df: pandas.DataFrame) -> pandas.DataFrame:
    """Find a move from the move name and character name

    Args:
        move_name (str): The name of the move
        character_name (str): The name of the character
        df (pandas.DataFrame): The dataframe containing the move data
    Returns:
        pandas.DataFrame: The dataframe containing the move data
    """

    # logger.debug(f"Searching for [{move_name}] for character [{character_name}]")

    name_regex: str = rf"^{move_name}$|\n{move_name}$|^{move_name}\n|\n{move_name}\n"

    # Check if the character name is the same, case insensitive
    character_check: pandas.Series[bool] = df["Character"].str.contains(
        character_name, flags=re.IGNORECASE)

    # Check if the move name is in either column, case insensitive
    move_check: pandas.Series[bool] = df["Move Name"].str.contains(
        name_regex, flags=re.IGNORECASE)
    if not move_check.any():
        # if the move name is not found, check the alias column
        move_check: pandas.Series[bool] = df["Alt Names"].str.contains(
            name_regex, flags=re.IGNORECASE)

    result: pandas.DataFrame = df[move_check & character_check]

    if result.empty:
        return pandas.DataFrame()
    else:
        return result


def get_frame_data_for_move(move_name: str, df: pandas.DataFrame) -> pandas.DataFrame:
    # Get the frame data for a single move, given a move name and a dataframe

    logger.debug(
        f"=================\nGetting frame data for move [{move_name}]")
    # check for follow-up moves such as 214HP~P or QCBLP P or 214 MP,P etc
    # regex that matches L, M or H, followed by P or K followed by "~", ",", "+" or " " followed by P or K
    follow_up_move_regex: str = r"(.+[lmh]?[pk])([~\+,\s]){1,3}([pk])"
    # search for the follow-up move in the move name case insensitive
    follow_up_move_search: re.Match[str] | None = re.search(
        follow_up_move_regex, move_name, re.IGNORECASE)

    if follow_up_move_search:
        # if the move name contains a follow-up move, get the frame data for the follow-up move
        logger.debug(f"Move [{move_name}] is a follow-up move")

        # get the frame data for the follow-up move
        data_to_add, move_name = find_base_move_data_for_followup_move(
            move_name, df, follow_up_move_search)
    else:
        data_to_add: pandas.DataFrame = pandas.DataFrame()

    generic_move_name_regex: str = r"(.*?)([lmh])([pk])"
    repeat_moves_regex: str = r"[Xx](\d+)$"

    data_for_move: pandas.DataFrame = find_move_from_name_and_character(move_name,
                                                                        character_name, df)

    # if the move name is not in the frame data dataframe, check if it is a repeat move
    repeat_search: re.Match[str] | None = re.search(repeat_moves_regex,
                                                    move_name, re.IGNORECASE)
    if repeat_search:
        # if the move name contains an x or X followed by a number, it is a repeat move (e.g 5MKx2)
        logger.debug(f"Move [{move_name}] is a repeat move")

        # get the move name without the repeat count and set the move name to that
        data_for_move = find_repeat_move_data(move_name, df,
                                              repeat_moves_regex,
                                              repeat_search)

    # if the move name is not in the frame data dataframe, check if it has an alias
    if data_for_move.empty:

        logger.debug(f"Move name not found, checking aliases")

        # try to get the alias move name
        data_for_move = find_alias_move_data(move_name, df)

    # if the move name is not in the frame data dataframe, try to find a generic form of the move name in the frame data dataframe
    elif data_for_move.empty and re.search(generic_move_name_regex, move_name):

        logger.debug(
            f"Move [{move_name}] not found, checking generic move names for matches"
        )

        # search for the generic move name in the frame data dataframe
        data_for_move = find_generic_move_data(
            move_name, df, generic_move_name_regex)

    # if the move name is not in the frame data dataframe, log that the move was not found
    if data_for_move.empty:

        logger.warning(f"Move {move_name} not found")

        # return an empty dataframe with the same columns as the frame data dataframe
        data_for_move: pandas.DataFrame = pandas.DataFrame(columns=df.columns)
    else:
        if not data_to_add.empty:
            # if the move is a follow-up move, add the frame data for the follow-up move to the dataframe
            data_for_move = pandas.concat([data_for_move, data_to_add])

    # return the dataframe with the move data
    return data_for_move


def find_generic_move_data(move_name: str, df: pandas.DataFrame, generic_move_name_regex: str) -> pandas.DataFrame:

    match: re.Match[str] | None = re.search(generic_move_name_regex,
                                            move_name,
                                            flags=re.IGNORECASE)

    # if the generic move name is found
    if match:
        # get the generic move name
        generic_move_name: str = match.group(1) + match.group(3)

        # search for the generic move name in the frame data dataframe
        logger.debug(
            f"Data for move [{move_name}] found as [{generic_move_name}]")
        data_for_move: pandas.DataFrame = find_move_from_name_and_character(
            generic_move_name, character_name, df)
    else:
        data_for_move: pandas.DataFrame = pandas.DataFrame()

    return data_for_move


def find_alias_move_data(move_name: str,
                         df: pandas.DataFrame) -> pandas.DataFrame:
    move_name_alias: str = get_alias_move(move_name)

    # if the alias move name is not empty, get the frame data for the alias move name
    if move_name_alias != "":
        logger.debug(f"Alias for [{move_name}] found as [{move_name_alias}]")
        data_for_move: pandas.DataFrame = find_move_from_name_and_character(
            move_name_alias, character_name, df)
    else:
        data_for_move: pandas.DataFrame = pandas.DataFrame()

    return data_for_move


def find_repeat_move_data(
    move_name: str,
    df: pandas.DataFrame,
    repeat_moves_regex: str,
    repeat_search: re.Match[str] | None,
) -> pandas.DataFrame:

    move_name_without_repeat_count: str = re.sub(repeat_moves_regex, "",
                                                 move_name)

    # get the frame data for the move without the repeat count
    data_for_move_without_repeat_count: pandas.DataFrame = (
        find_move_from_name_and_character(move_name_without_repeat_count,
                                          character_name, df))

    if data_for_move_without_repeat_count.any:
        data_for_move: pandas.DataFrame = data_for_move_without_repeat_count
        # if the move without the repeat count is found, get next x normals in the sequence where x is the repeat count -1
        # eg if the move is 5HPx3, get the frame data for 5HP, then get the frame data for 5HPx2 and 5HPx3
        logger.debug(f"Found data for move [{move_name_without_repeat_count}]")
        for i in range(int(repeat_search.group(1)) -
                       1) if repeat_search else range(0):
            temp_move_name: str = move_name_without_repeat_count + "X" + str(
                i + 2)
            temp_move_data: pandas.DataFrame = find_move_from_name_and_character(
                temp_move_name, character_name, df)

            data_for_move = pandas.concat(
                [data_for_move, temp_move_data],
                ignore_index=True,
            )
    else:
        data_for_move: pandas.DataFrame = pandas.DataFrame()

    return data_for_move


def find_base_move_data_for_followup_move(
    move_name: str,
    df: pandas.DataFrame,
    follow_up_move_search: re.Match[str]
) -> tuple[pandas.DataFrame, str]:
    # if the move is a follow-up move, get the frame data for the follow-up move and return the name of the base move and the frame data for the follow-up move
    base_move_name: str = follow_up_move_search.group(1)
    data_for_move: pandas.DataFrame = find_move_from_name_and_character(
        move_name, character_name, df)

    return data_for_move, base_move_name


def get_alias_move(move_name: str) -> str:

    # get all move name aliases that contain the given move name
    alias_df: pandas.DataFrame = move_name_alias_df[
        move_name_alias_df["Value"].str.contains(move_name,
                                                 na=False,
                                                 flags=re.IGNORECASE)]

    # return the alias if it exists
    return alias_df["Key"].iloc[0] if not alias_df.empty else ""


def get_frame_data_for_combo(combo_df: pandas.DataFrame) -> pandas.DataFrame:

    # initialize an empty frame data pandas.DataFrame
    combo_framedata_df: pandas.DataFrame = pandas.DataFrame(
        columns=full_framedata_df.columns)

    # get the combo moves from the given combo pandas.DataFrame
    combo_moves: pandas.Series[str] = combo_df[move_column_name]

    # loop through each move in the combo
    for move in combo_moves:
        # skip empty strings or strings with only spaces
        if move == "" or move.isspace():
            continue
        move.strip()
        # get the frame data for the current move
        move_framedata: pandas.DataFrame = get_frame_data_for_move(
            move, full_framedata_df)

        # append the move frame data to the temporary frame data pandas.DataFrame
        combo_framedata_df = concatenate_dataframes(combo_framedata_df,
                                                    move_framedata)

    return combo_framedata_df


combo_framedata_df: pandas.DataFrame = get_frame_data_for_combo(
    combo_framedata_df)


maxUndizzy: int = 240
damageScaling: float = 0.875
damageScalingMin: float = 0.2
# damage scaling minimum for attacks with over 1000 base damage
damageScalingMinBigHit: float = 0.275
# all hits after the 3rd hit are scaled compundingly by 0.875
# the minimum damage scaling is 0.2
# the minimum damage scaling for attacks with over 1000 base damage is 0.275
# function to calculate the damage scaling for a hit


def parse_hits(combo_frame_data_df: pandas.DataFrame) -> pandas.DataFrame:
    """Parse the hits from the combo frame data dataframe.

    Args:
        combo_frame_data_df (pandas.DataFrame): Combo frame data dataframe.

    Returns:
        pandas.DataFrame: Hits dataframe. Each row is a hit.
    """
    # Set up the regex to find the number of hits in a move

    # Set up the dataframe for the hits
    hits_df: pandas.DataFrame = pandas.DataFrame(
        columns=["Move Name", "Damage", "Chip", "Special"])

    for move in combo_frame_data_df["Move Name"]:
        # If the move is a kara, set the damage of the previous move to 0
        if move == "kara":
            logger.debug(
                f"Kara cancel detected, setting damage of previous move to 0")
            # get the location of the move 1 row above the current move
            combo_frame_data_df.loc[combo_frame_data_df.index.get_loc(move) -
                                    1, "Damage"] = 0
            continue

        # If the move does not have any damage, continue to the next move
        damage_check: pandas.DataFrame = combo_frame_data_df.loc[
            combo_frame_data_df["Move Name"] == move, "Damage"]  # type:ignore
        if damage_check.empty or damage_check.iloc[0] == "":
            continue

        # Initialize the lists for the damage, chip, and special properties of the move
        move_chip: list[str] = []
        move_special: list[str] = []

        # Get the damage list for the current move
        currentmove_damagestr: str = combo_frame_data_df.loc[
            combo_frame_data_df["Move Name"] == move, "Damage"].iloc[0]  # type:ignore

        # Extract the chip properties from the damage list and remove them from the list
        move_chip, currentmove_damagestr = extract_values_from_parentheses(
            move_chip, currentmove_damagestr)
        # Extract the special properties from the damage list and remove them from the list
        move_special, currentmove_damagestr = extract_values_from_brackets(
            move_special, currentmove_damagestr)

        # Initialize the list of the damage done by the move
        currentmove_damagelist: list = currentmove_damagestr.split(",")

        # clean the damage list and extract the damage, adding a row to the hits dataframe for each hit
        hits_df: pandas.DataFrame = clean_and_extract_damage(
            hits_df, move, currentmove_damagelist)

    return hits_df


def clean_and_extract_damage(
    hits_df: pandas.DataFrame,
    move: str,
    dmg_list: list[str],
) -> pandas.DataFrame:
    """Cleans the damage list and extracts the damage, adding a row to the hits dataframe for each hit

    Args:
        hits_df (pandas.DataFrame): dataframe for hits to be added to
        move (str): move name
        curr_dmg_list (list[str]): list of damage values for the move to be parsed

    Returns:
        pandas.DataFrame: dataframe with the hits for the move added
    """

    output_df: pandas.DataFrame = hits_df
    # Set up the regex to find the number of hits in a move
    num_hits_regex: str = r"(\d+)x(\d+)$"
    move_dmg: list[int] = []
    # for every element in the list of the move's damage values
    for i in range(len(dmg_list)):
        # if the string is empty, skip it
        if dmg_list[i] == "":
            continue
            # remove whitespace
        dmg_list[i] = re.sub(r"\s", "", dmg_list[i])
        if dmg_list[i] == "":
            continue
            # search for a match to the regex pattern for the number of hits and damage
        numhits_result: re.Match[str] | None = re.search(
            num_hits_regex, dmg_list[i])
        # if the regex pattern is found, extract the damage and number of hits
        if numhits_result:
            numhits: int = int(numhits_result.group(2))
            hitdmg: int = int(numhits_result.group(1))
            # add the damage for each hit to the move's damage list
            for j in range(numhits):
                move_dmg.append(hitdmg)
                # add the damage to a temporary pandas.DataFrame
                temp_df: pandas.DataFrame = pandas.DataFrame(
                    [[move, hitdmg, None, None]],
                    columns=output_df.columns,
                )
                # append the temporary pandas.DataFrame to the hits pandas.DataFrame
                output_df: pandas.DataFrame = pandas.concat([output_df, temp_df],
                                                            ignore_index=True)

            # if the regex pattern is not found and the string is not empty, add it directly to the move's damage list
        if dmg_list[i] != "" and not re.search(num_hits_regex,
                                               dmg_list[i]):
            move_dmg.append(int(dmg_list[i]))
            # add the damage to a temporary pandas.DataFrame
            temp_df: pandas.DataFrame = pandas.DataFrame(
                [[move, dmg_list[i], None, None]],
                columns=output_df.columns,
            )
            # append the temporary pandas.DataFrame to the hits pandas.DataFrame
            output_df: pandas.DataFrame = pandas.concat([output_df, temp_df],
                                                        ignore_index=True)
        logger.info(f"moveDamage: {move_dmg}")
    return output_df


def extract_values_from_brackets(l: list[str],
                                 s: str) -> tuple[list[str], str]:
    """Extracts values from a string surrounded by square brackets and removes them from the string

    Args:
        l (list[str]): list of strings, extracted values will be appended to this list
        s (str): string to search for values

    Returns:
        tuple[list[str], str]: tuple containing the list of extracted values and the string with the values removed
    """
    S: str = s
    # Define the regex pattern to search for
    bracket_regex: str = r"\[.+\]"
    # Search for the regex pattern in the string
    if re.search(bracket_regex, s):
        # If found, return a Match object
        r: re.Match[str] | None = re.search(bracket_regex, s)
        # Append the match to the list
        if r:
            l.append(r.group(0))
        # Remove the regex pattern from the string
        S: str = re.sub(bracket_regex, "", s)
        # Log the list and string
        logger.debug(l)
        logger.debug(S)
    # Return the string
    return l, S


def extract_values_from_parentheses(l: list[str],
                                    s: str) -> tuple[list[str], str]:
    """Extracts values from a string surrounded by parentheses and removes them from the string

    Args:
        l (list[str]): list of strings, extracted values will be appended to this list
        s (str): string to search for values

    Returns:
        tuple[list[str], str]: tuple containing the list of extracted values and the string with the values removed
    """
    S: str = s
    # define regex for parentheses
    parentheses_regex: str = r"\(.+\)"
    # check if regex is found in string
    if re.search(parentheses_regex, s):
        # assign match to variable
        r: re.Match[str] | None = re.search(parentheses_regex, s)
        # append string inside parentheses to list
        if r:
            l.append(r.group(0))
        # remove parentheses and string from string
        S: str = re.sub(parentheses_regex, "", s)
        logger.debug(l)
        logger.debug(S)
    return l, S


def get_damage_scaling_for_hit(hit_num: int, d: int) -> float:
    # convert the damage to an int
    damage: int = int(d)
    # check if the damage is 0 -0 or none
    if damage == 0 or damage == -0:
        # return the damage scaling for the hit before, as the hit did no damage
        return max(damageScalingMin, damageScaling**(hit_num - 4))

    if hit_num <= 3:
        return 1
    # check if the damage is greater than 1000
    if damage >= 1000:
        scaling: float = max(damageScalingMinBigHit,
                             damageScaling**(hit_num - 3))
    else:
        scaling: float = max(damageScalingMin, damageScaling**(hit_num - 3))

    # round the damage scaling to 3 decimal places
   # scaling: float = round(scaling, 3)
    return scaling


def get_combo_damage(combo_frame_data_df) -> int:
    # undizzy values for each hit level are 15,30,40,30,0

    table_undizzy: pandas.DataFrame = pandas.DataFrame(
        columns=["Light", "Medium", "Heavy", "Special", "Throws+Supers"])
    # add the undizzy values to the table
    table_undizzy.loc[0] = [15, 30, 40, 30, 0]  # type: ignore

    # create a new table to store the damage and undizzy values for each hit
    table_undizzy_damage: pandas.DataFrame = pandas.DataFrame(columns=[
        "Move Name",
        "Hit Number",
        "Damage",
        "DamageScaling",
        "Scaled Damage",
        "Undizzy",
    ])

    df_newhits: pandas.DataFrame = parse_hits(combo_frame_data_df)

    # add the newHits table to the damageAndUndizzyTable
    table_undizzy_damage = pandas.concat([table_undizzy_damage, df_newhits],
                                         ignore_index=True)
    # Add a column for the hit number
    # Hit number goes up for each non-zero damage hit

    for i in range(len(table_undizzy_damage)):
        if int(table_undizzy_damage.at[i, "Damage"]) > 0:
            if i == 0:
                table_undizzy_damage.at[i, "Hit Number"] = 1
            else:
                table_undizzy_damage.at[i, "Hit Number"] = (
                    table_undizzy_damage.at[i - 1, "Hit Number"] + 1)

    # add the damage scaling for each hit, based on the hit number column and the damage column
    table_undizzy_damage["DamageScaling"] = table_undizzy_damage.apply(
        lambda row: get_damage_scaling_for_hit(row["Hit Number"], row["Damage"]
                                               ),
        axis=1)

    # calculate the real damage for each hit rounded down
    table_undizzy_damage["Scaled Damage"] = table_undizzy_damage.apply(
        lambda row: math.floor(float(row["Damage"]) * float(row["DamageScaling"])), axis=1)
    # calculate the total damage for the combo for each hit by summing all previous hits
    table_undizzy_damage["Total Damage"] = table_undizzy_damage[
        "Scaled Damage"].cumsum()
    # set the hit number to the index of the row
    table_undizzy_damage["Hit Number"] = table_undizzy_damage.index + 1
    total_damage: int = table_undizzy_damage["Scaled Damage"].sum()
    total_damage_for_moves(table_undizzy_damage)
    logger.info(table_undizzy_damage)
    return total_damage


def total_damage_for_moves(
        damage_undizzy_table: pandas.DataFrame) -> pandas.DataFrame:
    # add a new column to the df to store the total damage for each move
    damage_undizzy_table.at[:, "Total Damage For Move"] = 0
    move_damage: int = 0
    # loop through each row in the df
    for hit in range(len(damage_undizzy_table)):

        move_name: str = damage_undizzy_table.at[hit, "Move Name"]

        # add the damage to the total damage for the move
        move_damage += damage_undizzy_table.at[hit, "Scaled Damage"]
        move_damage += 1

        # if it's not the last row and the next row has a different move name
        if (hit < len(damage_undizzy_table) - 1 and
                move_name != damage_undizzy_table.at[hit + 1, "Move Name"]):

            # add the total damage for the move to the damageAndUndizzyTable at the location of the first hit of the move
            damage_undizzy_table.at[hit, "Total Damage For Move"] = move_damage

            # reset the total damage and hits for the move
            move_damage = 0

        # if it's the last row, add the total damage and hits for the last move to table
        elif hit == len(damage_undizzy_table) - 1:
            # add the total damage and hits for the last move to table
            damage_undizzy_table.at[hit, "Total Damage For Move"] = move_damage

    return damage_undizzy_table


damage: int = get_combo_damage(combo_framedata_df)


logger.debug(f"Calculated damage: {damage}")
logger.debug(f"Expected damage: {expected_damage}")

logger.debug("Difference: " + str(damage - expected_damage))
logger.debug("Different as percentage: " + '%.2f' %
             ((damage - expected_damage) / expected_damage * 100) + "%")
