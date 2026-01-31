from enum import Enum
from pathlib import Path
import re
import yaml
from pydantic import BaseModel, model_validator, ConfigDict, ValidationError
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
    animalandveterinary = "animalandveterinary"
    drug = "drug"
    device = "device"
    food = "food"
    cosmetic = "cosmetic"
    other = "other"
    tobacco = "tobacco"
    transparency = "transparency"


class FDAAnimalVeterinaryEndpoint(Enum):
    event = "event"


class FDADrugEndpoint(Enum):
    event = "event"
    label = "label"
    ndc = "ndc"
    enforcement = "enforcement"
    drugsfda = "drugsfda"
    shortages = "shortages"


class FDADeviceEndpoint(Enum):
    _510k = "510k"
    classification = "classification"
    enforcement = "enforcement"
    event = "event"
    pma = "pma"
    recall = "recall"
    registrationlisting = "registrationlisting"
    covid19serology = "covid19serology"
    udi = "udi"


class FDAFoodEndpoint(Enum):
    event = "event"
    enforcement = "enforcement"


class FDACosmeticEndpoint(Enum):
    event = "event"


class FDATobaccoEndpoint(Enum):
    problem = "problem"


class FDAOtherEndpoint(Enum):
    historicaldocument = "historicaldocument"
    nsde = "nsde"
    substance = "substance"


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


class FDADrugLabelSearchField(Enum):
    abuse = "abuse"
    abuse_table = "abuse_table"
    accessories = "accessories"
    accessories_table = "accessories_table"
    active_ingredient = "active_ingredient"
    active_ingredient_table = "active_ingredient_table"
    adverse_reactions = "adverse_reactions"
    adverse_reactions_table = "adverse_reactions_table"
    alarms = "alarms"
    alarms_table = "alarms_table"
    animal_pharmacology_and_or_toxicology = "animal_pharmacology_and_or_toxicology"
    animal_pharmacology_and_or_toxicology_table = (
        "animal_pharmacology_and_or_toxicology_table"
    )
    ask_doctor = "ask_doctor"
    ask_doctor_table = "ask_doctor_table"
    ask_doctor_or_pharmacist = "ask_doctor_or_pharmacist"
    ask_doctor_or_pharmacist_table = "ask_doctor_or_pharmacist_table"
    assembly_or_installation_instructions = "assembly_or_installation_instructions"
    assembly_or_installation_instructions_table = (
        "assembly_or_installation_instructions_table"
    )
    boxed_warning = "boxed_warning"
    boxed_warning_table = "boxed_warning_table"
    calibration_instructions = "calibration_instructions"
    calibration_instructions_table = "calibration_instructions_table"
    carcinogenesis_and_mutagenesis_and_impairment_of_fertility = (
        "carcinogenesis_and_mutagenesis_and_impairment_of_fertility"
    )
    carcinogenesis_and_mutagenesis_and_impairment_of_fertility_table = (
        "carcinogenesis_and_mutagenesis_and_impairment_of_fertility_table"
    )
    cleaning = "cleaning"
    cleaning_table = "cleaning_table"
    clinical_pharmacology = "clinical_pharmacology"
    clinical_pharmacology_table = "clinical_pharmacology_table"
    clinical_studies = "clinical_studies"
    clinical_studies_table = "clinical_studies_table"
    compatible_accessories = "compatible_accessories"
    compatible_accessories_table = "compatible_accessories_table"
    components = "components"
    components_table = "components_table"
    contraindications = "contraindications"
    contraindications_table = "contraindications_table"
    controlled_substance = "controlled_substance"
    controlled_substance_table = "controlled_substance_table"
    dependence = "dependence"
    dependence_table = "dependence_table"
    description = "description"
    description_table = "description_table"
    diagram_of_device = "diagram_of_device"
    diagram_of_device_table = "diagram_of_device_table"
    disposal_and_waste_handling = "disposal_and_waste_handling"
    disposal_and_waste_handling_table = "disposal_and_waste_handling_table"
    do_not_use = "do_not_use"
    do_not_use_table = "do_not_use_table"
    dosage_and_administration = "dosage_and_administration"
    dosage_and_administration_table = "dosage_and_administration_table"
    dosage_forms_and_strengths = "dosage_forms_and_strengths"
    dosage_forms_and_strengths_table = "dosage_forms_and_strengths_table"
    drug_abuse_and_dependence = "drug_abuse_and_dependence"
    drug_abuse_and_dependence_table = "drug_abuse_and_dependence_table"
    drug_and_or_laboratory_test_interactions = (
        "drug_and_or_laboratory_test_interactions"
    )
    drug_and_or_laboratory_test_interactions_table = (
        "drug_and_or_laboratory_test_interactions_table"
    )
    drug_interactions = "drug_interactions"
    drug_interactions_table = "drug_interactions_table"
    effective_time = "effective_time"
    environmental_warning = "environmental_warning"
    environmental_warning_table = "environmental_warning_table"
    food_safety_warning = "food_safety_warning"
    food_safety_warning_table = "food_safety_warning_table"
    general_precautions = "general_precautions"
    general_precautions_table = "general_precautions_table"
    geriatric_use = "geriatric_use"
    geriatric_use_table = "geriatric_use_table"
    guaranteed_analysis_of_feed = "guaranteed_analysis_of_feed"
    guaranteed_analysis_of_feed_table = "guaranteed_analysis_of_feed_table"
    health_care_provider_letter = "health_care_provider_letter"
    health_care_provider_letter_table = "health_care_provider_letter_table"
    health_claim = "health_claim"
    health_claim_table = "health_claim_table"
    how_supplied = "how_supplied"
    how_supplied_table = "how_supplied_table"
    id = "id"
    inactive_ingredient = "inactive_ingredient"
    inactive_ingredient_table = "inactive_ingredient_table"
    indications_and_usage = "indications_and_usage"
    indications_and_usage_table = "indications_and_usage_table"
    information_for_owners_or_caregivers = "information_for_owners_or_caregivers"
    information_for_owners_or_caregivers_table = (
        "information_for_owners_or_caregivers_table"
    )
    information_for_patients = "information_for_patients"
    information_for_patients_table = "information_for_patients_table"
    instructions_for_use = "instructions_for_use"
    instructions_for_use_table = "instructions_for_use_table"
    intended_use_of_the_device = "intended_use_of_the_device"
    intended_use_of_the_device_table = "intended_use_of_the_device_table"
    keep_out_of_reach_of_children = "keep_out_of_reach_of_children"
    keep_out_of_reach_of_children_table = "keep_out_of_reach_of_children_table"
    labor_and_delivery = "labor_and_delivery"
    labor_and_delivery_table = "labor_and_delivery_table"
    laboratory_tests = "laboratory_tests"
    laboratory_tests_table = "laboratory_tests_table"
    mechanism_of_action = "mechanism_of_action"
    mechanism_of_action_table = "mechanism_of_action_table"
    microbiology = "microbiology"
    microbiology_table = "microbiology_table"
    nonclinical_toxicology = "nonclinical_toxicology"
    nonclinical_toxicology_table = "nonclinical_toxicology_table"
    nonteratogenic_effects = "nonteratogenic_effects"
    nonteratogenic_effects_table = "nonteratogenic_effects_table"
    nursing_mothers = "nursing_mothers"
    nursing_mothers_table = "nursing_mothers_table"
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
    other_safety_information = "other_safety_information"
    other_safety_information_table = "other_safety_information_table"
    overdosage = "overdosage"
    overdosage_table = "overdosage_table"
    package_label_principal_display_panel = "package_label_principal_display_panel"
    package_label_principal_display_panel_table = (
        "package_label_principal_display_panel_table"
    )
    patient_medication_information = "patient_medication_information"
    patient_medication_information_table = "patient_medication_information_table"
    pediatric_use = "pediatric_use"
    pediatric_use_table = "pediatric_use_table"
    pharmacodynamics = "pharmacodynamics"
    pharmacodynamics_table = "pharmacodynamics_table"
    pharmacogenomics = "pharmacogenomics"
    pharmacogenomics_table = "pharmacogenomics_table"
    pharmacokinetics = "pharmacokinetics"
    pharmacokinetics_table = "pharmacokinetics_table"
    precautions = "precautions"
    precautions_table = "precautions_table"
    pregnancy = "pregnancy"
    pregnancy_table = "pregnancy_table"
    pregnancy_or_breast_feeding = "pregnancy_or_breast_feeding"
    pregnancy_or_breast_feeding_table = "pregnancy_or_breast_feeding_table"
    purpose = "purpose"
    purpose_table = "purpose_table"
    questions = "questions"
    questions_table = "questions_table"
    recent_major_changes = "recent_major_changes"
    recent_major_changes_table = "recent_major_changes_table"
    reference = "reference"
    reference_table = "reference_table"
    retained_splash_statement = "retained_splash_statement"
    retained_splash_statement_table = "retained_splash_statement_table"
    route_of_administration = "route_of_administration"
    route_of_administration_table = "route_of_administration_table"
    safe_sleeping_guidelines = "safe_sleeping_guidelines"
    safe_sleeping_guidelines_table = "safe_sleeping_guidelines_table"
    safety_and_handling = "safety_and_handling"
    safety_and_handling_table = "safety_and_handling_table"
    search_key = "search_key"
    search_key_table = "search_key_table"
    sectional_information = "sectional_information"
    sectional_information_table = "sectional_information_table"
    set_id = "set_id"
    splash_statements = "splash_statements"
    splash_statements_table = "splash_statements_table"
    storage_and_handling = "storage_and_handling"
    storage_and_handling_table = "storage_and_handling_table"
    strength = "strength"
    strength_table = "strength_table"
    substance = "substance"
    substance_table = "substance_table"
    summary_of_safety_and_effectiveness = "summary_of_safety_and_effectiveness"
    summary_of_safety_and_effectiveness_table = (
        "summary_of_safety_and_effectiveness_table"
    )
    supplemental_american_core_data = "supplemental_american_core_data"
    supplemental_american_core_data_table = "supplemental_american_core_data_table"
    suppression_of_data = "suppression_of_data"
    suppression_of_data_table = "suppression_of_data_table"
    table_of_contents = "table_of_contents"
    table_of_contents_table = "table_of_contents_table"
    teratogenic_effects = "teratogenic_effects"
    teratogenic_effects_table = "teratogenic_effects_table"
    unapproved_drug_section = "unapproved_drug_section"
    unapproved_drug_section_table = "unapproved_drug_section_table"
    usage_in_specific_populations = "usage_in_specific_populations"
    usage_in_specific_populations_table = "usage_in_specific_populations_table"
    user_warnings = "user_warnings"
    user_warnings_table = "user_warnings_table"
    version_number = "version_number"
    warning = "warning"
    warnings = "warnings"
    warnings_and_cautions = "warnings_and_cautions"
    warnings_and_cautions_table = "warnings_and_cautions_table"
    warnings_table = "warnings_table"
    what_doctors_need_to_know = "what_doctors_need_to_know"
    what_doctors_need_to_know_table = "what_doctors_need_to_know_table"
    what_is_the_most_important_information_i_should_know_about = (
        "what_is_the_most_important_information_i_should_know_about"
    )
    what_is_the_most_important_information_i_should_know_about_table = (
        "what_is_the_most_important_information_i_should_know_about_table"
    )
    when_not_to_use = "when_not_to_use"
    when_not_to_use_table = "when_not_to_use_table"
    when_should_i_not_take_this_drug = "when_should_i_not_take_this_drug"
    when_should_i_not_take_this_drug_table = "when_should_i_not_take_this_drug_table"
    who_should_not_take_this_drug = "who_should_not_take_this_drug"
    who_should_not_take_this_drug_table = "who_should_not_take_this_drug_table"
    window_of_tolerance_for_laser_radiation = "window_of_tolerance_for_laser_radiation"
    window_of_tolerance_for_laser_radiation_table = (
        "window_of_tolerance_for_laser_radiation_table"
    )


class FDADrugNDCSearchField(Enum):
    product_id = "product_id"
    product_ndc = "product_ndc"
    spl_id = "spl_id"
    product_type = "product_type"
    finished = "finished"
    brand_name = "brand_name"
    brand_name_base = "brand_name_base"
    brand_name_suffix = "brand_name_suffix"
    generic_name = "generic_name"
    dosage_form = "dosage_form"
    route = "route"
    marketing_start_date = "marketing_start_date"
    marketing_end_date = "marketing_end_date"
    marketing_category = "marketing_category"
    application_number = "application_number"
    pharm_class = "pharm_class"
    dea_schedule = "dea_schedule"
    listing_expiration_date = "listing_expiration_date"
    active_ingredients_name = "active_ingredients.name"
    active_ingredients_strength = "active_ingredients.strength"
    packaging_package_ndc = "packaging.package_ndc"
    packaging_description = "packaging.description"
    packaging_marketing_start_date = "packaging.marketing_start_date"
    packaging_marketing_end_date = "packaging.marketing_end_date"
    packaging_sample = "packaging.sample"
    openfda_is_original_packager = "openfda.is_original_packager"
    openfda_manufacturer_name = "openfda.manufacturer_name"
    openfda_nui = "openfda.nui"
    openfda_pharm_class_cs = "openfda.pharm_class_cs"
    openfda_pharm_class_epc = "openfda.pharm_class_epc"
    openfda_pharm_class_moa = "openfda.pharm_class_moa"
    openfda_pharm_class_pe = "openfda.pharm_class_pe"
    openfda_rxcui = "openfda.rxcui"
    openfda_spl_set_id = "openfda.spl_set_id"
    openfda_unii = "openfda.unii"
    openfda_upc = "openfda.upc"


class FDADrugDrugsFDASearchField(Enum):
    application_number = "application_number"
    openfda_application_number = "openfda.application_number"
    openfda_brand_name = "openfda.brand_name"
    openfda_generic_name = "openfda.generic_name"
    openfda_manufacturer_name = "openfda.manufacturer_name"
    openfda_nui = "openfda.nui"
    openfda_package_ndc = "openfda.package_ndc"
    openfda_pharm_class_cs = "openfda.pharm_class_cs"
    openfda_pharm_class_epc = "openfda.pharm_class_epc"
    openfda_pharm_class_pe = "openfda.pharm_class_pe"
    openfda_pharm_class_moa = "openfda.pharm_class_moa"
    openfda_product_ndc = "openfda.product_ndc"
    openfda_route = "openfda.route"
    openfda_rxcui = "openfda.rxcui"
    openfda_spl_id = "openfda.spl_id"
    openfda_spl_set_id = "openfda.spl_set_id"
    openfda_substance_name = "openfda.substance_name"
    openfda_unii = "openfda.unii"
    products_active_ingredients_name = "products.active_ingredients.name"
    products_active_ingredients_strength = "products.active_ingredients.strength"
    products_brand_name = "products.brand_name"
    products_dosage_form = "products.dosage_form"
    products_marketing_status = "products.marketing_status"
    products_product_number = "products.product_number"
    products_reference_drug = "products.reference_drug"
    products_reference_standard = "products.reference_standard"
    products_route = "products.route"
    products_te_code = "products.te_code"
    sponsor_name = "sponsor_name"
    submissions_submission_property_type_code = (
        "submissions.submission_property_type.code"
    )
    submissions_application_docs_id = "submissions.application_docs.id"
    submissions_application_docs_date = "submissions.application_docs.date"
    submissions_application_docs_title = "submissions.application_docs.title"
    submissions_application_docs_type = "submissions.application_docs.type"
    submissions_application_docs_url = "submissions.application_docs.url"
    submissions_review_priority = "submissions.review_priority"
    submissions_submission_class_code = "submissions.submission_class_code"
    submissions_submission_class_code_description = (
        "submissions.submission_class_code_description"
    )
    submissions_submission_number = "submissions.submission_number"
    submissions_submission_public_notes = "submissions.submission_public_notes"
    submissions_submission_status = "submissions.submission_status"
    submissions_submission_status_date = "submissions.submission_status_date"
    submissions_submission_type = "submissions.submission_type"


class FDADrugShortagesSearchField(Enum):
    package_ndc = "package_ndc"
    generic_name = "generic_name"
    proprietary_name = "proprietary_name"
    company_name = "company_name"
    contact_info = "contact_info"
    presentation = "presentation"
    update_type = "update_type"
    availability = "availability"
    related_info = "related_info"
    related_info_link = "related_info_link"
    resolved_note = "resolved_note"
    shortage_reason = "shortage_reason"
    therapeutic_category = "therapeutic_category"
    dosage_form = "dosage_form"
    strength = "strength"
    status = "status"
    update_date = "update_date"
    change_date = "change_date"
    discontinued_date = "discontinued_date"
    initial_posting_date = "initial_posting_date"
    openfda_brand_name = "openfda.brand_name"
    openfda_dosage_form = "openfda.dosage_form"
    openfda_is_original_packager = "openfda.is_original_packager"
    openfda_manufacturer_name = "openfda.manufacturer_name"
    openfda_nui = "openfda.nui"
    openfda_original_packager_product_ndc = "openfda.original_packager_product_ndc"
    openfda_package_ndc = "openfda.package_ndc"
    openfda_pharm_class_cs = "openfda.pharm_class_cs"
    openfda_pharm_class_epc = "openfda.pharm_class_epc"
    openfda_pharm_class_moa = "openfda.pharm_class_moa"
    openfda_pharm_class_pe = "openfda.pharm_class_pe"
    openfda_product_ndc = "openfda.product_ndc"
    openfda_product_type = "openfda.product_type"
    openfda_route = "openfda.route"
    openfda_rxcui = "openfda.rxcui"
    openfda_spl_id = "openfda.spl_id"
    openfda_spl_set_id = "openfda.spl_set_id"
    openfda_substance_name = "openfda.substance_name"
    openfda_unii = "openfda.unii"
    openfda_upc = "openfda.upc"


class FDAAnimalVeterinaryEventSearchField(Enum):
    animal_age_max = "animal.age.max"
    animal_age_min = "animal.age.min"
    animal_age_qualifier = "animal.age.qualifier"
    animal_age_unit = "animal.age.unit"
    animal_breed_breed_component = "animal.breed.breed_component"
    animal_breed_is_crossbred = "animal.breed.is_crossbred"
    animal_female_animal_physiological_status = (
        "animal.female_animal_physiological_status"
    )
    animal_gender = "animal.gender"
    animal_reproductive_status = "animal.reproductive_status"
    animal_species = "animal.species"
    animal_weight_max = "animal.weight.max"
    animal_weight_min = "animal.weight.min"
    animal_weight_qualifier = "animal.weight.qualifier"
    animal_weight_unit = "animal.weight.unit"
    drug_active_ingredients_name = "drug.active_ingredients.name"
    drug_administered_by = "drug.administered_by"
    drug_ae_abated_after_stopping_drug = "drug.ae_abated_after_stopping_drug"
    drug_ae_reappeared_after_resuming_drug = "drug.ae_reappeared_after_resuming_drug"
    drug_atc_vet_code = "drug.atc_vet_code"
    drug_brand_name = "drug.brand_name"
    drug_dosage_form = "drug.dosage_form"
    drug_first_exposure_date = "drug.first_exposure_date"
    drug_frequency_of_administration_unit = "drug.frequency_of_administration.unit"
    drug_frequency_of_administration_value = "drug.frequency_of_administration.value"
    drug_last_exposure_date = "drug.last_exposure_date"
    drug_lot_expiration = "drug.lot_expiration"
    drug_lot_number = "drug.lot_number"
    drug_manufacturer_name = "drug.manufacturer.name"
    drug_manufacturer_registration_number = "drug.manufacturer.registration_number"
    drug_manufacturing_date = "drug.manufacturing_date"
    drug_number_of_defective_items = "drug.number_of_defective_items"
    drug_number_of_items_returned = "drug.number_of_items_returned"
    drug_off_label_use = "drug.off_label_use"
    drug_previous_ae_to_drug = "drug.previous_ae_to_drug"
    drug_previous_exposure_to_drug = "drug.previous_exposure_to_drug"
    drug_product_ndc = "drug.product_ndc"
    drug_route = "drug.route"
    drug_used_according_to_label = "drug.used_according_to_label"
    duration_unit = "duration.unit"
    duration_value = "duration.value"
    health_assessment_prior_to_exposure_assessed_by = (
        "health_assessment_prior_to_exposure.assessed_by"
    )
    health_assessment_prior_to_exposure_condition = (
        "health_assessment_prior_to_exposure.condition"
    )
    number_of_animals_affected = "number_of_animals_affected"
    number_of_animals_treated = "number_of_animals_treated"
    onset_date = "onset_date"
    original_receive_date = "original_receive_date"
    outcome_medical_status = "outcome.medical_status"
    outcome_number_of_animals_affected = "outcome.number_of_animals_affected"
    primary_reporter = "primary_reporter"
    reaction_accuracy = "reaction.accuracy"
    reaction_number_of_animals_affected = "reaction.number_of_animals_affected"
    reaction_veddra_term_code = "reaction.veddra_term_code"
    reaction_veddra_term_name = "reaction.veddra_term_name"
    reaction_veddra_version = "reaction.veddra_version"
    receiver_city = "receiver.city"
    receiver_country = "receiver.country"
    receiver_organization = "receiver.organization"
    receiver_postal_code = "receiver.postal_code"
    receiver_state = "receiver.state"
    receiver_street_address = "receiver.street_address"
    report_id = "report_id"
    secondary_reporter = "secondary_reporter"
    serious_ae = "serious_ae"
    time_between_exposure_and_onset = "time_between_exposure_and_onset"
    treated_for_ae = "treated_for_ae"
    type_of_information = "type_of_information"
    unique_aer_id_number = "unique_aer_id_number"


class FDADevice510kSearchField(Enum):
    address_1 = "address_1"
    address_2 = "address_2"
    advisory_committee = "advisory_committee"
    advisory_committee_description = "advisory_committee_description"
    applicant = "applicant"
    city = "city"
    clearance_type = "clearance_type"
    contact = "contact"
    country_code = "country_code"
    date_received = "date_received"
    decision_code = "decision_code"
    decision_date = "decision_date"
    decision_description = "decision_description"
    device_name = "device_name"
    expedited_review_flag = "expedited_review_flag"
    k_number = "k_number"
    meta_disclaimer = "meta.disclaimer"
    meta_last_updated = "meta.last_updated"
    meta_license = "meta.license"
    meta_results_limit = "meta.results.limit"
    meta_results_skip = "meta.results.skip"
    meta_results_total = "meta.results.total"
    openfda_device_class = "openfda.device_class"
    openfda_device_name = "openfda.device_name"
    openfda_medical_specialty_description = "openfda.medical_specialty_description"
    postal_code = "postal_code"
    product_code = "product_code"
    review_advisory_committee = "review_advisory_committee"
    state = "state"
    statement_or_summary = "statement_or_summary"
    third_party_flag = "third_party_flag"
    zip_code = "zip_code"


class FDADeviceClassificationSearchField(Enum):
    definition = "definition"
    device_class = "device_class"
    device_name = "device_name"
    gmp_exempt_flag = "gmp_exempt_flag"
    implant_flag = "implant_flag"
    life_sustain_support_flag = "life_sustain_support_flag"
    medical_specialty = "medical_specialty"
    medical_specialty_description = "medical_specialty_description"
    product_code = "product_code"
    regulation_number = "regulation_number"
    review_code = "review_code"
    review_panel = "review_panel"
    submission_type_id = "submission_type_id"
    summary_malfunction_reporting = "summary_malfunction_reporting"
    third_party_flag = "third_party_flag"
    unclassified_reason = "unclassified_reason"


class FDADeviceEnforcementSearchField(Enum):
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
    meta_disclaimer = "meta.disclaimer"
    meta_last_updated = "meta.last_updated"
    meta_license = "meta.license"
    meta_results_limit = "meta.results.limit"
    meta_results_skip = "meta.results.skip"
    meta_results_total = "meta.results.total"
    more_code_info = "more_code_info"
    openfda_is_original_packager = "openfda.is_original_packager"
    product_code = "product_code"
    product_description = "product_description"
    product_quantity = "product_quantity"
    product_type = "product_type"
    reason_for_recall = "reason_for_recall"
    recall_initiation_date = "recall_initiation_date"
    recall_number = "recall_number"
    recalling_firm = "recalling_firm"
    report_date = "report_date"
    state = "state"
    status = "status"
    termination_date = "termination_date"
    voluntary_mandated = "voluntary_mandated"


class FDADeviceEventSearchField(Enum):
    adverse_event_flag = "adverse_event_flag"
    date_facility_aware = "date_facility_aware"
    date_manufacturer_received = "date_manufacturer_received"
    date_of_event = "date_of_event"
    date_received = "date_received"
    date_report = "date_report"
    date_report_to_fda = "date_report_to_fda"
    date_report_to_manufacturer = "date_report_to_manufacturer"
    device_brand_name = "device.brand_name"
    device_catalog_number = "device.catalog_number"
    device_date_received = "device.date_received"
    device_date_removed_flag = "device.date_removed_flag"
    device_date_returned_to_manufacturer = "device.date_returned_to_manufacturer"
    device_device_age_text = "device.device_age_text"
    device_device_availability = "device.device_availability"
    device_device_evaluated_by_manufacturer = "device.device_evaluated_by_manufacturer"
    device_device_event_key = "device.device_event_key"
    device_device_operator = "device.device_operator"
    device_device_report_product_code = "device.device_report_product_code"
    device_device_sequence_number = "device.device_sequence_number"
    device_expiration_date_of_device = "device.expiration_date_of_device"
    device_generic_name = "device.generic_name"
    device_implant_flag = "device.implant_flag"
    device_lot_number = "device.lot_number"
    device_manufacturer_d_address_1 = "device.manufacturer_d_address_1"
    device_manufacturer_d_address_2 = "device.manufacturer_d_address_2"
    device_manufacturer_d_city = "device.manufacturer_d_city"
    device_manufacturer_d_country = "device.manufacturer_d_country"
    device_manufacturer_d_name = "device.manufacturer_d_name"
    device_manufacturer_d_postal_code = "device.manufacturer_d_postal_code"
    device_manufacturer_d_state = "device.manufacturer_d_state"
    device_manufacturer_d_zip_code = "device.manufacturer_d_zip_code"
    device_manufacturer_d_zip_code_ext = "device.manufacturer_d_zip_code_ext"
    device_model_number = "device.model_number"
    device_openfda_device_class = "device.openfda.device_class"
    device_openfda_device_name = "device.openfda.device_name"
    device_openfda_medical_specialty_description = (
        "device.openfda.medical_specialty_description"
    )
    device_openfda_regulation_number = "device.openfda.regulation_number"
    device_other_id_number = "device.other_id_number"
    device_udi_di = "device.udi_di"
    device_udi_public = "device.udi_public"
    device_date_of_manufacturer = "device_date_of_manufacturer"
    distributor_address_1 = "distributor_address_1"
    distributor_address_2 = "distributor_address_2"
    distributor_city = "distributor_city"
    distributor_name = "distributor_name"
    distributor_state = "distributor_state"
    distributor_zip_code = "distributor_zip_code"
    distributor_zip_code_ext = "distributor_zip_code_ext"
    event_key = "event_key"
    event_location = "event_location"
    event_type = "event_type"
    expiration_date_of_device = "expiration_date_of_device"
    health_professional = "health_professional"
    initial_report_to_fda = "initial_report_to_fda"
    manufacturer_address_1 = "manufacturer_address_1"
    manufacturer_address_2 = "manufacturer_address_2"
    manufacturer_city = "manufacturer_city"
    manufacturer_contact_address_1 = "manufacturer_contact_address_1"
    manufacturer_contact_address_2 = "manufacturer_contact_address_2"
    manufacturer_contact_area_code = "manufacturer_contact_area_code"
    manufacturer_contact_city = "manufacturer_contact_city"
    manufacturer_contact_country = "manufacturer_contact_country"
    manufacturer_contact_exchange = "manufacturer_contact_exchange"
    manufacturer_contact_extension = "manufacturer_contact_extension"
    manufacturer_contact_f_name = "manufacturer_contact_f_name"
    manufacturer_contact_l_name = "manufacturer_contact_l_name"
    manufacturer_contact_pcity = "manufacturer_contact_pcity"
    manufacturer_contact_pcountry = "manufacturer_contact_pcountry"
    manufacturer_contact_phone_number = "manufacturer_contact_phone_number"
    manufacturer_contact_plocal = "manufacturer_contact_plocal"
    manufacturer_contact_postal_code = "manufacturer_contact_postal_code"
    manufacturer_contact_state = "manufacturer_contact_state"
    manufacturer_contact_t_name = "manufacturer_contact_t_name"
    manufacturer_contact_zip_code = "manufacturer_contact_zip_code"
    manufacturer_contact_zip_ext = "manufacturer_contact_zip_ext"
    manufacturer_country = "manufacturer_country"
    manufacturer_g1_address_1 = "manufacturer_g1_address_1"
    manufacturer_g1_address_2 = "manufacturer_g1_address_2"
    manufacturer_g1_city = "manufacturer_g1_city"
    manufacturer_g1_country = "manufacturer_g1_country"
    manufacturer_g1_name = "manufacturer_g1_name"
    manufacturer_g1_postal_code = "manufacturer_g1_postal_code"
    manufacturer_g1_state = "manufacturer_g1_state"
    manufacturer_g1_zip_code = "manufacturer_g1_zip_code"
    manufacturer_g1_zip_code_ext = "manufacturer_g1_zip_code_ext"
    manufacturer_link_flag = "manufacturer_link_flag"
    manufacturer_name = "manufacturer_name"
    manufacturer_postal_code = "manufacturer_postal_code"
    manufacturer_state = "manufacturer_state"
    manufacturer_zip_code = "manufacturer_zip_code"
    manufacturer_zip_code_ext = "manufacturer_zip_code_ext"
    mdr_report_key = "mdr_report_key"
    mdr_text_date_report = "mdr_text.date_report"
    mdr_text_mdr_text_key = "mdr_text.mdr_text_key"
    mdr_text_patient_sequence_number = "mdr_text.patient_sequence_number"
    mdr_text_text = "mdr_text.text"
    mdr_text_text_type_code = "mdr_text.text_type_code"
    number_devices_in_event = "number_devices_in_event"
    number_patients_in_event = "number_patients_in_event"
    patient_date_received = "patient.date_received"
    patient_patient_age = "patient.patient_age"
    patient_patient_ethnicity = "patient.patient_ethnicity"
    patient_patient_race = "patient.patient_race"
    patient_patient_sequence_number = "patient.patient_sequence_number"
    patient_patient_sex = "patient.patient_sex"
    patient_patient_weight = "patient.patient_weight"
    previous_use_code = "previous_use_code"
    product_problem_flag = "product_problem_flag"
    removal_correction_number = "removal_correction_number"
    report_date = "report_date"
    report_number = "report_number"
    report_source_code = "report_source_code"
    report_to_fda = "report_to_fda"
    report_to_manufacturer = "report_to_manufacturer"
    reporter_occupation_code = "reporter_occupation_code"
    reprocessed_and_reused_flag = "reprocessed_and_reused_flag"
    single_use_flag = "single_use_flag"


class FDADevicePMASearchField(Enum):
    advisory_committee = "advisory_committee"
    advisory_committee_description = "advisory_committee_description"
    ao_statement = "ao_statement"
    applicant = "applicant"
    city = "city"
    date_received = "date_received"
    decision_code = "decision_code"
    decision_date = "decision_date"
    docket_number = "docket_number"
    expedited_review_flag = "expedited_review_flag"
    fed_reg_notice_date = "fed_reg_notice_date"
    generic_name = "generic_name"
    openfda_device_class = "openfda.device_class"
    openfda_device_name = "openfda.device_name"
    openfda_medical_specialty_description = "openfda.medical_specialty_description"
    pma_number = "pma_number"
    product_code = "product_code"
    state = "state"
    street_1 = "street_1"
    street_2 = "street_2"
    supplement_number = "supplement_number"
    supplement_reason = "supplement_reason"
    supplement_type = "supplement_type"
    trade_name = "trade_name"
    zip = "zip"
    zip_ext = "zip_ext"


class FDADeviceRecallSearchField(Enum):
    action = "action"
    additional_info_contact = "additional_info_contact"
    address_1 = "address_1"
    address_2 = "address_2"
    cfres_id = "cfres_id"
    city = "city"
    code_info = "code_info"
    country = "country"
    distribution_pattern = "distribution_pattern"
    event_date_created = "event_date_created"
    event_date_initiated = "event_date_initiated"
    event_date_posted = "event_date_posted"
    event_date_terminated = "event_date_terminated"
    firm_fei_number = "firm_fei_number"
    meta_disclaimer = "meta.disclaimer"
    meta_last_updated = "meta.last_updated"
    meta_license = "meta.license"
    meta_results_limit = "meta.results.limit"
    meta_results_skip = "meta.results.skip"
    meta_results_total = "meta.results.total"
    openfda_device_class = "openfda.device_class"
    openfda_device_name = "openfda.device_name"
    openfda_medical_specialty_description = "openfda.medical_specialty_description"
    other_submission_description = "other_submission_description"
    postal_code = "postal_code"
    product_code = "product_code"
    product_description = "product_description"
    product_quantity = "product_quantity"
    product_res_number = "product_res_number"
    reason_for_recall = "reason_for_recall"
    recall_status = "recall_status"
    recalling_firm = "recalling_firm"
    res_event_number = "res_event_number"
    root_cause_description = "root_cause_description"
    state = "state"


class FDADeviceRegistrationListingSearchField(Enum):
    k_number = "k_number"
    pma_number = "pma_number"
    products_created_date = "products.created_date"
    products_exempt = "products.exempt"
    products_openfda_device_class = "products.openfda.device_class"
    products_openfda_device_name = "products.openfda.device_name"
    products_openfda_medical_specialty_description = (
        "products.openfda.medical_specialty_description"
    )
    products_openfda_regulation_number = "products.openfda.regulation_number"
    products_owner_operator_number = "products.owner_operator_number"
    products_product_code = "products.product_code"
    registration_address_line_1 = "registration.address_line_1"
    registration_address_line_2 = "registration.address_line_2"
    registration_city = "registration.city"
    registration_fei_number = "registration.fei_number"
    registration_initial_importer_flag = "registration.initial_importer_flag"
    registration_iso_country_code = "registration.iso_country_code"
    registration_name = "registration.name"
    registration_owner_operator_contact_address_address_1 = (
        "registration.owner_operator.contact_address.address_1"
    )
    registration_owner_operator_contact_address_address_2 = (
        "registration.owner_operator.contact_address.address_2"
    )
    registration_owner_operator_contact_address_city = (
        "registration.owner_operator.contact_address.city"
    )
    registration_owner_operator_contact_address_iso_country_code = (
        "registration.owner_operator.contact_address.iso_country_code"
    )
    registration_owner_operator_contact_address_postal_code = (
        "registration.owner_operator.contact_address.postal_code"
    )
    registration_owner_operator_contact_address_state_code = (
        "registration.owner_operator.contact_address.state_code"
    )
    registration_owner_operator_contact_address_state_province = (
        "registration.owner_operator.contact_address.state_province"
    )
    registration_owner_operator_firm_name = "registration.owner_operator.firm_name"
    registration_owner_operator_official_correspondent_first_name = (
        "registration.owner_operator.official_correspondent.first_name"
    )
    registration_owner_operator_official_correspondent_last_name = (
        "registration.owner_operator.official_correspondent.last_name"
    )
    registration_owner_operator_official_correspondent_middle_initial = (
        "registration.owner_operator.official_correspondent.middle_initial"
    )
    registration_owner_operator_official_correspondent_phone_number = (
        "registration.owner_operator.official_correspondent.phone_number"
    )
    registration_owner_operator_official_correspondent_subaccount_company_name = (
        "registration.owner_operator.official_correspondent.subaccount_company_name"
    )
    registration_owner_operator_owner_operator_number = (
        "registration.owner_operator.owner_operator_number"
    )
    registration_postal_code = "registration.postal_code"
    registration_reg_expiry_date_year = "registration.reg_expiry_date_year"
    registration_registration_number = "registration.registration_number"
    registration_state_code = "registration.state_code"
    registration_status_code = "registration.status_code"
    registration_us_agent_address_line_1 = "registration.us_agent.address_line_1"
    registration_us_agent_address_line_2 = "registration.us_agent.address_line_2"
    registration_us_agent_bus_phone_area_code = (
        "registration.us_agent.bus_phone_area_code"
    )
    registration_us_agent_bus_phone_extn = "registration.us_agent.bus_phone_extn"
    registration_us_agent_bus_phone_num = "registration.us_agent.bus_phone_num"
    registration_us_agent_business_name = "registration.us_agent.business_name"
    registration_us_agent_city = "registration.us_agent.city"
    registration_us_agent_email_address = "registration.us_agent.email_address"
    registration_us_agent_fax_area_code = "registration.us_agent.fax_area_code"
    registration_us_agent_fax_num = "registration.us_agent.fax_num"
    registration_us_agent_iso_country_code = "registration.us_agent.iso_country_code"
    registration_us_agent_name = "registration.us_agent.name"
    registration_us_agent_postal_code = "registration.us_agent.postal_code"
    registration_us_agent_state_code = "registration.us_agent.state_code"
    registration_us_agent_zip_code = "registration.us_agent.zip_code"
    registration_zip_code = "registration.zip_code"


class FDADeviceCovid19SerologySearchField(Enum):
    antibody_agree = "antibody_agree"
    antibody_truth = "antibody_truth"
    control = "control"
    date_performed = "date_performed"
    days_from_symptom = "days_from_symptom"
    device = "device"
    evaluation_id = "evaluation_id"
    group = "group"
    iga_agree = "iga_agree"
    iga_result = "iga_result"
    igg_agree = "igg_agree"
    igg_result = "igg_result"
    igg_titer = "igg_titer"
    igg_truth = "igg_truth"
    igm_agree = "igm_agree"
    igm_iga_agree = "igm_iga_agree"
    igm_iga_result = "igm_iga_result"
    igm_igg_agree = "igm_igg_agree"
    igm_igg_result = "igm_igg_result"
    igm_result = "igm_result"
    igm_titer = "igm_titer"
    igm_truth = "igm_truth"
    lot_number = "lot_number"
    manufacturer = "manufacturer"
    pan_agree = "pan_agree"
    pan_result = "pan_result"
    pan_titer = "pan_titer"
    panel = "panel"
    sample_id = "sample_id"
    sample_no = "sample_no"
    type = "type"


class FDADeviceUDISearchField(Enum):
    brand_name = "brand_name"
    catalog_number = "catalog_number"
    commercial_distribution_end_date = "commercial_distribution_end_date"
    commercial_distribution_status = "commercial_distribution_status"
    company_name = "company_name"
    customer_contacts_email = "customer_contacts.email"
    customer_contacts_phone = "customer_contacts.phone"
    device_count_in_base_package = "device_count_in_base_package"
    device_description = "device_description"
    device_sizes_text = "device_sizes.text"
    device_sizes_type = "device_sizes.type"
    device_sizes_unit = "device_sizes.unit"
    device_sizes_value = "device_sizes.value"
    gmdn_terms_code = "gmdn_terms.code"
    gmdn_terms_code_status = "gmdn_terms.code_status"
    gmdn_terms_definition = "gmdn_terms.definition"
    gmdn_terms_implantable = "gmdn_terms.implantable"
    gmdn_terms_name = "gmdn_terms.name"
    has_donation_id_number = "has_donation_id_number"
    has_expiration_date = "has_expiration_date"
    has_lot_or_batch_number = "has_lot_or_batch_number"
    has_manufacturing_date = "has_manufacturing_date"
    has_serial_number = "has_serial_number"
    identifiers_id = "identifiers.id"
    identifiers_issuing_agency = "identifiers.issuing_agency"
    identifiers_package_discontinue_date = "identifiers.package_discontinue_date"
    identifiers_package_status = "identifiers.package_status"
    identifiers_package_type = "identifiers.package_type"
    identifiers_quantity_per_package = "identifiers.quantity_per_package"
    identifiers_type = "identifiers.type"
    identifiers_unit_of_use_id = "identifiers.unit_of_use_id"
    is_combination_product = "is_combination_product"
    is_direct_marking_exempt = "is_direct_marking_exempt"
    is_hct_p = "is_hct_p"
    is_kit = "is_kit"
    is_labeled_as_no_nrl = "is_labeled_as_no_nrl"
    is_labeled_as_nrl = "is_labeled_as_nrl"
    is_otc = "is_otc"
    is_pm_exempt = "is_pm_exempt"
    is_rx = "is_rx"
    is_single_use = "is_single_use"
    labeler_duns_number = "labeler_duns_number"
    mri_safety = "mri_safety"
    premarket_submissions_submission_number = "premarket_submissions.submission_number"
    premarket_submissions_submission_type = "premarket_submissions.submission_type"
    premarket_submissions_supplement_number = "premarket_submissions.supplement_number"
    product_codes_code = "product_codes.code"
    product_codes_name = "product_codes.name"
    product_codes_openfda_device_class = "product_codes.openfda.device_class"
    product_codes_openfda_device_name = "product_codes.openfda.device_name"
    product_codes_openfda_medical_specialty_description = (
        "product_codes.openfda.medical_specialty_description"
    )
    product_codes_openfda_regulation_number = "product_codes.openfda.regulation_number"
    public_version_date = "public_version_date"
    public_version_number = "public_version_number"
    public_version_status = "public_version_status"
    publish_date = "publish_date"
    record_key = "record_key"
    record_status = "record_status"
    sterilization_is_sterile = "sterilization.is_sterile"
    sterilization_is_sterilization_prior_use = (
        "sterilization.is_sterilization_prior_use"
    )
    sterilization_sterilization_methods = "sterilization.sterilization_methods"
    storage_high_unit = "storage.high.unit"
    storage_high_value = "storage.high.value"
    storage_low_unit = "storage.low.unit"
    storage_low_value = "storage.low.value"
    storage_special_conditions = "storage.special_conditions"
    storage_type = "storage.type"
    version_or_model_number = "version_or_model_number"


class FDAFoodEventSearchField(Enum):
    consumer_age = "consumer.age"
    consumer_age_unit = "consumer.age_unit"
    consumer_gender = "consumer.gender"
    date_created = "date_created"
    date_started = "date_started"
    outcomes = "outcomes"
    products_industry_code = "products.industry_code"
    products_industry_name = "products.industry_name"
    products_name_brand = "products.name_brand"
    products_role = "products.role"
    reactions = "reactions"
    report_number = "report_number"


class FDAFoodEnforcementSearchField(Enum):
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


class FDACosmeticEventSearchField(Enum):
    report_number = "report_number"
    report_version = "report_version"
    legacy_report_id = "legacy_report_id"
    report_type = "report_type"
    initial_received_date = "initial_received_date"
    latest_received_date = "latest_received_date"
    event_date = "event_date"
    products_product_name = "products.product_name"
    products_role = "products.role"
    patient_age = "patient.age"
    patient_age_unit = "patient.age_unit"
    patient_gender = "patient.gender"
    reactions = "reactions"
    meddra_version = "meddra_version"
    outcomes = "outcomes"


class FDATobaccoProblemSearchField(Enum):
    report_id = "report_id"
    date_submitted = "date_submitted"
    number_tobacco_products = "number_tobacco_products"
    tobacco_products = "tobacco_products"
    number_health_problems = "number_health_problems"
    reported_health_problems = "reported_health_problems"
    nonuser_affected = "nonuser_affected"
    number_product_problems = "number_product_problems"
    reported_product_problems = "reported_product_problems"


class FDAOtherHistoricalDocumentSearchField(Enum):
    doc_type = "doc_type"
    year = "year"
    num_of_pages = "num_of_pages"
    text = "text"
    download_url = "download_url"


class FDAOtherNSDESearchField(Enum):
    package_ndc = "package_ndc"
    package_ndc11 = "package_ndc11"
    proprietary_name = "proprietary_name"
    dosage_form = "dosage_form"
    marketing_category = "marketing_category"
    application_number_or_citation = "application_number_or_citation"
    product_type = "product_type"
    marketing_start_date = "marketing_start_date"
    marketing_end_date = "marketing_end_date"
    billing_unit = "billing_unit"
    inactivation_date = "inactivation_date"
    reactivation_date = "reactivation_date"


class FDAOtherSubstanceSearchField(Enum):
    substance_name = "substance_name"
    unii = "unii"


SEARCH_FIELD_VALIDATION_RULES = {
    FDAAnimalVeterinaryEndpoint.event: _load_field_rules(
        "animalandveterinary_event_fields.yaml"
    ),
    FDADrugEndpoint.event: _load_field_rules("drug_event_fields.yaml"),
    FDADrugEndpoint.enforcement: _load_field_rules("drug_enforcement_fields.yaml"),
    FDADrugEndpoint.label: _load_field_rules("drug_label_fields.yaml"),
    FDADrugEndpoint.ndc: _load_field_rules("drug_ndc_fields.yaml"),
    FDADrugEndpoint.drugsfda: _load_field_rules("drug_drugsfda_fields.yaml"),
    FDADrugEndpoint.shortages: _load_field_rules("drug_shortages_fields.yaml"),
    FDADeviceEndpoint._510k: _load_field_rules("device_510k_fields.yaml"),
    FDADeviceEndpoint.classification: _load_field_rules("device_classification_fields.yaml"),
    FDADeviceEndpoint.enforcement: _load_field_rules("device_enforcement_fields.yaml"),
    FDADeviceEndpoint.event: _load_field_rules("device_event_fields.yaml"),
    FDADeviceEndpoint.pma: _load_field_rules("device_pma_fields.yaml"),
    FDADeviceEndpoint.recall: _load_field_rules("device_recall_fields.yaml"),
    FDADeviceEndpoint.registrationlisting: _load_field_rules("device_registrationlisting_fields.yaml"),
    FDADeviceEndpoint.covid19serology: _load_field_rules("device_covid19serology_fields.yaml"),
    FDADeviceEndpoint.udi: _load_field_rules("device_udi_fields.yaml"),
    FDAFoodEndpoint.event: _load_field_rules("food_event_fields.yaml"),
    FDAFoodEndpoint.enforcement: _load_field_rules("food_enforcement_fields.yaml"),
    FDACosmeticEndpoint.event: _load_field_rules("cosmetic_event_fields.yaml"),
    FDATobaccoEndpoint.problem: _load_field_rules("tobacco_problem_fields.yaml"),
    FDAOtherEndpoint.historicaldocument: _load_field_rules("other_historicaldocument_fields.yaml"),
    FDAOtherEndpoint.nsde: _load_field_rules("other_nsde_fields.yaml"),
    FDAOtherEndpoint.substance: _load_field_rules("other_substance_fields.yaml"),
}


SEARCH_FIELD_ENUMS = {
    FDAAnimalVeterinaryEndpoint.event: FDAAnimalVeterinaryEventSearchField,
    FDADrugEndpoint.event: FDADrugEventSearchField,
    FDADrugEndpoint.enforcement: FDADrugEnforcementSearchField,
    FDADrugEndpoint.label: FDADrugLabelSearchField,
    FDADrugEndpoint.ndc: FDADrugNDCSearchField,
    FDADrugEndpoint.drugsfda: FDADrugDrugsFDASearchField,
    FDADrugEndpoint.shortages: FDADrugShortagesSearchField,
    FDADeviceEndpoint._510k: FDADevice510kSearchField,
    FDADeviceEndpoint.classification: FDADeviceClassificationSearchField,
    FDADeviceEndpoint.enforcement: FDADeviceEnforcementSearchField,
    FDADeviceEndpoint.event: FDADeviceEventSearchField,
    FDADeviceEndpoint.pma: FDADevicePMASearchField,
    FDADeviceEndpoint.recall: FDADeviceRecallSearchField,
    FDADeviceEndpoint.registrationlisting: FDADeviceRegistrationListingSearchField,
    FDADeviceEndpoint.covid19serology: FDADeviceCovid19SerologySearchField,
    FDADeviceEndpoint.udi: FDADeviceUDISearchField,
    FDAFoodEndpoint.event: FDAFoodEventSearchField,
    FDAFoodEndpoint.enforcement: FDAFoodEnforcementSearchField,
    FDACosmeticEndpoint.event: FDACosmeticEventSearchField,
    FDATobaccoEndpoint.problem: FDATobaccoProblemSearchField,
    FDAOtherEndpoint.historicaldocument: FDAOtherHistoricalDocumentSearchField,
    FDAOtherEndpoint.nsde: FDAOtherNSDESearchField,
    FDAOtherEndpoint.substance: FDAOtherSubstanceSearchField,
}


VALID_ENDPOINTS = {
    FDACategory.animalandveterinary: FDAAnimalVeterinaryEndpoint,
    FDACategory.drug: FDADrugEndpoint,
    FDACategory.device: FDADeviceEndpoint,
    FDACategory.food: FDAFoodEndpoint,
    FDACategory.cosmetic: FDACosmeticEndpoint,
    FDACategory.tobacco: FDATobaccoEndpoint,
    FDACategory.other: FDAOtherEndpoint,
}


class FDAModel(BaseModel):
    model_config = ConfigDict(use_enum_values=True)
    category: FDACategory
    endpoint: (
        FDAAnimalVeterinaryEndpoint
        | FDADrugEndpoint
        | FDADeviceEndpoint
        | FDAFoodEndpoint
        | FDACosmeticEndpoint
        | FDATobaccoEndpoint
        | FDAOtherEndpoint
    )
    search: Optional[Dict[str, Any]] = None
    count: Optional[str] = None
    skip: Optional[int] = None
    sort: Optional[str] = None
    limit: Optional[int] = None

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
    def check_valid_limit_value(self):
        if self.limit is not None:
            if not (1 <= self.limit <= 1000):
                raise ValueError("limit must be between 1 and 1000")
        return self

    @model_validator(mode="after")
    def check_valid_search_values(self):
        search_field_enum_value_dic = {
            k.value: v for k, v in SEARCH_FIELD_ENUMS.items() if k in VALID_ENDPOINTS[FDACategory(self.category)]
        }
        search_field_validation_rules = {
            k.value: v for k, v in SEARCH_FIELD_VALIDATION_RULES.items()
        }

        if self.endpoint not in search_field_enum_value_dic:
            raise ValueError(f"Invalid endpoint '{self.endpoint}'")

        valid_field_values = {
            field.value for field in search_field_enum_value_dic[self.endpoint]
        }
        rules_map = search_field_validation_rules[self.endpoint]
        for field_path, value in self.search.items():
            if field_path not in valid_field_values:
                raise ValueError(
                    f"Invalid search field '{field_path}'. Must be one of: {sorted(valid_field_values)} for the endpoint '{self.endpoint}'"
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

    try:
        invalid_model = FDAModel(
            category="drug", endpoint="event", search={"strength": "10"}
        )
    except ValidationError as e:
        print(e)

    print(valid_model)
    print(valid_model.model_dump())
