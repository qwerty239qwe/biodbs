import re
import xml.etree.ElementTree as ET
import pandas as pd
from functools import reduce


def xml_to_tabular(xml, tag=None, how="union"):
    """
    Convert XML data to a tabular format.

    Args:
        xml (str or Element): The XML data to be converted.
        tag (str, optional): The tag to filter the XML data. Defaults to None.
        how (str, optional): The method to combine attribute keys. Defaults to "union".

    Returns:
        pandas.DataFrame: The tabular representation of the XML data.
    """
    tree = ET.fromstring(xml) if not isinstance(xml, ET.Element) else xml
    child_keys = [set(ch.attrib.keys()) for ch in tree.iter(tag)]
    if len(child_keys) == 0:
        return pd.DataFrame({})
    to_gets = reduce(getattr(set, how), child_keys)
    data = {key: [ch.attrib.get(key) for ch in tree.iter(tag)] for key in to_gets}
    return pd.DataFrame(data)


def response_to_df(rsp, columns):
    return pd.DataFrame([r.split("\t") for r in rsp.text.splitlines()], columns=columns)


def find_contained_rows(df, contain, cols, ignore_case=True):
    contain = contain.lower() if ignore_case else contain
    boolean_dfs = [df[col].str.contains(contain, case=ignore_case)
                   for col in cols]
    return df.loc[reduce(lambda l, r: l | r, boolean_dfs)]


def find_matched_rows(df: pd.DataFrame,
                      pattern: str,
                      cols: list):
    """
    Find rows in a DataFrame that match a given pattern in specified columns.

    Parameters:
    - df (pandas.DataFrame): The DataFrame to search for matching rows.
    - pattern (str): The regular expression pattern to match.
    - cols (list): A list of column names in the DataFrame to search for matches.

    Returns:
    - pandas.DataFrame: A new DataFrame containing only the rows that match the pattern in the specified columns.

    Raises:
    - ValueError: If the provided pattern is invalid.

    Example:
    >>> df = pd.DataFrame({'A': ['apple', 'banana', 'cherry'], 'B': ['cat', 'dog', 'elephant']})
    >>> pattern = r'^[a-z]{5}$'
    >>> cols = ['A']
    >>> find_matched_rows(df, pattern, cols)
           A    B
    0  apple  cat
    1  banana  dog
    """
    try:
        boolean_dfs = [df[col].str.match(pattern)
                       for col in cols]
        return df.loc[reduce(lambda l, r: l | r, boolean_dfs)]
    except re.error as e:
        raise ValueError(f"Invalid regular expression: {pattern}") from e