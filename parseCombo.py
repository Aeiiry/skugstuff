"""Functions for parsing the combo data from the csv files"""
import logging
import os
import typing
import re
import pandas
import constants as const

logging.basicConfig(level=logging.DEBUG)
logger: logging.Logger = logging.getLogger(__name__)


def get_csv_list(path: str) -> list[str]:
    """Returns a list of all csv files in a given path with their relative path"""
    return [os.path.join(path, f) for f in os.listdir(path) if f.endswith(".csv")]


def create_df_copy_columns(df: pandas.DataFrame) -> pandas.DataFrame:
    """Creates a copy of a dataframe with the same columns"""

    copy_df: pandas.DataFrame = pandas.DataFrame(columns=df.columns)

    return copy_df


def get_first_value_from_df(df: pandas.DataFrame, key: str) -> typing.Any:
    """Gets the first value from a dataframe for a given key"""
    value: typing.Any = df[key][0]
    return value


def set_column_value(df: pandas.DataFrame, column: str, value: str) -> None:
    """Set an entire column to a given value

    Args:
        df (pandas.DataFrame): dataframe to set the column value in
        column (str): column to set the value in
        value (str): value to set the column to
    """
    logger.debug(f"Setting {column} to {value}")
    df[column] = value


def split_columns(
    df: pandas.DataFrame, column_name: str, seperator: str
) -> pandas.DataFrame:
    """Split a column into multiple rows based on a given seperator

    Args:
        df (pandas.DataFrame): dataframe to split the column in
        column_name (str): column to split
        seperator (str): seperator to split the column on

    Returns:
        pandas.DataFrame: dataframe with the column split
    """
    splitdf = df.copy()
    # split the values in a column on a given seperator
    logger.debug(f'Splitting {column_name} on "{seperator}"')
    splitdf[column_name] = splitdf[column_name].str.split(seperator)
    # explode the column so that each value is on a row
    splitdf = splitdf.explode(column_name)
    return splitdf


def concatenate_dataframes(
    dataframe1: pandas.DataFrame, dataframe2: pandas.DataFrame
) -> pandas.DataFrame:
    """Concatenate two dataframes

    Args:
        dataframe1 (pandas.DataFrame): first dataframe to concatenate
        dataframe2 (pandas.DataFrame): second dataframe to concatenate

    Returns:
        pandas.DataFrame: resulting dataframe
    """
    return pandas.concat([dataframe1, dataframe2], ignore_index=True)


def find_move_from_name_and_character(
    # TODO(aeiry): Fix all of this, mostly the checking of the character name and move name
    move_name: str,
    character_name: str,
    df: pandas.DataFrame,
) -> pandas.DataFrame:
    """Find a move from the move name and character name

    Args:
        move_name (str): The name of the move
        character_name (str): The name of the character
        df (pandas.DataFrame): The dataframe containing the move data
    Returns:
        pandas.DataFrame: The dataframe containing the move data
    """

    # logger.debug(f"Searching for [{move_name}] for character [{character_name}]")

    name_regex: str = rf"^{move_name}$|^{move_name}\n|\n{move_name}$|\n{move_name}\n"

    # Check if the character name is the same, case insensitive
    character_check: pandas.Series[bool] = df["Character"].str.contains(
        character_name, flags=re.IGNORECASE
    )

    # for each of the rows that match the character name, check if the move name is the same
    for index, row in df[character_check].iterrows():
        # check if the move name is the same, case insensitive
        move_check_regex: re.Match[str] | None = re.search(
            name_regex, row["Move Name"], flags=re.IGNORECASE
        )
        if move_check_regex:
            logger.debug(f"Found move [{move_name}] for character [{character_name}]")
            return df.loc[[index]]
        else:
            move_check_regex = re.search(
                name_regex, row["Alt Names"], flags=re.IGNORECASE
            )
            if move_check_regex:
                logger.debug(
                    f"Found move [{move_name}] for character [{character_name}]"
                )
                return df.loc[[index]]

    logger.debug(f"Could not find move [{move_name}] for character [{character_name}]")
    return pandas.DataFrame()


def get_frame_data_for_move(
    move_name: str,
    full_framedata_df: pandas.DataFrame,
    character_name: str,
    move_name_alias_df: pandas.DataFrame,
) -> pandas.DataFrame:
    """Get the frame data for a single move, given a move name and a dataframe

    Args:
        move_name (str): The name of the move
        full_framedata_df (pandas.DataFrame): The dataframe containing the move data
        character_name (str): The name of the character
        move_name_alias_df (pandas.DataFrame): The dataframe containing the move aliases
    Returns:
        pandas.DataFrame: The dataframe containing the move data
    """
    # Get the frame data for a single move, given a move name and a dataframe

    logger.debug(f"=================\nGetting frame data for move [{move_name}]")
    # check for follow-up moves such as 214HP~P or QCBLP P or 214 MP,P etc
    # regex that matches L, M or H, followed by P or K followed by "~", ",", "+" or " " followed by P or K
    follow_up_move_regex: str = r"(.+[lmh]?[pk])([~\+,\s]){1,3}([pk])"
    # search for the follow-up move in the move name case insensitive
    follow_up_move_search: re.Match[str] | None = re.search(
        follow_up_move_regex, move_name, re.IGNORECASE
    )

    if follow_up_move_search:
        # if the move name contains a follow-up move, get the frame data for the follow-up move
        logger.debug(f"Move [{move_name}] is a follow-up move")

        # get the frame data for the follow-up move
        data_to_add, move_name = find_base_move_data_for_followup_move(
            move_name, full_framedata_df, follow_up_move_search, character_name
        )
    else:
        data_to_add = pandas.DataFrame()

    generic_move_name_regex: str = r"(.*?)([lmh])([pk])"
    repeat_moves_regex: str = r"[Xx](\d+)$"

    data_for_move: pandas.DataFrame = find_move_from_name_and_character(
        move_name, character_name, full_framedata_df
    )

    # if the move name is not in the frame data dataframe, check if it is a repeat move
    repeat_search: re.Match[str] | None = re.search(
        repeat_moves_regex, move_name, re.IGNORECASE
    )
    if repeat_search:
        # if the move name contains an x or X followed by a number, it is a repeat move (e.g 5MKx2)
        logger.debug(f"Move [{move_name}] is a repeat move")

        # get the move name without the repeat count and set the move name to that
        data_for_move = find_repeat_move_data(
            move_name,
            full_framedata_df,
            repeat_moves_regex,
            repeat_search,
            character_name,
        )

    # if the move name is not in the frame data dataframe, check if it has an alias
    if data_for_move.empty:

        logger.debug("Move name not found, checking aliases")

        # try to get the alias move name
        data_for_move = find_alias_move_data(
            move_name, full_framedata_df, character_name, move_name_alias_df
        )

    # if the move name is not in the frame data dataframe, try to find a generic form of the move name in the frame data dataframe
    elif data_for_move.empty and re.search(generic_move_name_regex, move_name):

        logger.debug(
            f"Move [{move_name}] not found, checking generic move names for matches"
        )

        # search for the generic move name in the frame data dataframe
        data_for_move = find_generic_move_data(
            move_name, full_framedata_df, generic_move_name_regex, character_name
        )

    # if the move name is not in the frame data dataframe, log that the move was not found
    if data_for_move.empty:

        logger.warning(f"Move {move_name} not found")

        # return an empty dataframe with the same columns as the frame data dataframe
        data_for_move = pandas.DataFrame(columns=full_framedata_df.columns)
    else:
        if not data_to_add.empty:
            # if the move is a follow-up move, add the frame data for the follow-up move to the dataframe
            data_for_move = pandas.concat([data_for_move, data_to_add])

    # return the dataframe with the move data
    return data_for_move


def find_generic_move_data(
    move_name: str,
    full_framedata_df: pandas.DataFrame,
    generic_move_name_regex: str,
    character_name: str,
) -> pandas.DataFrame:
    """Attempt to find a generic form of the move name in the frame data dataframe

    Args:
        move_name (str): Move name
        full_framedata_df (pandas.DataFrame): Frame data dataframe
        generic_move_name_regex (str): Regex to find generic move name
        character_name (str): Character name

    Returns:
        pandas.DataFrame: Dataframe with move data, or empty dataframe if move not found
    """

    match: re.Match[str] | None = re.search(
        generic_move_name_regex, move_name, flags=re.IGNORECASE
    )

    # if the generic move name is found
    if match:
        # get the generic move name
        generic_move_name: str = match.group(1) + match.group(3)

        # search for the generic move name in the frame data dataframe
        logger.debug(f"Data for move [{move_name}] found as [{generic_move_name}]")
        data_for_move: pandas.DataFrame = find_move_from_name_and_character(
            generic_move_name, character_name, full_framedata_df
        )
    else:
        data_for_move = pandas.DataFrame()

    return data_for_move


def find_alias_move_data(
    move_name: str,
    full_framedata_df: pandas.DataFrame,
    character_name: str,
    move_name_alias_df: pandas.DataFrame,
) -> pandas.DataFrame:
    """Attempt to find the alias move name in the frame data dataframe

    Args:
        move_name (str): Move name
        full_framedata_df (pandas.DataFrame): Frame data dataframe
        character_name (str): Character name
        move_name_alias_df (pandas.DataFrame): Dataframe with move name aliases

    Returns:
        pandas.DataFrame: Dataframe with move data, or empty dataframe if move not found
    """
    move_name_alias: str = get_alias_move(move_name, move_name_alias_df)

    # if the alias move name is not empty, get the frame data for the alias move name
    if move_name_alias != "":
        logger.debug(f"Alias for [{move_name}] found as [{move_name_alias}]")
        data_for_move: pandas.DataFrame = find_move_from_name_and_character(
            move_name_alias, character_name, full_framedata_df
        )
    else:
        data_for_move = pandas.DataFrame()

    return data_for_move


def find_repeat_move_data(
    move_name: str,
    full_framedata_df: pandas.DataFrame,
    repeat_moves_regex: str,
    repeat_search: re.Match[str] | None,
    character_name: str,
) -> pandas.DataFrame:
    """Attempt to find the frame data for a repeat move, e.g. 5MKx2

    Args:
        move_name (str): Move name
        full_framedata_df (pandas.DataFrame): Frame data dataframe
        repeat_moves_regex (str): Regex to find repeat moves
        repeat_search (re.Match[str] | None): Match object for the repeat move
        character_name (str): Character name

    Returns:
        pandas.DataFrame: Dataframe with move data, or empty dataframe if move not found
    """

    move_name_without_repeat_count: str = re.sub(repeat_moves_regex, "", move_name)

    # get the frame data for the move without the repeat count
    data_for_move_without_repeat_count: pandas.DataFrame = (
        find_move_from_name_and_character(
            move_name_without_repeat_count, character_name, full_framedata_df
        )
    )

    if data_for_move_without_repeat_count is not None:
        data_for_move: pandas.DataFrame = data_for_move_without_repeat_count
        # if the move without the repeat count is found, get next x normals in the sequence where x is the repeat count -1
        # eg if the move is 5HPx3, get the frame data for 5HP, then get the frame data for 5HPx2 and 5HPx3
        logger.debug(f"Found data for move [{move_name_without_repeat_count}]")
        for i in range(int(repeat_search.group(1)) - 1) if repeat_search else range(0):
            temp_move_name: str = move_name_without_repeat_count + "X" + str(i + 2)
            temp_move_data: pandas.DataFrame = find_move_from_name_and_character(
                temp_move_name, character_name, full_framedata_df
            )

            data_for_move = pandas.concat(
                [data_for_move, temp_move_data],
                ignore_index=True,
            )
    else:
        data_for_move = pandas.DataFrame()

    return data_for_move


def find_base_move_data_for_followup_move(
    move_name: str,
    full_framedata_df: pandas.DataFrame,
    follow_up_move_search: re.Match[str],
    character_name: str,
) -> tuple[pandas.DataFrame, str]:
    """Attempt to find the frame data for a follow-up move, e.g. 214MKx2

    Args:
        move_name (str): Move name
        full_framedata_df (pandas.DataFrame): Frame data dataframe
        follow_up_move_search (re.Match[str]): Match object for the follow-up move
        character_name (str): Character name

    Returns:
        tuple[pandas.DataFrame, str]: Dataframe with move data, or empty dataframe if move not found, and the name of the base move
    """
    # if the move is a follow-up move, get the frame data for the follow-up move and return the name of the base move and the frame data for the follow-up move
    base_move_name: str = follow_up_move_search.group(1)
    data_for_move: pandas.DataFrame = find_move_from_name_and_character(
        move_name, character_name, full_framedata_df
    )

    return data_for_move, base_move_name


def get_alias_move(move_name: str, move_name_alias_df: pandas.DataFrame) -> str:
    """Get the alias move name for the given move name

    Args:
        move_name (str): Move name
        move_name_alias_df (pandas.DataFrame): Dataframe with move name aliases

    Returns:
        str: Alias move name, or empty string if no alias found
    """

    # get all move name aliases that contain the given move name
    alias_df = move_name_alias_df[
        move_name_alias_df["Value"].str.contains(
            move_name, na=False, flags=re.IGNORECASE
        )
    ]

    # return the alias if it exists
    return alias_df["Key"].iloc[0] if not alias_df.empty else ""


def get_frame_data_for_combo(
    combo_df: pandas.DataFrame,
    full_framedata_df: pandas.DataFrame,
    move_name_alias_df: pandas.DataFrame,
) -> pandas.DataFrame:
    """Get the frame data for a combo

    Args:
        combo_df (pandas.DataFrame): Combo dataframe
        full_framedata_df (pandas.DataFrame): Frame data dataframe
        move_name_alias_df (pandas.DataFrame): Dataframe with move name aliases

    Returns:
        pandas.DataFrame: Dataframe with combo frame data
    """

    # get the character name from the combo pandas.DataFrame

    character_name: str = combo_df[const.CHARACTER_NAME_COLUMN].iloc[0]

    # initialize an empty frame data pandas.DataFrame
    combo_framedata_df: pandas.DataFrame = pandas.DataFrame(
        columns=full_framedata_df.columns
    )

    # get the combo moves from the given combo pandas.DataFrame
    combo_moves: pandas.Series = combo_df[const.MOVE_NAME_COLUMN]

    # get the frame data for all moves in the combo by looping through the moves
    for move in combo_moves:
        move_framedata: pandas.DataFrame = get_frame_data_for_move(
            move, full_framedata_df, character_name, move_name_alias_df
        )

        # append the move frame data to the temporary frame data pandas.DataFrame
        combo_framedata_df = pandas.concat(
            [combo_framedata_df, move_framedata], ignore_index=True
        )

    return combo_framedata_df


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
        columns=[const.MOVE_NAME_COLUMN, "Damage", "Chip", "Special"]
    )

    for movestr in combo_frame_data_df[const.MOVE_NAME_COLUMN]:
        # find a way to keep track of the cell that is being parsed

        # Get the series for the current move
        move_series: pandas.Series = combo_frame_data_df.loc[
            combo_frame_data_df[const.MOVE_NAME_COLUMN] == movestr
        ]

        # If the move is a kara, set the damage of the previous move to 0
        if movestr == "kara":
            logger.debug("Kara cancel detected, setting damage of previous move to 0")
            # get the location of the move 1 row above the current move
            previous_move_location: int = combo_frame_data_df.index[
                combo_frame_data_df[const.MOVE_NAME_COLUMN] == movestr
            ][0]
            # set the damage of the previous move to 0
            combo_frame_data_df.loc[previous_move_location, "Damage"] = 0
            continue

        # If the move does not have any damage, continue to the next move
        if move_series["Damage"].isnull().values.any():
            logger.debug(f"Move [{movestr}] does not have any damage")
            continue
        # Initialize the lists for the damage, chip, and special properties of the move
        move_chip: list[str] = []
        move_special: list[str] = []

        # Get the damage list for the current move
        currentmove_damagestr: str = move_series["Damage"].iloc[0]

        # Extract the chip properties from the damage list and remove them from the list
        move_chip, currentmove_damagestr = extract_values_from_parentheses(
            move_chip, currentmove_damagestr
        )
        # Extract the special properties from the damage list and remove them from the list
        move_special, currentmove_damagestr = extract_values_from_brackets(
            move_special, currentmove_damagestr
        )

        # Initialize the list of the damage done by the move
        currentmove_damagelist: list = currentmove_damagestr.split(",")

        # clean the damage list and extract the damage, adding a row to the hits dataframe for each hit
        hits_df = clean_and_extract_damage(hits_df, movestr, currentmove_damagelist)

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
    for _, string in enumerate(dmg_list):
        # if the string is empty, skip it
        if string == "":
            continue
            # remove whitespace
        string = re.sub(r"\s", "", string)
        if string == "":
            continue
            # search for a match to the regex pattern for the number of hits and damage
        numhits_result: re.Match[str] | None = re.search(num_hits_regex, string)
        # if the regex pattern is found, extract the damage and number of hits
        if numhits_result:
            numhits: int = int(numhits_result.group(2))
            hitdmg: int = int(numhits_result.group(1))
            # add the damage for each hit to the move's damage list
            for _ in range(numhits):
                move_dmg.append(hitdmg)
                # add the damage to a temporary pandas.DataFrame
                temp_df: pandas.DataFrame = pandas.DataFrame(
                    [[move, hitdmg, None, None]],
                    columns=output_df.columns,
                )
                # append the temporary pandas.DataFrame to the hits pandas.DataFrame
                output_df = pandas.concat([output_df, temp_df], ignore_index=True)

            # if the regex pattern is not found and the string is not empty, add it directly to the move's damage list
        if string != "" and not re.search(num_hits_regex, string):
            move_dmg.append(int(string))
            # add the damage to a temporary pandas.DataFrame
            temp_df = pandas.DataFrame(
                [[move, string, None, None]],
                columns=output_df.columns,
            )
            # append the temporary pandas.DataFrame to the hits pandas.DataFrame
            output_df = pandas.concat([output_df, temp_df], ignore_index=True)
        logger.info(f"moveDamage: {move_dmg}")
    return output_df


def extract_values_from_brackets(lst: list[str], string: str) -> tuple[list[str], str]:
    """Extracts values from a string surrounded by square brackets and removes them from the string

    Args:
        lst (list[str]): list of strings, extracted values will be appended to this list
        string (str): string to search for values

    Returns:
        tuple[list[str], str]: tuple containing the list of extracted values and the string with the values removed
    """
    return_string: str = string
    # Define the regex pattern to search for
    bracket_regex: str = r"\[.+\]"
    # Search for the regex pattern in the string
    if re.search(bracket_regex, string):
        # If found, return a Match object
        r: re.Match[str] | None = re.search(bracket_regex, string)
        # Append the match to the list
        if r:
            lst.append(r.group(0))
        # Remove the regex pattern from the string
        return_string = re.sub(bracket_regex, "", string)
        # Log the list and string
        logger.debug(lst)
        logger.debug(return_string)
    # Return the string
    return lst, return_string


def extract_values_from_parentheses(
    lst: list[str], string: str
) -> tuple[list[str], str]:
    """Extracts values from a string surrounded by parentheses and removes them from the string

    Args:
        lst (list[str]): list of strings, extracted values will be appended to this list
        string (str): string to search for values

    Returns:
        tuple[list[str], str]: tuple containing the list of extracted values and the string with the values removed
    """
    return_string: str = string
    # define regex for parentheses
    parentheses_regex: str = r"\(.+\)"
    # check if regex is found in string
    if re.search(parentheses_regex, string):
        # assign match to variable
        r: re.Match[str] | None = re.search(parentheses_regex, string)
        # append string inside parentheses to list
        if r:
            lst.append(r.group(0))
        # remove parentheses and string from string
        return_string = re.sub(parentheses_regex, "", string)
        logger.debug(lst)
        logger.debug(return_string)
    return lst, return_string
