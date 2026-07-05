# EUKARYOME

EUKARYOME is a eukaryote-wide rRNA reference database (SSU, LSU, ITS, longread).
Releases are published as static archives, so biodbs builds the download URL from
the marker and version — there is no listing to browse.

## Download a Marker Archive

```python
from biodbs.fetch.EUKARYOME import EUKARYOME_Fetcher, MARKERS

print(MARKERS)  # ('SSU', 'LSU', 'ITS', 'longread')

fetcher = EUKARYOME_Fetcher()
path = fetcher.download("SSU", dest="data/eukaryome")            # latest default version
path = fetcher.download("ITS", dest="data/eukaryome", version="2.0")
```

Markers are case-insensitive. Existing files are kept by default. Some archives
contain a **nested 7z** that must be extracted separately (7z is not in the Python
standard library).

## Just the URL

```python
url = fetcher.build_url("LSU", version="2.0")
```

## Convenience Functions

```python
from biodbs.fetch import eukaryome_download, eukaryome_build_url

path = eukaryome_download("SSU", dest="data/eukaryome")
url = eukaryome_build_url("ITS")
```
