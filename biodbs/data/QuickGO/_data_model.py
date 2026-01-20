from enum import Enum
from pathlib import Path
import re
from pydantic import BaseModel, model_validator, ConfigDict, ValidationError
from typing import Dict, Any, Optional


class QuickGOCategory(Enum):
    ontology = "ontology"
    annotation = "annotation"
    geneproduct = "geneproduct"


class QuickGOOntologyEndpoint(Enum):
    go_about = "go/about"
    go_search = "go/search"
    go_terms = "go/terms"
    go_slim = "go/slim"
    go_terms_graph = "go/terms/graph"
    go_terms_ids = "go/terms/{ids}"
    go_terms_ancestors = "go/terms/{ids}/ancestors"
    go_terms_descendants = "go/terms/{ids}/descendants"


class QuickGOModel(BaseModel):
    category: QuickGOCategory
    endpoint: str

    model_config = ConfigDict(arbitrary_types_allowed=True)