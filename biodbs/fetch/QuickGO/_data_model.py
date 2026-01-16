from enum import Enum
from pathlib import Path
import re
import yaml
from pydantic import BaseModel, model_validator, ConfigDict, ValidationError
from typing import Dict, Any, Optional


class QuickGOCategory(Enum):
    ontology = "ontology"
    annotation = "annotation"
    geneproduct = "geneproduct"