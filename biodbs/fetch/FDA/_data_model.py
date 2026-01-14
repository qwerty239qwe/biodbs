from enum import Enum
from pydantic import BaseModel, model_validator, ConfigDict
from typing import Dict, Any


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


VALID_ENDPOINTS = {
    FDACategory("drug"): FDADrugEndpoint,
    FDACategory("food"): FDAFoodEndpoint,
}


class FDAModel(BaseModel):
    model_config = ConfigDict(use_enum_values=True)
    category: FDACategory
    endpoint: FDADrugEndpoint | FDAFoodEndpoint
    search: Dict[FDADrugEventSearchField, Any]

    @model_validator(mode="after")
    def check_valid_endpoint(self):
        valid_endpoints = VALID_ENDPOINTS[FDACategory(self.category)]
        valid_values = [val.value for val in valid_endpoints]
        if self.endpoint not in valid_values:
            raise ValueError(
                f"{self.endpoint} is not a valid endpoint for {self.category}. Please choose from {valid_values}"
            )
        return self


if __name__ == "__main__":
    valid_model = FDAModel(category="drug", endpoint="event")

    print(valid_model)
    print(valid_model.model_dump())
