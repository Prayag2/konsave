"""
This module parses conf.yaml
"""
import os
import re
from konsave.consts import HOME, CONFIG_DIR, KONSAVE_DIR, PROFILES_DIR


def ends_with(grouped_regex, path) -> str:
    """Finds folder with name ending with the provided string.

    Args:
        grouped_regex: regex of the function
        path: path
    """
    occurence = re.search(grouped_regex, path).group()
    dirs = os.listdir(path[0 : path.find(occurence)])
    ends_with_text = re.search(grouped_regex, occurence).group(2)
    for directory in dirs:
        if directory.endswith(ends_with_text):
            return path.replace(occurence, directory)
    return occurence


def begins_with(grouped_regex, path) -> str:
    """Finds folder with name beginning with the provided string.

    Args:
        grouped_regex: regex of the function
        path: path
    """
    occurence = re.search(grouped_regex, path).group()
    dirs = os.listdir(path[0 : path.find(occurence)])
    ends_with_text = re.search(grouped_regex, occurence).group(2)
    for directory in dirs:
        if directory.startswith(ends_with_text):
            return path.replace(occurence, directory)
    return occurence


def parse_keywords(tokens_, token_symbol, parsed):
    """Replaces keywords with values in conf.yaml. For example, it will replace, $HOME with
    /home/username/

    Args:
        tokens_: the token dictionary
        token_symbol: TOKEN_SYMBOL
        parsed: the parsed conf.yaml file
    """
    for item in parsed:
        for name in parsed[item]:
            for key, value in tokens_["keywords"]["dict"].items():
                word = token_symbol + key
                location = parsed[item][name]["location"]
                if word in location:
                    parsed[item][name]["location"] = location.replace(word, value)


def parse_functions(tokens_, token_symbol, parsed):
    """Replaces functions with values in conf.yaml. For example, it will replace,
    ${ENDS_WITH='text'} with a folder whose name ends with "text"

    Args:
        tokens_: the token dictionary
        token_symbol: TOKEN_SYMBOL
        parsed: the parsed conf.yaml file
    """
    functions = tokens_["functions"]
    raw_regex = f"\\{token_symbol}{functions['raw_regex']}"
    grouped_regex = f"\\{token_symbol}{functions['grouped_regex']}"

    for item in parsed:
        for name in parsed[item]:
            location = parsed[item][name]["location"]
            occurences = re.findall(raw_regex, location)
            if not occurences:
                continue
            for occurence in occurences:
                func = re.search(grouped_regex, occurence).group(1)
                if func in functions["dict"]:
                    parsed[item][name]["location"] = functions["dict"][func](
                        grouped_regex, location
                    )


TOKEN_SYMBOL = "$"
tokens = {
    "keywords": {
        "dict": {
            "HOME": HOME,
            "CONFIG_DIR": CONFIG_DIR,
            "KONSAVE_DIR": KONSAVE_DIR,
            "PROFILES_DIR": PROFILES_DIR,
        }
    },
    "functions": {
        "raw_regex": r"\{\w+\=(?:\"|')\S+(?:\"|')\}",
        "grouped_regex": r"\{(\w+)\=(?:\"|')(\S+)(?:\"|')\}",
        "dict": {"ENDS_WITH": ends_with, "BEGINS_WITH": begins_with},
    },
}
