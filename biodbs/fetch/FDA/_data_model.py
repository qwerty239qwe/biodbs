from enum import Enum
from pathlib import Path
import re
import yaml
from pydantic import BaseModel, model_validator, ConfigDict
from typing import Dict, Any, Optional


def _load_field_rules(field_rule_file_name) -> Dict[str, Dict[str, Any]]:
    yaml_path = Path(__file__).parent / "field_rules" / field_rule_file_name
    with open(yaml_path, encoding="utf-8") as f:
        schema = yaml.safe_load(f)

    rules = {}

    def extract_rules(props: Dict, prefix: str = ""):
        for name, config in props.items():
            if not isinstance(config, dict):
                continue
            field_path = f"{prefix}{name}" if prefix else name
            field_type = config.get("type")

            if field_type == "object":
                if "properties" in config:
                    extract_rules(config["properties"], f"{field_path}.")
            elif field_type == "array":
                items = config.get("items", {})
                if "properties" in items:
                    extract_rules(items["properties"], f"{field_path}.")
                elif items.get("type") == "string":
                    rule = {}
                    if items.get("pattern"):
                        rule["pattern"] = items["pattern"]
                    if (
                        items.get("possible_values")
                        and items["possible_values"].get("type") == "one_of"
                    ):
                        rule["one_of"] = list(items["possible_values"]["value"].keys())
                    if rule:
                        rules[field_path] = rule
            else:
                rule = {}
                if config.get("pattern"):
                    rule["pattern"] = config["pattern"]
                if (
                    config.get("possible_values")
                    and config["possible_values"].get("type") == "one_of"
                ):
                    rule["one_of"] = list(config["possible_values"]["value"].keys())
                if rule:
                    rules[field_path] = rule

    extract_rules(schema.get("properties", {}))
    return rules


class FDACategory(Enum):
    drug = "drug"
    food = "food"
    cosmetic = "cosmetic"
    animalandveterinary = "animalandveterinary"


class FDADrugEndpoint(Enum):
    event = "event"
    label = "label"
    ndc = "ndc"
    enforcement = "enforcement"
    drugsfda = "drugsfda"
    shortages = "shortages"


class FDAFoodEndpoint(Enum):
    event = "event"


class FDADrugEventSearchField(Enum):
    authoritynumb = "authoritynumb"
    companynumb = "companynumb"
    duplicate = "duplicate"
    fulfillexpeditecriteria = "fulfillexpeditecriteria"
    occurcountry = "occurcountry"
    patient_drug_actiondrug = "patient.drug.actiondrug"
    patient_drug_activesubstance_activesubstancename = (
        "patient.drug.activesubstance.activesubstancename"
    )
    patient_drug_drugadditional = "patient.drug.drugadditional"
    patient_drug_drugadministrationroute = "patient.drug.drugadministrationroute"
    patient_drug_drugauthorizationnumb = "patient.drug.drugauthorizationnumb"
    patient_drug_drugbatchnumb = "patient.drug.drugbatchnumb"
    patient_drug_drugcharacterization = "patient.drug.drugcharacterization"
    patient_drug_drugcumulativedosagenumb = "patient.drug.drugcumulativedosagenumb"
    patient_drug_drugcumulativedosageunit = "patient.drug.drugcumulativedosageunit"
    patient_drug_drugdosageform = "patient.drug.drugdosageform"
    patient_drug_drugdosagetext = "patient.drug.drugdosagetext"
    patient_drug_drugenddate = "patient.drug.drugenddate"
    patient_drug_drugenddateformat = "patient.drug.drugenddateformat"
    patient_drug_drugindication = "patient.drug.drugindication"
    patient_drug_drugintervaldosagedefinition = (
        "patient.drug.drugintervaldosagedefinition"
    )
    patient_drug_drugintervaldosageunitnumb = "patient.drug.drugintervaldosageunitnumb"
    patient_drug_drugrecurreadministration = "patient.drug.drugrecurreadministration"
    patient_drug_drugrecurrence_drugrecuractionmeddraversion = (
        "patient.drug.drugrecurrence.drugrecuractionmeddraversion"
    )
    patient_drug_drugrecurrence_drugrecuraction = (
        "patient.drug.drugrecurrence.drugrecuraction"
    )
    patient_drug_drugseparatedosagenumb = "patient.drug.drugseparatedosagenumb"
    patient_drug_drugstartdate = "patient.drug.drugstartdate"
    patient_drug_drugstartdateformat = "patient.drug.drugstartdateformat"
    patient_drug_drugstructuredosagenumb = "patient.drug.drugstructuredosagenumb"
    patient_drug_drugstructuredosageunit = "patient.drug.drugstructuredosageunit"
    patient_drug_drugtreatmentduration = "patient.drug.drugtreatmentduration"
    patient_drug_drugtreatmentdurationunit = "patient.drug.drugtreatmentdurationunit"
    patient_drug_medicinalproduct = "patient.drug.medicinalproduct"
    patient_drug_openfda_application_number = "patient.drug.openfda.application_number"
    patient_drug_openfda_brand_name = "patient.drug.openfda.brand_name"
    patient_drug_openfda_generic_name = "patient.drug.openfda.generic_name"
    patient_drug_openfda_manufacturer_name = "patient.drug.openfda.manufacturer_name"
    patient_drug_openfda_nui = "patient.drug.openfda.nui"
    patient_drug_openfda_package_ndc = "patient.drug.openfda.package_ndc"
    patient_drug_openfda_pharm_class_cs = "patient.drug.openfda.pharm_class_cs"
    patient_drug_openfda_pharm_class_epc = "patient.drug.openfda.pharm_class_epc"
    patient_drug_openfda_pharm_class_pe = "patient.drug.openfda.pharm_class_pe"
    patient_drug_openfda_pharm_class_moa = "patient.drug.openfda.pharm_class_moa"
    patient_drug_openfda_product_ndc = "patient.drug.openfda.product_ndc"
    patient_drug_openfda_product_type = "patient.drug.openfda.product_type"
    patient_drug_openfda_route = "patient.drug.openfda.route"
    patient_drug_openfda_rxcui = "patient.drug.openfda.rxcui"
    patient_drug_openfda_spl_id = "patient.drug.openfda.spl_id"
    patient_drug_openfda_spl_set_id = "patient.drug.openfda.spl_set_id"
    patient_drug_openfda_substance_name = "patient.drug.openfda.substance_name"
    patient_drug_openfda_unii = "patient.drug.openfda.unii"
    patient_patientagegroup = "patient.patientagegroup"
    patient_patientdeath_patientdeathdate = "patient.patientdeath.patientdeathdate"
    patient_patientdeath_patientdeathdateformat = (
        "patient.patientdeath.patientdeathdateformat"
    )
    patient_patientonsetage = "patient.patientonsetage"
    patient_patientonsetageunit = "patient.patientonsetageunit"
    patient_patientsex = "patient.patientsex"
    patient_patientweight = "patient.patientweight"
    patient_reaction_reactionmeddrapt = "patient.reaction.reactionmeddrapt"
    patient_reaction_reactionmeddraversionpt = (
        "patient.reaction.reactionmeddraversionpt"
    )
    patient_reaction_reactionoutcome = "patient.reaction.reactionoutcome"
    patient_summary_narrativeincludeclinical = (
        "patient.summary.narrativeincludeclinical"
    )
    primarysource_literaturereference = "primarysource.literaturereference"
    primarysource_qualification = "primarysource.qualification"
    primarysource_reportercountry = "primarysource.reportercountry"
    primarysourcecountry = "primarysourcecountry"
    receiptdate = "receiptdate"
    receiptdateformat = "receiptdateformat"
    receivedate = "receivedate"
    receivedateformat = "receivedateformat"
    receiver_receiverorganization = "receiver.receiverorganization"
    receiver_receivertype = "receiver.receivertype"
    reportduplicate_duplicatenumb = "reportduplicate.duplicatenumb"
    reportduplicate_duplicatesource = "reportduplicate.duplicatesource"
    reporttype = "reporttype"
    safetyreportid = "safetyreportid"
    safetyreportversion = "safetyreportversion"
    sender_senderorganization = "sender.senderorganization"
    sender_sendertype = "sender.sendertype"
    serious = "serious"
    seriousnesscongenitalanomali = "seriousnesscongenitalanomali"
    seriousnessdeath = "seriousnessdeath"
    seriousnessdisabling = "seriousnessdisabling"
    seriousnesshospitalization = "seriousnesshospitalization"
    seriousnesslifethreatening = "seriousnesslifethreatening"
    seriousnessother = "seriousnessother"
    transmissiondate = "transmissiondate"
    transmissiondateformat = "transmissiondateformat"


class FDADrugEnforcementSearchField(Enum):
    address_1 = "address_1"
    address_2 = "address_2"
    center_classification_date = "center_classification_date"
    city = "city"
    classification = "classification"
    code_info = "code_info"
    country = "country"
    distribution_pattern = "distribution_pattern"
    event_id = "event_id"
    initial_firm_notification = "initial_firm_notification"
    more_code_info = "more_code_info"
    openfda_application_number = "openfda.application_number"
    openfda_brand_name = "openfda.brand_name"
    openfda_generic_name = "openfda.generic_name"
    openfda_is_original_packager = "openfda.is_original_packager"
    openfda_manufacturer_name = "openfda.manufacturer_name"
    openfda_nui = "openfda.nui"
    openfda_original_packager_product_ndc = "openfda.original_packager_product_ndc"
    openfda_package_ndc = "openfda.package_ndc"
    openfda_pharm_class_cs = "openfda.pharm_class_cs"
    openfda_pharm_class_epc = "openfda.pharm_class_epc"
    openfda_pharm_class_pe = "openfda.pharm_class_pe"
    openfda_pharm_class_moa = "openfda.pharm_class_moa"
    openfda_product_ndc = "openfda.product_ndc"
    openfda_product_type = "openfda.product_type"
    openfda_route = "openfda.route"
    openfda_rxcui = "openfda.rxcui"
    openfda_spl_id = "openfda.spl_id"
    openfda_spl_set_id = "openfda.spl_set_id"
    openfda_substance_name = "openfda.substance_name"
    openfda_unii = "openfda.unii"
    openfda_upc = "openfda.upc"
    product_type = "product_type"
    product_code = "product_code"
    product_description = "product_description"
    product_quantity = "product_quantity"
    reason_for_recall = "reason_for_recall"
    recall_initiation_date = "recall_initiation_date"
    recall_number = "recall_number"
    recalling_firm = "recalling_firm"
    report_date = "report_date"
    state = "state"
    status = "status"
    termination_date = "termination_date"
    voluntary_mandated = "voluntary_mandated"


SEARCH_FIELD_VALIDATION_RULES = {
    FDADrugEndpoint.event: _load_field_rules("drug_event_fields.yaml"),
    FDADrugEndpoint.enforcement: _load_field_rules("drug_enforcement_fields.yaml"),
    FDADrugEndpoint.label: _load_field_rules("drug_label_fields.yaml"),
    FDADrugEndpoint.ndc: _load_field_rules("drug_ndc_fields.yaml"),
    FDADrugEndpoint.drugsfda: _load_field_rules("drug_drugsfda_fields.yaml"),
    FDADrugEndpoint.shortages: _load_field_rules("drug_shortages_fields.yaml"),
}


SEARCH_FIELD_ENUMS = {
    FDADrugEndpoint.event: FDADrugEventSearchField,
    FDADrugEndpoint.enforcement: FDADrugEnforcementSearchField,
}


VALID_ENDPOINTS = {
    FDACategory("drug"): FDADrugEndpoint,
    FDACategory("food"): FDAFoodEndpoint,
}


class FDAModel(BaseModel):
    model_config = ConfigDict(use_enum_values=True)
    category: FDACategory
    endpoint: FDADrugEndpoint | FDAFoodEndpoint
    search: Dict[str, Any]

    @model_validator(mode="after")
    def check_valid_endpoint(self):
        valid_endpoints = VALID_ENDPOINTS[FDACategory(self.category)]
        valid_values = [val.value for val in valid_endpoints]
        if self.endpoint not in valid_values:
            raise ValueError(
                f"{self.endpoint} is not a valid endpoint for {self.category}. Please choose from {valid_values}"
            )
        return self

    @model_validator(mode="after")
    def check_valid_search_values(self):
        if self.endpoint not in SEARCH_FIELD_ENUMS:
            return self

        valid_field_values = {
            field.value for field in SEARCH_FIELD_ENUMS[self.endpoint]
        }
        rules_map = SEARCH_FIELD_VALIDATION_RULES[FDADrugEndpoint.event]
        for field_path, value in self.search.items():
            if field_path not in valid_field_values:
                raise ValueError(
                    f"Invalid search field '{field_path}'. Must be one of: {valid_field_values}"
                )
            rules = rules_map.get(field_path, {})

            str_value = str(value)

            if "one_of" in rules:
                if str_value not in rules["one_of"]:
                    raise ValueError(
                        f"Invalid value '{value}' for field '{field_path}'. "
                        f"Must be one of: {rules['one_of']}"
                    )

            if "pattern" in rules:
                if not re.match(rules["pattern"], str_value):
                    raise ValueError(
                        f"Invalid value '{value}' for field '{field_path}'. "
                        f"Must match pattern: {rules['pattern']}"
                    )

        return self


if __name__ == "__main__":
    valid_model = FDAModel(
        category="drug",
        endpoint="event",
        search={"patient.patientsex": "1"},
    )

    print(valid_model)
    print(valid_model.model_dump())
