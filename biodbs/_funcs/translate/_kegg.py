"""Shared KEGG conversion behavior for gene and chemical translators."""

import pandas as pd


def convert_kegg(ids, from_db, to_db, convert, *, bulk=False, return_dict=False):
    """Keep KEGG prefixes and one-to-many rows; bulk queries are explicit."""
    if not ids and not bulk:
        frame = pd.DataFrame(columns=["source_id", "target_id"])
    else:
        frame = convert(target_db=to_db, source=ids if ids else from_db).as_dataframe()
    if return_dict:
        # Match existing scalar dictionary semantics: keep the first mapping.
        return dict(frame.drop_duplicates("source_id").loc[:, ["source_id", "target_id"]]
                    .itertuples(index=False, name=None))
    return frame
