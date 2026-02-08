# FDA

Access drug and device data via the [openFDA API](https://open.fda.gov/).

## Overview

openFDA provides access to:

- **Drug Events** - Adverse event reports
- **Drug Labels** - Drug labeling information
- **Drug Enforcement** - Recalls and enforcement actions
- **Device Data** - Medical device reports

## Quick Start

```python
from biodbs.fetch import fda_drug_events, fda_drug_labels

# Search drug adverse events
events = fda_drug_events(search="aspirin", limit=10)
```

## Drug Data

### Adverse Events

```python
from biodbs.fetch import fda_drug_events

events = fda_drug_events(
    search="aspirin",
    limit=100
)
```

### Drug Labels

```python
from biodbs.fetch import fda_drug_labels

labels = fda_drug_labels(search="aspirin")
```

### Drug Enforcement

```python
from biodbs.fetch import fda_drug_enforcement

recalls = fda_drug_enforcement(search="aspirin")
```

### NDC Directory

```python
from biodbs.fetch import fda_drug_ndc

ndc = fda_drug_ndc(search="aspirin")
```

### Drugs@FDA

```python
from biodbs.fetch import fda_drug_drugsfda

drugs = fda_drug_drugsfda(search="aspirin")
```

## Device Data

### Device Events

```python
from biodbs.fetch import fda_device_events

events = fda_device_events(search="pacemaker", limit=10)
```

### Device Classification

```python
from biodbs.fetch import fda_device_classification

classification = fda_device_classification(search="pacemaker")
```

### 510(k) Clearances

```python
from biodbs.fetch import fda_device_510k

clearances = fda_device_510k(search="pacemaker")
```

## Food Data

### Food Events

```python
from biodbs.fetch import fda_food_events

events = fda_food_events(search="salmonella", limit=10)
```

### Food Enforcement

```python
from biodbs.fetch import fda_food_enforcement

recalls = fda_food_enforcement(search="salmonella")
```

## Generic Search

```python
from biodbs.fetch import fda_search, fda_search_all

# Single page
results = fda_search(
    endpoint="drug/event",
    search="aspirin",
    limit=100
)

# All pages
all_results = fda_search_all(
    endpoint="drug/event",
    search="aspirin",
    max_results=1000
)
```

## Using the Fetcher Class

```python
from biodbs.fetch.FDA import FDA_Fetcher

fetcher = FDA_Fetcher()
events = fetcher.drug_events(search="aspirin")
```

## Related Resources

- **[ChEMBL](chembl.md)** - Bioactivity data, mechanisms of action, and drug target information.
- **[PubChem](pubchem.md)** - Chemical properties, safety data, and pharmacology information.
