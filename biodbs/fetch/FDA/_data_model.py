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
    FDADrugEndpoint.label: FDADrugLabelSearchField,
    FDADrugEndpoint.ndc: FDADrugNDCSearchField,
    FDADrugEndpoint.drugsfda: FDADrugDrugsFDASearchField,
    FDADrugEndpoint.shortages: FDADrugShortagesSearchField,
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
        search_field_enum_value_dic = {k.value: v for k, v in SEARCH_FIELD_ENUMS.items()}
        search_field_validation_rules = {k.value: v for k, v in SEARCH_FIELD_VALIDATION_RULES.items()}

        if self.endpoint not in search_field_enum_value_dic:
            raise ValueError(f"Invalid endpoint '{self.endpoint}'")

        valid_field_values = {
            field.value for field in search_field_enum_value_dic[self.endpoint]
        }
        rules_map = search_field_validation_rules[self.endpoint]
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

    try:
        invalid_model = FDAModel(
            category="drug",
            endpoint="event",
            search={"strength": "10"}
        )
    except ValidationError as e:
        print(e)

    print(valid_model)
    print(valid_model.model_dump())
