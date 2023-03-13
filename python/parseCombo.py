"""Functions for parsing the combo data from the csv files"""
import os
import typing
from typing import Any
import re
import constants as const
from constants import logger
from pandas import DataFrame, Series
import pandas as pd


# flake8: noqa: E501
def get_csv_list(path: str) -> list[str]:
    """Returns a list of all csv files in a given path with their relative path"""
    return [os.path.join(path, f) for f in os.listdir(path) if f.endswith(".csv")]


def split_columns(df: DataFrame, column_name: str, seperator: str) -> DataFrame:
    """Split a column into multiple rows based on a given seperator"""
    splitdf: DataFrame = df.copy()
    # split the values in a column on a given seperator
    logger.debug(f'Splitting {column_name} on "{seperator}"')
    splitdf[column_name] = splitdf[column_name].str.split(seperator)
    # explode the column so that each value is on a row
    splitdf = splitdf.explode(column_name)
    return splitdf


def handle_annie_divekick(move_name: str, frame_data: DataFrame) -> DataFrame:
    """Logic for handling Annie's divekick moves"""
    data_for_move: DataFrame = DataFrame()
    divekick_move_name: str = re.sub(r"[LMH]", "", move_name)

    divekick_df: DataFrame = frame_data.loc[
        frame_data[const.MOVE_NAME].str.contains(const.ANNIE_DIVEKICK, na=False)
    ].reset_index(drop=True)

    divekick_check: Series[bool] = divekick_df[const.MOVE_NAME].str.contains(
        divekick_move_name, flags=re.IGNORECASE, na=False
    )

    if not divekick_check.any():
        divekick_check = divekick_df[const.ALT_NAMES].str.contains(
            divekick_move_name, flags=re.IGNORECASE, na=False
        )

    if divekick_check.any():
        divekick_count_check: re.Match[str] | None = re.search(
            r"x\s?(\d)|[~\s,]", divekick_move_name, flags=re.IGNORECASE
        )

        if divekick_count_check:
            divekick_count: int = (
                int(divekick_count_check.group(1))
                if divekick_count_check.group(1)
                else (divekick_count_check.end() - divekick_count_check.start() + 1)
            )
        else:
            divekick_count: int = 1

        global annie_divekick_count
        previous_divekick_count: int = annie_divekick_count
        annie_divekick_count += divekick_count

        data_for_move = divekick_df[
            divekick_df.index.isin(range(previous_divekick_count, annie_divekick_count))
        ].reset_index(drop=True)
    return data_for_move


def character_specific_move_data(
    move_name: str,
    character_name: str,
    frame_data: DataFrame,
    move_name_alias_df: DataFrame,
) -> DataFrame:
    """Check for and handle character specific move data"""
    data_for_move: DataFrame = DataFrame()

    # check if the move name has a character specific version
    # Most common variations of the move are j236HK or j236MK~HK
    match character_name:
        case "Annie":
            divekick_first_check_regex: re.Pattern[str] = re.compile(
                r"j?236[LMH]?K", re.IGNORECASE
            )

            divekick_first_check: re.Match[str] | None = re.search(
                divekick_first_check_regex, move_name
            )

            alias_move: str = find_move_alias(move_name_alias_df, move_name)

            if divekick_first_check:
                if alias_move:
                    move_name = alias_move
                    # remove any LMH from the move name
                data_for_move = handle_annie_divekick(move_name, frame_data)
                return data_for_move

        case _:
            return data_for_move

    return data_for_move


def find_move_from_name_and_character(
    move_name: str,
    character_name: str,
    frame_data: DataFrame,
    check_aliases: bool = False,
    move_name_alias_df: DataFrame = DataFrame(),
) -> DataFrame:
    """Find a move from the move name and character name"""
    # replace regex characters with escaped versions
    move_name_escaped: str = re.sub(r"([\\^$*+?.()|{}[\]])", r"\\\1", move_name)
    if check_aliases and not move_name_alias_df.empty:
        move_name_escaped = find_move_alias(move_name_alias_df, move_name_escaped)

    name_regex: str = rf"^{move_name_escaped}$|^{move_name_escaped}\n|\n{move_name_escaped}$|\n{move_name_escaped}\n"
    character_check: Series[bool] = frame_data[const.CHARACTER_NAME].str.contains(
        character_name, flags=re.IGNORECASE
    )
    character_df: DataFrame = frame_data[character_check][
        [const.MOVE_NAME, const.ALT_NAMES]
    ]

    move_df: DataFrame = character_df[
        character_df[const.MOVE_NAME].str.contains(name_regex, flags=re.IGNORECASE)
    ]
    if move_df.empty:
        move_df = character_df[
            character_df[const.ALT_NAMES].str.contains(name_regex, flags=re.IGNORECASE)
        ]

    move_data: DataFrame = frame_data.loc[move_df.index]
    return move_data


def find_move_alias(move_name_alias_df: DataFrame, move_name_escaped: str) -> str:
    """Attempt to find an alias for a move"""
    alias_move: str
    alias_regex: str = rf"^{move_name_escaped}$|^{move_name_escaped}\n|\n{move_name_escaped}$|\n{move_name_escaped}\n"
    alias_search: Series[bool] = move_name_alias_df["Value"].str.contains(
        alias_regex, regex=True, flags=re.IGNORECASE, na=False
    )
    if alias_search.any():
        # Get the key for the alias
        alias_move = move_name_alias_df["Key"][alias_search].iloc[0]
        logger.debug(f"Found alias for move [{move_name_escaped}]: [{alias_move}]")
    else:
        alias_move = ""
    return alias_move


def get_frame_data_for_move(
    move_name: str,
    full_framedata_df: DataFrame,
    character_name: str,
    move_name_alias_df: DataFrame,
) -> DataFrame:
    """Get the frame data for a single move, given a move name and a dataframe"""

    logger.debug(f"===========Getting frame data for move [{move_name}]===========")
    # check for follow-up moves such as 214HP~P or QCBLP P or 214 MP,P etc
    # regex that matches L, M or H, followed by P or K followed by "~", ",", "+" or " " followed by P or K

    search_state: str | None = list(const.SEARCH_STATES.keys())[0]
    data_for_move: DataFrame = DataFrame()
    searches_performed: dict[str, bool] = const.SEARCH_STATES.copy()

    while search_state:
        match search_state:
            case "character_specific":
                data_for_move: DataFrame = character_specific_move_data(
                    move_name, character_name, full_framedata_df, move_name_alias_df
                )
            case "repeat":
                repeat_moves_regex: str = r"\s?[Xx]\s?(\d+)$"
                repeat_search: re.Match[str] | None = re.search(
                    repeat_moves_regex, move_name, re.IGNORECASE
                )
                if repeat_search:
                    logger.debug(f"Move [{move_name}] is a repeat move")
                    data_for_move = find_repeat_move_data(
                        move_name,
                        full_framedata_df,
                        repeat_moves_regex,
                        repeat_search,
                        character_name,
                    )
            case "start":
                data_for_move: DataFrame = find_move_from_name_and_character(
                    move_name, character_name, full_framedata_df
                )

            case "follow_up":
                follow_up_move_regex: str = r"(.+[lmh]?[pk])([~\+,\s]){1,3}([pk])"
                follow_up_move_search: re.Match[str] | None = re.search(
                    follow_up_move_regex, move_name, re.IGNORECASE
                )

                if follow_up_move_search:
                    logger.debug(f"Move [{move_name}] is a follow-up move")

                    data_to_add: DataFrame = find_base_move_data_for_followup_move(
                        full_framedata_df,
                        follow_up_move_search,
                        character_name,
                        move_name_alias_df,
                    )

                    data_for_move: DataFrame = pd.concat([data_to_add, data_for_move])
            case "alias":
                logger.debug("Move name not found, checking aliases")
                data_for_move = find_move_from_name_and_character(
                    move_name,
                    character_name,
                    full_framedata_df,
                    True,
                    move_name_alias_df,
                )
            case "generic":
                generic_move_name_regex: str = r"(.*?)([lmh])([pk])"
                generic_search: re.Match[str] | None = re.search(
                    generic_move_name_regex, move_name
                )
                if generic_search:
                    data_for_move = find_generic_move_data(
                        move_name,
                        full_framedata_df,
                        generic_move_name_regex,
                        character_name,
                    )
            case "no_strength":
                # Check for omission of move strength (e.g. 214MKx2 -> 214Kx2)
                data_for_move = find_move_no_strength_specified(
                    move_name, full_framedata_df, character_name, move_name_alias_df
                )

            case "found":
                logger.debug("Found move")
                search_state = None
                return data_for_move
            case "not_found":
                logger.warning(
                    f"Move [{move_name}] not found for character [{character_name}]"
                )
                search_state = None
                return DataFrame()
            case _:
                search_state = "not_found"

        search_state, searches_performed = update_search_state(
            search_state, data_for_move, searches_performed
        )
    return data_for_move


def update_search_state(
    search_state: str, data_for_move: DataFrame, searches_performed: dict[str, bool]
) -> tuple[str, dict[str, bool]]:
    """Update the search state, setting it to the next state that has not been performed
    Update the searches performed dictionary to reflect the current search state"""
    new_searches_performed: dict[str, bool] = searches_performed.copy()
    new_searches_performed[search_state] = True
    new_search_state = search_state
    if not data_for_move.empty and search_state != "start":
        new_search_state = "found"
        return new_search_state, new_searches_performed
    # Set the search state to the next state that has not been performed

    elif search_state == "no_strength":
        # Reset search state to start
        new_search_state: str = "start"
        new_searches_performed: dict[str, bool] = const.SEARCH_STATES.copy()
        new_searches_performed["no_strength"] = True
        return new_search_state, new_searches_performed
    else:
        for state in const.SEARCH_STATES:
            if not new_searches_performed[state]:
                new_search_state: str = state
                break
    return new_search_state, new_searches_performed


def find_move_no_strength_specified(
    move_name: str,
    full_framedata_df: DataFrame,
    character_name: str,
    move_name_alias_df: DataFrame,
) -> DataFrame:
    """Check for omission of move strength (e.g. 214K -> 214MK)
    returns a dataframe of the frame data for the move if it exists, otherwise an empty dataframe
    by default, the move strength is assumed to be the highest strength available for the move
    """
    possible_move_data: DataFrame = DataFrame()
    strength_regex: str = r"(.*)([lmh])?([pk])[\s,~+Xx].*"
    strength_search: re.Match[str] | None = re.search(
        strength_regex, move_name, re.IGNORECASE
    )
    # if group 1 is empty but group 2 is not, then the move strength was omitted
    if strength_search and not strength_search.group(2) and strength_search.group(3):
        # Find possible matches for each strength
        for strength in ["L", "M", "H"]:
            possible_base_move_name: str = (
                f"{strength_search.group(1)}{strength}{strength_search.group(3)}"
            )
            # append the frame data for the possible base move to the list if it exists

            possible_move: DataFrame = find_move_from_name_and_character(
                possible_base_move_name, character_name, full_framedata_df
            )
            if possible_move.empty:
                possible_move = find_move_from_name_and_character(
                    possible_base_move_name,
                    character_name,
                    full_framedata_df,
                    True,
                    move_name_alias_df,
                )
            if not possible_move.empty:
                possible_move_data = pd.concat([possible_move_data, possible_move])

        if not possible_move_data.empty:
            logger.debug(f"Found {len(possible_move_data)} possible base moves")
            # add the highest strength version of the move to the data
            data_for_base_move: DataFrame = possible_move_data.tail(1)
            logger.debug(
                f"Adding highest strength version {data_for_base_move[const.MOVE_NAME].iloc[0]}"
            )
            return data_for_base_move

    return DataFrame()


def find_generic_move_data(
    move_name: str,
    full_framedata_df: DataFrame,
    generic_move_name_regex: str,
    character_name: str,
) -> DataFrame:
    """Attempt to find a generic form of the move name in the frame data dataframe"""

    match: re.Match[str] | None = re.search(
        generic_move_name_regex, move_name, flags=re.IGNORECASE
    )

    # if the generic move name is found
    if match:
        # get the generic move name
        generic_move_name: str = match.group(1) + match.group(3)

        # search for the generic move name in the frame data dataframe
        logger.debug(f"Data for move [{move_name}] found as [{generic_move_name}]")
        data_for_move: DataFrame = find_move_from_name_and_character(
            generic_move_name, character_name, full_framedata_df
        )
    else:
        data_for_move = DataFrame()

    return data_for_move


def find_repeat_move_data(
    move_name: str,
    full_framedata_df: DataFrame,
    repeat_moves_regex: str,
    repeat_search: re.Match[str] | None,
    character_name: str,
) -> DataFrame:
    """Attempt to find the frame data for a repeat move, e.g. 5MKx2"""

    move_name_without_repeat_count: str = re.sub(repeat_moves_regex, "", move_name)
    logger.debug(f"Move name without repeat count [{move_name_without_repeat_count}]")

    # get the frame data for the move without the repeat count
    data_for_move_without_repeat_count: DataFrame = find_move_from_name_and_character(
        move_name_without_repeat_count, character_name, full_framedata_df
    )

    if not data_for_move_without_repeat_count.empty:
        data_for_move: DataFrame = data_for_move_without_repeat_count
        # if the move without the repeat count is found, get next x normals in the sequence where x is the repeat count -1
        # eg if the move is 5HPx3, get the frame data for 5HP, then get the frame data for 5HPx2 and 5HPx3
        # first index is column 0 of data_for_move

        logger.debug(f"Found data for move [{move_name_without_repeat_count}]")

        for i in range(int(repeat_search.group(1)) - 1) if repeat_search else range(0):
            base_move_index: int = full_framedata_df.index[
                full_framedata_df[const.MOVE_NAME] == move_name_without_repeat_count
            ].tolist()[0]

            next_move_in_sequence: Series[Any] = full_framedata_df.iloc[
                1 + i + base_move_index
            ]
            logger.debug(f"Next move: {next_move_in_sequence[const.MOVE_NAME]}")
            data_for_move = pd.concat(
                [data_for_move, next_move_in_sequence.to_frame().T]
            )
    else:
        logger.warning(f"Could not find repeat data for move [{move_name}]")
        data_for_move = DataFrame()

    return data_for_move


def find_base_move_data_for_followup_move(
    full_framedata_df: DataFrame,
    follow_up_move_search: re.Match[str],
    character_name: str,
    move_name_alias_df: DataFrame,
) -> DataFrame:
    """Attempt to find the frame data for a follow-up move, e.g. 214MKx2"""
    # if the move is a follow-up move, get the frame data for the follow-up move and return the name of the base move and the frame data for the follow-up move
    base_move_name: str = follow_up_move_search.group(1)
    data_for_base_move: DataFrame = find_move_from_name_and_character(
        base_move_name, character_name, full_framedata_df, True, move_name_alias_df
    )

    if data_for_base_move.empty:
        logger.warning(
            f"Could not find base move data for follow-up move [{base_move_name}]"
        )

    return data_for_base_move


def get_frame_data_for_combo(
    combo_df: DataFrame,
    full_framedata_df: DataFrame,
    move_name_alias_df: DataFrame,
) -> DataFrame:
    """Get the frame data for a combo"""

    # get the character name from the combo DataFrame

    # Combo globals
    global annie_divekick_count
    annie_divekick_count = 0

    character_name: str = combo_df[const.CHARACTER_NAME].iloc[0]

    # initialize an empty frame data DataFrame
    combo_framedata_df: DataFrame = DataFrame(columns=full_framedata_df.columns)

    # get the combo moves from the given combo DataFrame
    combo_moves: Series[typing.Any] = combo_df[const.MOVE_NAME]

    # get the frame data for all moves in the combo by looping through the moves
    for move in combo_moves:
        if isinstance(move, float):
            logger.debug(
                f"Move [{move}] is not a string, skipping it as it is not a move"
            )
            continue

        # Check against automatically ignored moves
        # Case insensitive
        if move.lower() in const.IGNORED_MOVES:
            logger.debug(f"Ignoring move [{move}], it is in the ignored moves list")
            continue

        if move.lower() == "kara":
            logger.debug(
                "Move name is kara, assuming previous move was kara cancelled so removing it from the combo"
            )
            logger.debug(
                f"Move removed: {combo_framedata_df.iloc[-1][const.MOVE_NAME]}"
            )
            # If the move is kara, assume the previous move was kara cancelled and remove it from the combo
            combo_framedata_df = combo_framedata_df.iloc[:-1]

            continue

        move_framedata: DataFrame = get_frame_data_for_move(
            move, full_framedata_df, character_name, move_name_alias_df
        )

        # append the move frame data to the temporary frame data DataFrame
        combo_framedata_df = pd.concat(
            [combo_framedata_df, move_framedata], ignore_index=True
        )

    return combo_framedata_df


def parse_hits(combo_frame_data_df: DataFrame) -> DataFrame:
    """Parse the hits from the combo frame data dataframe."""
    # Set up the regex to find the number of hits in a move

    # Set up the dataframe for the hits
    hits_df: DataFrame = DataFrame(
        columns=[const.MOVE_NAME, "Damage", "Chip", "Special"]
    )
    movestr: str
    for movestr in combo_frame_data_df[const.MOVE_NAME]:
        # find a way to keep track of the cell that is being parsed

        # Get the series for the current move
        move_series: Series[typing.Any] = combo_frame_data_df.loc[
            combo_frame_data_df[const.MOVE_NAME] == movestr
        ].iloc[0]

        # If the move does not have any damage, continue to the next move
        if (
            move_series["Damage"] == "0"
            or move_series["Damage"] == ""
            or move_series["Damage"] == None
        ):
            logger.debug(f"Move [{movestr}] does not have any damage")
            continue
        # Initialize the lists for the damage, chip, and special properties of the move
        move_chip: list[str] = []
        move_special: list[str] = []

        # Get the damage list for the current move
        currentmove_damagestr: str = move_series["Damage"]

        # Extract the chip properties from the damage list and remove them from the list
        move_chip, currentmove_damagestr = extract_values_from_parentheses(
            move_chip, currentmove_damagestr
        )
        # Extract the special properties from the damage list and remove them from the list
        move_special, currentmove_damagestr = extract_values_from_brackets(
            move_special, currentmove_damagestr
        )

        # Initialize the list of the damage done by the move
        currentmove_damagelist: list[str] = currentmove_damagestr.split(",")

        # clean the damage list and extract the damage, adding a row to the hits dataframe for each hit
        hits_df = clean_and_extract_damage(hits_df, movestr, currentmove_damagelist)

    return hits_df


def clean_and_extract_damage(
    hits_df: DataFrame,
    move: str,
    dmg_list: list[str],
) -> DataFrame:
    """Cleans the damage list and extracts the damage, adding a row to the hits dataframe for each hit"""

    output_df: DataFrame = hits_df
    # Set up the regex to find the number of hits in a move
    num_hits_regex: str = r"(\d+)x(\d+)$"
    move_dmg: list[int] = []
    # for every element in the list of the move's damage values
    for _, string in enumerate(dmg_list):
        # if the string is empty, skip it
        if string == "":
            continue
            # remove whitespace
        string: str = re.sub(r"\s", "", string)
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
                # add the damage to a temporary DataFrame
                temp_df: DataFrame = DataFrame(
                    [[move, hitdmg, None, None]],
                    columns=output_df.columns,
                )
                # append the temporary DataFrame to the hits DataFrame
                output_df = pd.concat([output_df, temp_df], ignore_index=True)

            # if the regex pattern is not found and the string is not empty, add it directly to the move's damage list
        if string != "" and not re.search(num_hits_regex, string):
            move_dmg.append(int(string))
            # add the damage to a temporary DataFrame
            temp_df = DataFrame(
                [[move, string, None, None]],
                columns=output_df.columns,
            )
            # append the temporary DataFrame to the hits DataFrame
            output_df = pd.concat([output_df, temp_df], ignore_index=True)
    return output_df


def extract_values_from_brackets(lst: list[str], string: str) -> tuple[list[str], str]:
    """Extracts values from a string surrounded by square brackets and removes them from the string"""
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
    # Return the string
    return lst, return_string


def extract_values_from_parentheses(
    lst: list[str], string: str
) -> tuple[list[str], str]:
    """Extracts values from a string surrounded by parentheses and removes them from the string"""
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
    return lst, return_string
