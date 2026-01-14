
from enum import Enum
from pydantic import BaseModel, model_validator, ConfigDict



class FDACategory(Enum):
    drug = "drug"
    food = "food"
    cosmetic = "cosmetic"


class FDADrugEndpoint(Enum):
    event = "event"
    

class FDAFoodEndpoint(Enum):
    event = "event"



VALID_ENDPOINTS = {FDACategory("drug"): FDADrugEndpoint,
                   FDACategory("food"): FDAFoodEndpoint}


class FDAModel(BaseModel):

    model_config = ConfigDict(use_enum_values=True)
    category: FDACategory
    endpoint: FDADrugEndpoint | FDAFoodEndpoint

    @model_validator(mode='after')
    def check_valid_endpoint(self):
        valid_endpoints = VALID_ENDPOINTS[FDACategory(self.category)]
        valid_values = [val.value for val in valid_endpoints]
        if self.endpoint not in valid_values:
            raise ValueError(f"{self.endpoint} is not a valid endpoint for {self.category}. Please choose from {valid_values}")
        return self
    

if __name__ == "__main__":
    valid_model = FDAModel(category="drug", endpoint="event")

    print(valid_model)
    print(valid_model.model_dump())