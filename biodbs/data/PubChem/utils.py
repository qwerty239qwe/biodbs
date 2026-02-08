"""Utility functions for parsing PubChem PUG View hierarchical data."""

from typing import Union


def parse_cmp(cmp_dics: Union[list, dict]) -> dict:
    """Parse PUG View section hierarchy into a cleaner dict structure.

    Args:
        cmp_dics: List of section dictionaries with TOCHeading keys.

    Returns:
        Dictionary with headings as keys and nested content as values.
    """
    new_dic = {}

    for cmp_dic in cmp_dics:
        if "TOCHeading" in cmp_dic:
            new_key = cmp_dic["TOCHeading"]
            if "Section" in cmp_dic:
                new_val = parse_cmp(cmp_dic["Section"])
            elif "Information" in cmp_dic:
                new_val = parse_cmp(cmp_dic["Information"])
            else:
                raise ValueError()
            new_dic[new_key] = new_val
    if len(new_dic) == 0:
        return cmp_dics
    return new_dic


def _find_vals(val_dic):
    """Extract values from PUG View Value dictionaries.

    A helper function for clean_value().

    Args:
        val_dic: Dictionary containing Value data.

    Returns:
        Extracted value(s).
    """
    for k, v in val_dic.items():
        if isinstance(v, list):
            if isinstance(v[0], dict):
                return [val for vi in v for tp, val in vi.items() if tp not in ["Markup"]]
            else:
                return v
        else:
            return v


def clean_value(cmp_dic):
    """Clean PUG View data by removing metadata and flattening values.

    Removes values with ReferenceNumber, Description, and DisplayControls keys,
    flattens the values if it is a list with single value,
    and removes the data type indicators in the given dict.

    Args:
        cmp_dic: Dictionary or list from PUG View response.

    Returns:
        Cleaned dictionary with simplified structure.
    """
    new_dic = {}
    if isinstance(cmp_dic, list):
        found_val = [clean_value(v) for v in cmp_dic]
        return found_val if len(found_val) > 1 else found_val[0]

    if not isinstance(cmp_dic, dict):
        return cmp_dic

    if "Value" in cmp_dic and "Name" in cmp_dic:
        return {cmp_dic["Name"]: _find_vals(cmp_dic["Value"])}

    for k, v in cmp_dic.items():

        if k in ["ReferenceNumber", "Description", "DisplayControls"]:
            continue
        if k == "Value":
            found_val = _find_vals(v)
            return found_val[0] if (isinstance(found_val, list) and len(found_val) == 1) else found_val
        else:
            new_dic[k] = clean_value(v)
    return new_dic
