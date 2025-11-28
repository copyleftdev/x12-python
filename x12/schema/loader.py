"""
X12 Schema loader.

Loads and provides access to X12 transaction schemas.
"""
from __future__ import annotations

from x12.schema.definitions import (
    ElementDefinition,
    SegmentDefinition,
    LoopDefinition,
    TransactionSchema,
)


class SchemaLoader:
    """Loads X12 transaction schemas.
    
    Provides access to predefined schemas for common X12 transactions.
    
    Example:
        >>> loader = SchemaLoader()
        >>> schema = loader.load("005010X222A1")
        >>> print(schema.name)
        Health Care Claim: Professional
    """
    
    def __init__(self) -> None:
        """Initialize schema loader with built-in schemas."""
        self._schemas: dict[str, TransactionSchema] = {}
        self._load_builtin_schemas()
    
    def _load_builtin_schemas(self) -> None:
        """Load built-in schema definitions."""
        # Healthcare - HIPAA 5010
        self._schemas["005010X222A1"] = self._build_837p_schema()  # 837P Professional
        self._schemas["005010X223A3"] = self._build_837i_schema()  # 837I Institutional
        self._schemas["005010X224A3"] = self._build_837d_schema()  # 837D Dental
        self._schemas["005010X221A1"] = self._build_835_schema()   # 835 Remittance
        self._schemas["005010X279A1"] = self._build_270_schema()   # 270/271 Eligibility
        self._schemas["005010X212"] = self._build_276_schema()     # 276/277 Claim Status
        self._schemas["005010X220A1"] = self._build_834_schema()   # 834 Enrollment
        self._schemas["005010X217"] = self._build_278_schema()     # 278 Authorization
        self._schemas["005010X218"] = self._build_820_schema()     # 820 Premium Payment
        
        # Supply Chain - 4010
        self._schemas["004010"] = self._build_850_schema()         # 850 Purchase Order
        self._schemas["004010_856"] = self._build_856_schema()     # 856 Ship Notice
        self._schemas["004010_810"] = self._build_810_schema()     # 810 Invoice
        self._schemas["004010_855"] = self._build_855_schema()     # 855 PO Acknowledgment
        self._schemas["004010_860"] = self._build_860_schema()     # 860 PO Change
    
    def load(self, version: str) -> TransactionSchema | None:
        """Load schema by version identifier.
        
        Args:
            version: Implementation guide version (e.g., "005010X222A1").
            
        Returns:
            TransactionSchema or None if not found.
        """
        return self._schemas.get(version)
    
    def load_by_transaction(
        self,
        transaction_set_id: str,
        base_version: str = "005010",
    ) -> TransactionSchema | None:
        """Load schema by transaction type.
        
        Args:
            transaction_set_id: Transaction type (e.g., "837", "835").
            base_version: Base X12 version.
            
        Returns:
            TransactionSchema or None if not found.
        """
        for version, schema in self._schemas.items():
            if schema.transaction_set_id == transaction_set_id:
                if base_version in version:
                    return schema
        return None
    
    def list_versions(self) -> list[str]:
        """List all available schema versions.
        
        Returns:
            List of version identifiers.
        """
        return list(self._schemas.keys())
    
    def _build_837p_schema(self) -> TransactionSchema:
        """Build 837P Professional Claim schema."""
        schema = TransactionSchema(
            version="005010X222A1",
            transaction_set_id="837",
            name="Health Care Claim: Professional",
            functional_group_id="HC",
        )
        
        # NM1 - Individual or Organizational Name
        schema.segment_definitions["NM1"] = SegmentDefinition(
            segment_id="NM1",
            name="Individual or Organizational Name",
            elements=[
                ElementDefinition(position=1, name="Entity Identifier Code", required=True, data_type="ID", min_length=2, max_length=3,
                    valid_values=["85", "87", "IL", "PR", "QC", "DN", "77", "DQ", "PW", "45", "FA", "71", "72", "73", "74", "82", "DD", "DK", "P3", "PE"]),
                ElementDefinition(position=2, name="Entity Type Qualifier", required=True, data_type="ID", min_length=1, max_length=1,
                    valid_values=["1", "2"]),
                ElementDefinition(position=3, name="Name Last or Organization Name", required=False, data_type="AN", min_length=1, max_length=60),
                ElementDefinition(position=4, name="Name First", required=False, data_type="AN", min_length=1, max_length=35),
                ElementDefinition(position=5, name="Name Middle", required=False, data_type="AN", min_length=1, max_length=25),
                ElementDefinition(position=6, name="Name Prefix", required=False, data_type="AN", min_length=1, max_length=10),
                ElementDefinition(position=7, name="Name Suffix", required=False, data_type="AN", min_length=1, max_length=10),
                ElementDefinition(position=8, name="Identification Code Qualifier", required=False, data_type="ID", min_length=1, max_length=2,
                    valid_values=["24", "34", "46", "MI", "XX"]),
                ElementDefinition(position=9, name="Identification Code", required=False, data_type="AN", min_length=2, max_length=80),
            ],
        )
        
        # CLM - Claim Information
        schema.segment_definitions["CLM"] = SegmentDefinition(
            segment_id="CLM",
            name="Claim Information",
            elements=[
                ElementDefinition(position=1, name="Claim Submitter's Identifier", required=True, data_type="AN", min_length=1, max_length=38),
                ElementDefinition(position=2, name="Total Claim Charge Amount", required=True, data_type="N2", min_length=1, max_length=18),
                ElementDefinition(position=3, name="Claim Filing Indicator Code", required=False, data_type="ID", min_length=1, max_length=2),
                ElementDefinition(position=4, name="Non-Institutional Claim Type Code", required=False, data_type="ID", min_length=1, max_length=2),
                ElementDefinition(position=5, name="Health Care Service Location Information", required=True, data_type="AN", min_length=1, max_length=15),
            ],
        )
        
        # DTP - Date/Time Reference
        schema.segment_definitions["DTP"] = SegmentDefinition(
            segment_id="DTP",
            name="Date or Time Period",
            elements=[
                ElementDefinition(position=1, name="Date/Time Qualifier", required=True, data_type="ID", min_length=3, max_length=3),
                ElementDefinition(position=2, name="Date Time Period Format Qualifier", required=True, data_type="ID", min_length=2, max_length=3,
                    valid_values=["D8", "RD8"]),
                ElementDefinition(position=3, name="Date Time Period", required=True, data_type="AN", min_length=1, max_length=35),
            ],
        )
        
        # SV1 - Professional Service
        schema.segment_definitions["SV1"] = SegmentDefinition(
            segment_id="SV1",
            name="Professional Service",
            elements=[
                ElementDefinition(position=1, name="Composite Medical Procedure Identifier", required=True, data_type="AN", min_length=1, max_length=50),
                ElementDefinition(position=2, name="Line Item Charge Amount", required=True, data_type="N2", min_length=1, max_length=18),
                ElementDefinition(position=3, name="Unit or Basis for Measurement Code", required=False, data_type="ID", min_length=2, max_length=2),
                ElementDefinition(position=4, name="Service Unit Count", required=False, data_type="N0", min_length=1, max_length=15),
            ],
        )
        
        # HI - Health Care Information Codes
        schema.segment_definitions["HI"] = SegmentDefinition(
            segment_id="HI",
            name="Health Care Information Codes",
            elements=[
                ElementDefinition(position=1, name="Health Care Code Information", required=True, data_type="AN", min_length=1, max_length=30),
            ],
        )
        
        # REF - Reference Information
        schema.segment_definitions["REF"] = SegmentDefinition(
            segment_id="REF",
            name="Reference Information",
            elements=[
                ElementDefinition(position=1, name="Reference Identification Qualifier", required=True, data_type="ID", min_length=2, max_length=3),
                ElementDefinition(position=2, name="Reference Identification", required=False, data_type="AN", min_length=1, max_length=50),
            ],
        )
        
        # N3 - Address Information
        schema.segment_definitions["N3"] = SegmentDefinition(
            segment_id="N3",
            name="Party Location",
            elements=[
                ElementDefinition(position=1, name="Address Information", required=True, data_type="AN", min_length=1, max_length=55),
                ElementDefinition(position=2, name="Address Information", required=False, data_type="AN", min_length=1, max_length=55),
            ],
        )
        
        # N4 - Geographic Location
        schema.segment_definitions["N4"] = SegmentDefinition(
            segment_id="N4",
            name="Geographic Location",
            elements=[
                ElementDefinition(position=1, name="City Name", required=False, data_type="AN", min_length=2, max_length=30),
                ElementDefinition(position=2, name="State or Province Code", required=False, data_type="ID", min_length=2, max_length=2),
                ElementDefinition(position=3, name="Postal Code", required=False, data_type="ID", min_length=3, max_length=15),
            ],
        )
        
        # Loop definitions
        schema.loop_definitions["2000A"] = LoopDefinition(
            loop_id="2000A",
            name="Billing Provider Hierarchical Level",
            segments=["HL", "PRV"],
            child_loops=["2010AA", "2010AB"],
            min_occurs=1,
            max_occurs=None,
        )
        
        schema.loop_definitions["2010AA"] = LoopDefinition(
            loop_id="2010AA",
            name="Billing Provider Name",
            segments=["NM1", "N3", "N4", "REF", "PER"],
            min_occurs=1,
            max_occurs=1,
        )
        
        schema.loop_definitions["2000B"] = LoopDefinition(
            loop_id="2000B",
            name="Subscriber Hierarchical Level",
            segments=["HL", "SBR"],
            child_loops=["2010BA", "2010BB", "2300"],
            min_occurs=1,
            max_occurs=None,
        )
        
        schema.loop_definitions["2300"] = LoopDefinition(
            loop_id="2300",
            name="Claim Information",
            segments=["CLM", "DTP", "REF", "HI"],
            child_loops=["2400"],
            min_occurs=1,
            max_occurs=100,
        )
        
        schema.loop_definitions["2400"] = LoopDefinition(
            loop_id="2400",
            name="Service Line",
            segments=["LX", "SV1", "DTP", "REF"],
            min_occurs=1,
            max_occurs=50,
        )
        
        return schema
    
    def _build_835_schema(self) -> TransactionSchema:
        """Build 835 Remittance Advice schema."""
        schema = TransactionSchema(
            version="005010X221A1",
            transaction_set_id="835",
            name="Health Care Claim Payment/Advice",
            functional_group_id="HP",
        )
        
        # Copy common segments from 837P
        schema.segment_definitions["NM1"] = self._build_837p_schema().segment_definitions["NM1"]
        schema.segment_definitions["REF"] = self._build_837p_schema().segment_definitions["REF"]
        schema.segment_definitions["DTP"] = self._build_837p_schema().segment_definitions["DTP"]
        
        # Basic segment definitions for 835
        schema.segment_definitions["CLP"] = SegmentDefinition(
            segment_id="CLP",
            name="Claim Payment Information",
            elements=[
                ElementDefinition(position=1, name="Claim Submitter's Identifier", required=True, data_type="AN", min_length=1, max_length=38),
                ElementDefinition(position=2, name="Claim Status Code", required=True, data_type="ID", min_length=1, max_length=2),
                ElementDefinition(position=3, name="Total Claim Charge Amount", required=True, data_type="N2", min_length=1, max_length=18),
                ElementDefinition(position=4, name="Claim Payment Amount", required=True, data_type="N2", min_length=1, max_length=18),
            ],
        )
        
        schema.segment_definitions["SVC"] = SegmentDefinition(
            segment_id="SVC",
            name="Service Payment Information",
            elements=[
                ElementDefinition(position=1, name="Composite Medical Procedure Identifier", required=True, data_type="AN", min_length=1, max_length=50),
                ElementDefinition(position=2, name="Line Item Charge Amount", required=True, data_type="N2", min_length=1, max_length=18),
                ElementDefinition(position=3, name="Line Item Provider Payment Amount", required=True, data_type="N2", min_length=1, max_length=18),
            ],
        )
        
        return schema
    
    def _build_270_schema(self) -> TransactionSchema:
        """Build 270/271 Eligibility Inquiry/Response schema."""
        schema = TransactionSchema(
            version="005010X279A1",
            transaction_set_id="270",
            name="Health Care Eligibility Benefit Inquiry/Response",
            functional_group_id="HS",
        )
        
        # Copy NM1 from 837P
        schema.segment_definitions["NM1"] = self._build_837p_schema().segment_definitions["NM1"]
        schema.segment_definitions["REF"] = self._build_837p_schema().segment_definitions["REF"]
        schema.segment_definitions["DTP"] = self._build_837p_schema().segment_definitions["DTP"]
        
        schema.segment_definitions["EQ"] = SegmentDefinition(
            segment_id="EQ",
            name="Eligibility or Benefit Inquiry",
            elements=[
                ElementDefinition(position=1, name="Service Type Code", required=True, data_type="ID", min_length=1, max_length=2),
                ElementDefinition(position=2, name="Composite Medical Procedure Identifier", required=False, data_type="AN", min_length=1, max_length=50),
            ],
        )
        
        # EB - Eligibility or Benefit Information (271 Response)
        schema.segment_definitions["EB"] = SegmentDefinition(
            segment_id="EB",
            name="Eligibility or Benefit Information",
            elements=[
                ElementDefinition(position=1, name="Eligibility or Benefit Information Code", required=True, data_type="ID", min_length=1, max_length=2),
                ElementDefinition(position=2, name="Coverage Level Code", required=False, data_type="ID", min_length=3, max_length=3),
                ElementDefinition(position=3, name="Service Type Code", required=False, data_type="ID", min_length=1, max_length=2),
                ElementDefinition(position=4, name="Insurance Type Code", required=False, data_type="ID", min_length=1, max_length=3),
                ElementDefinition(position=5, name="Plan Coverage Description", required=False, data_type="AN", min_length=1, max_length=50),
                ElementDefinition(position=6, name="Time Period Qualifier", required=False, data_type="ID", min_length=1, max_length=2),
                ElementDefinition(position=7, name="Monetary Amount", required=False, data_type="N2", min_length=1, max_length=18),
            ],
        )
        
        return schema
    
    def _build_850_schema(self) -> TransactionSchema:
        """Build 850 Purchase Order schema."""
        schema = TransactionSchema(
            version="004010",
            transaction_set_id="850",
            name="Purchase Order",
            functional_group_id="PO",
        )
        
        schema.segment_definitions["BEG"] = SegmentDefinition(
            segment_id="BEG",
            name="Beginning Segment for Purchase Order",
            elements=[
                ElementDefinition(position=1, name="Transaction Set Purpose Code", required=True, data_type="ID", min_length=2, max_length=2),
                ElementDefinition(position=2, name="Purchase Order Type Code", required=True, data_type="ID", min_length=2, max_length=2),
                ElementDefinition(position=3, name="Purchase Order Number", required=True, data_type="AN", min_length=1, max_length=22),
                ElementDefinition(position=5, name="Date", required=True, data_type="DT", min_length=8, max_length=8),
            ],
        )
        
        schema.segment_definitions["PO1"] = SegmentDefinition(
            segment_id="PO1",
            name="Baseline Item Data",
            elements=[
                ElementDefinition(position=1, name="Assigned Identification", required=False, data_type="AN", min_length=1, max_length=20),
                ElementDefinition(position=2, name="Quantity Ordered", required=True, data_type="N0", min_length=1, max_length=15),
                ElementDefinition(position=3, name="Unit or Basis for Measurement Code", required=True, data_type="ID", min_length=2, max_length=2),
                ElementDefinition(position=4, name="Unit Price", required=True, data_type="N2", min_length=1, max_length=17),
            ],
        )
        
        return schema
    
    def _build_837i_schema(self) -> TransactionSchema:
        """Build 837I Institutional Claim schema."""
        schema = TransactionSchema(
            version="005010X223A3",
            transaction_set_id="837",
            name="Health Care Claim: Institutional",
            functional_group_id="HC",
        )
        
        # Copy common segments from 837P
        schema.segment_definitions["NM1"] = self._build_837p_schema().segment_definitions["NM1"]
        schema.segment_definitions["CLM"] = self._build_837p_schema().segment_definitions["CLM"]
        schema.segment_definitions["DTP"] = self._build_837p_schema().segment_definitions["DTP"]
        schema.segment_definitions["REF"] = self._build_837p_schema().segment_definitions["REF"]
        schema.segment_definitions["HI"] = self._build_837p_schema().segment_definitions["HI"]
        schema.segment_definitions["N3"] = self._build_837p_schema().segment_definitions["N3"]
        schema.segment_definitions["N4"] = self._build_837p_schema().segment_definitions["N4"]
        
        # CL1 - Institutional Claim Code
        schema.segment_definitions["CL1"] = SegmentDefinition(
            segment_id="CL1",
            name="Institutional Claim Code",
            elements=[
                ElementDefinition(position=1, name="Admission Type Code", required=False, data_type="ID", min_length=1, max_length=1),
                ElementDefinition(position=2, name="Admission Source Code", required=False, data_type="ID", min_length=1, max_length=1),
                ElementDefinition(position=3, name="Patient Status Code", required=False, data_type="ID", min_length=1, max_length=2),
            ],
        )
        
        # SV2 - Institutional Service Line
        schema.segment_definitions["SV2"] = SegmentDefinition(
            segment_id="SV2",
            name="Institutional Service Line",
            elements=[
                ElementDefinition(position=1, name="Revenue Code", required=True, data_type="AN", min_length=1, max_length=48),
                ElementDefinition(position=2, name="Composite Medical Procedure Identifier", required=False, data_type="AN", min_length=1, max_length=50),
                ElementDefinition(position=3, name="Line Item Charge Amount", required=True, data_type="N2", min_length=1, max_length=18),
                ElementDefinition(position=4, name="Unit or Basis for Measurement Code", required=False, data_type="ID", min_length=2, max_length=2),
                ElementDefinition(position=5, name="Service Unit Count", required=False, data_type="N0", min_length=1, max_length=15),
            ],
        )
        
        return schema
    
    def _build_837d_schema(self) -> TransactionSchema:
        """Build 837D Dental Claim schema."""
        schema = TransactionSchema(
            version="005010X224A3",
            transaction_set_id="837",
            name="Health Care Claim: Dental",
            functional_group_id="HC",
        )
        
        # Copy common segments
        schema.segment_definitions["NM1"] = self._build_837p_schema().segment_definitions["NM1"]
        schema.segment_definitions["CLM"] = self._build_837p_schema().segment_definitions["CLM"]
        schema.segment_definitions["DTP"] = self._build_837p_schema().segment_definitions["DTP"]
        schema.segment_definitions["REF"] = self._build_837p_schema().segment_definitions["REF"]
        schema.segment_definitions["N3"] = self._build_837p_schema().segment_definitions["N3"]
        schema.segment_definitions["N4"] = self._build_837p_schema().segment_definitions["N4"]
        
        # DN1 - Orthodontic Information
        schema.segment_definitions["DN1"] = SegmentDefinition(
            segment_id="DN1",
            name="Orthodontic Information",
            elements=[
                ElementDefinition(position=1, name="Quantity", required=False, data_type="N0", min_length=1, max_length=15),
                ElementDefinition(position=2, name="Quantity", required=False, data_type="N0", min_length=1, max_length=15),
                ElementDefinition(position=3, name="Yes/No Condition", required=False, data_type="ID", min_length=1, max_length=1),
                ElementDefinition(position=4, name="Description", required=False, data_type="AN", min_length=1, max_length=80),
            ],
        )
        
        # DN2 - Tooth Status
        schema.segment_definitions["DN2"] = SegmentDefinition(
            segment_id="DN2",
            name="Tooth Status",
            elements=[
                ElementDefinition(position=1, name="Tooth Number", required=True, data_type="AN", min_length=1, max_length=50),
                ElementDefinition(position=2, name="Tooth Status Code", required=True, data_type="ID", min_length=1, max_length=2),
            ],
        )
        
        # SV3 - Dental Service
        schema.segment_definitions["SV3"] = SegmentDefinition(
            segment_id="SV3",
            name="Dental Service",
            elements=[
                ElementDefinition(position=1, name="Composite Medical Procedure Identifier", required=True, data_type="AN", min_length=1, max_length=50),
                ElementDefinition(position=2, name="Line Item Charge Amount", required=True, data_type="N2", min_length=1, max_length=18),
            ],
        )
        
        return schema
    
    def _build_276_schema(self) -> TransactionSchema:
        """Build 276/277 Claim Status schema."""
        schema = TransactionSchema(
            version="005010X212",
            transaction_set_id="276",
            name="Health Care Claim Status Request/Response",
            functional_group_id="HR",
        )
        
        schema.segment_definitions["NM1"] = self._build_837p_schema().segment_definitions["NM1"]
        
        # TRN - Trace
        schema.segment_definitions["TRN"] = SegmentDefinition(
            segment_id="TRN",
            name="Trace",
            elements=[
                ElementDefinition(position=1, name="Trace Type Code", required=True, data_type="ID", min_length=1, max_length=2),
                ElementDefinition(position=2, name="Reference Identification", required=True, data_type="AN", min_length=1, max_length=50),
            ],
        )
        
        # STC - Status Information
        schema.segment_definitions["STC"] = SegmentDefinition(
            segment_id="STC",
            name="Status Information",
            elements=[
                ElementDefinition(position=1, name="Health Care Claim Status", required=True, data_type="AN", min_length=1, max_length=50),
            ],
        )
        
        return schema
    
    def _build_834_schema(self) -> TransactionSchema:
        """Build 834 Benefit Enrollment schema."""
        schema = TransactionSchema(
            version="005010X220A1",
            transaction_set_id="834",
            name="Benefit Enrollment and Maintenance",
            functional_group_id="BE",
        )
        
        schema.segment_definitions["NM1"] = self._build_837p_schema().segment_definitions["NM1"]
        schema.segment_definitions["N3"] = self._build_837p_schema().segment_definitions["N3"]
        schema.segment_definitions["N4"] = self._build_837p_schema().segment_definitions["N4"]
        schema.segment_definitions["REF"] = self._build_837p_schema().segment_definitions["REF"]
        schema.segment_definitions["DTP"] = self._build_837p_schema().segment_definitions["DTP"]
        
        # INS - Member Level Detail
        schema.segment_definitions["INS"] = SegmentDefinition(
            segment_id="INS",
            name="Member Level Detail",
            elements=[
                ElementDefinition(position=1, name="Yes/No Condition", required=True, data_type="ID", min_length=1, max_length=1),
                ElementDefinition(position=2, name="Individual Relationship Code", required=True, data_type="ID", min_length=2, max_length=2),
                ElementDefinition(position=3, name="Maintenance Type Code", required=True, data_type="ID", min_length=3, max_length=3),
                ElementDefinition(position=4, name="Maintenance Reason Code", required=False, data_type="ID", min_length=2, max_length=3),
            ],
        )
        
        # HD - Health Coverage
        schema.segment_definitions["HD"] = SegmentDefinition(
            segment_id="HD",
            name="Health Coverage",
            elements=[
                ElementDefinition(position=1, name="Maintenance Type Code", required=True, data_type="ID", min_length=3, max_length=3),
                ElementDefinition(position=3, name="Insurance Line Code", required=False, data_type="ID", min_length=1, max_length=3),
                ElementDefinition(position=4, name="Plan Coverage Description", required=False, data_type="AN", min_length=1, max_length=50),
            ],
        )
        
        # DMG - Demographic Information
        schema.segment_definitions["DMG"] = SegmentDefinition(
            segment_id="DMG",
            name="Demographic Information",
            elements=[
                ElementDefinition(position=1, name="Date Time Period Format Qualifier", required=False, data_type="ID", min_length=2, max_length=3),
                ElementDefinition(position=2, name="Date Time Period", required=False, data_type="AN", min_length=1, max_length=35),
                ElementDefinition(position=3, name="Gender Code", required=False, data_type="ID", min_length=1, max_length=1),
            ],
        )
        
        return schema
    
    def _build_278_schema(self) -> TransactionSchema:
        """Build 278 Prior Authorization schema."""
        schema = TransactionSchema(
            version="005010X217",
            transaction_set_id="278",
            name="Health Care Services Review",
            functional_group_id="HI",
        )
        
        schema.segment_definitions["NM1"] = self._build_837p_schema().segment_definitions["NM1"]
        schema.segment_definitions["DTP"] = self._build_837p_schema().segment_definitions["DTP"]
        schema.segment_definitions["REF"] = self._build_837p_schema().segment_definitions["REF"]
        
        # UM - Health Care Services Review Information
        schema.segment_definitions["UM"] = SegmentDefinition(
            segment_id="UM",
            name="Health Care Services Review Information",
            elements=[
                ElementDefinition(position=1, name="Request Category Code", required=True, data_type="ID", min_length=1, max_length=2),
                ElementDefinition(position=2, name="Certification Type Code", required=True, data_type="ID", min_length=1, max_length=1),
                ElementDefinition(position=3, name="Service Type Code", required=False, data_type="ID", min_length=1, max_length=2),
            ],
        )
        
        # HCR - Health Care Services Review
        schema.segment_definitions["HCR"] = SegmentDefinition(
            segment_id="HCR",
            name="Health Care Services Review",
            elements=[
                ElementDefinition(position=1, name="Action Code", required=True, data_type="ID", min_length=1, max_length=2),
                ElementDefinition(position=2, name="Reference Identification", required=False, data_type="AN", min_length=1, max_length=50),
            ],
        )
        
        return schema
    
    def _build_820_schema(self) -> TransactionSchema:
        """Build 820 Premium Payment schema."""
        schema = TransactionSchema(
            version="005010X218",
            transaction_set_id="820",
            name="Payment Order/Remittance Advice",
            functional_group_id="RA",
        )
        
        schema.segment_definitions["NM1"] = self._build_837p_schema().segment_definitions["NM1"]
        schema.segment_definitions["N3"] = self._build_837p_schema().segment_definitions["N3"]
        schema.segment_definitions["N4"] = self._build_837p_schema().segment_definitions["N4"]
        schema.segment_definitions["REF"] = self._build_837p_schema().segment_definitions["REF"]
        
        # BPR - Financial Information
        schema.segment_definitions["BPR"] = SegmentDefinition(
            segment_id="BPR",
            name="Financial Information",
            elements=[
                ElementDefinition(position=1, name="Transaction Handling Code", required=True, data_type="ID", min_length=1, max_length=2),
                ElementDefinition(position=2, name="Monetary Amount", required=True, data_type="N2", min_length=1, max_length=18),
                ElementDefinition(position=3, name="Credit/Debit Flag Code", required=True, data_type="ID", min_length=1, max_length=1),
            ],
        )
        
        # ENT - Entity
        schema.segment_definitions["ENT"] = SegmentDefinition(
            segment_id="ENT",
            name="Entity",
            elements=[
                ElementDefinition(position=1, name="Assigned Number", required=False, data_type="N0", min_length=1, max_length=6),
                ElementDefinition(position=2, name="Entity Identifier Code", required=False, data_type="ID", min_length=2, max_length=3),
            ],
        )
        
        # RMR - Remittance Advice Accounts Receivable Open Item Reference
        schema.segment_definitions["RMR"] = SegmentDefinition(
            segment_id="RMR",
            name="Remittance Advice Accounts Receivable",
            elements=[
                ElementDefinition(position=1, name="Reference Identification Qualifier", required=False, data_type="ID", min_length=2, max_length=3),
                ElementDefinition(position=2, name="Reference Identification", required=False, data_type="AN", min_length=1, max_length=50),
                ElementDefinition(position=4, name="Monetary Amount", required=False, data_type="N2", min_length=1, max_length=18),
            ],
        )
        
        return schema
    
    def _build_856_schema(self) -> TransactionSchema:
        """Build 856 Ship Notice/Manifest schema."""
        schema = TransactionSchema(
            version="004010_856",
            transaction_set_id="856",
            name="Ship Notice/Manifest",
            functional_group_id="SH",
        )
        
        # BSN - Beginning Segment for Ship Notice
        schema.segment_definitions["BSN"] = SegmentDefinition(
            segment_id="BSN",
            name="Beginning Segment for Ship Notice",
            elements=[
                ElementDefinition(position=1, name="Transaction Set Purpose Code", required=True, data_type="ID", min_length=2, max_length=2),
                ElementDefinition(position=2, name="Shipment Identification", required=True, data_type="AN", min_length=2, max_length=30),
                ElementDefinition(position=3, name="Date", required=True, data_type="DT", min_length=8, max_length=8),
                ElementDefinition(position=4, name="Time", required=True, data_type="TM", min_length=4, max_length=8),
            ],
        )
        
        # HL - Hierarchical Level
        schema.segment_definitions["HL"] = SegmentDefinition(
            segment_id="HL",
            name="Hierarchical Level",
            elements=[
                ElementDefinition(position=1, name="Hierarchical ID Number", required=True, data_type="AN", min_length=1, max_length=12),
                ElementDefinition(position=2, name="Hierarchical Parent ID Number", required=False, data_type="AN", min_length=1, max_length=12),
                ElementDefinition(position=3, name="Hierarchical Level Code", required=True, data_type="ID", min_length=1, max_length=2),
                ElementDefinition(position=4, name="Hierarchical Child Code", required=False, data_type="ID", min_length=1, max_length=1),
            ],
        )
        
        # TD1 - Carrier Details (Quantity and Weight)
        schema.segment_definitions["TD1"] = SegmentDefinition(
            segment_id="TD1",
            name="Carrier Details (Quantity and Weight)",
            elements=[
                ElementDefinition(position=1, name="Packaging Code", required=False, data_type="AN", min_length=3, max_length=5),
                ElementDefinition(position=2, name="Lading Quantity", required=False, data_type="N0", min_length=1, max_length=7),
            ],
        )
        
        # TD5 - Carrier Details (Routing Sequence/Transit Time)
        schema.segment_definitions["TD5"] = SegmentDefinition(
            segment_id="TD5",
            name="Carrier Details (Routing)",
            elements=[
                ElementDefinition(position=1, name="Routing Sequence Code", required=False, data_type="ID", min_length=1, max_length=2),
                ElementDefinition(position=2, name="Identification Code Qualifier", required=False, data_type="ID", min_length=1, max_length=2),
                ElementDefinition(position=3, name="Identification Code", required=False, data_type="AN", min_length=2, max_length=80),
            ],
        )
        
        # REF - Reference
        schema.segment_definitions["REF"] = self._build_837p_schema().segment_definitions["REF"]
        
        # SN1 - Item Detail (Shipment)
        schema.segment_definitions["SN1"] = SegmentDefinition(
            segment_id="SN1",
            name="Item Detail (Shipment)",
            elements=[
                ElementDefinition(position=1, name="Assigned Identification", required=False, data_type="AN", min_length=1, max_length=20),
                ElementDefinition(position=2, name="Number of Units Shipped", required=True, data_type="N0", min_length=1, max_length=10),
                ElementDefinition(position=3, name="Unit or Basis for Measurement Code", required=True, data_type="ID", min_length=2, max_length=2),
            ],
        )
        
        return schema
    
    def _build_810_schema(self) -> TransactionSchema:
        """Build 810 Invoice schema."""
        schema = TransactionSchema(
            version="004010_810",
            transaction_set_id="810",
            name="Invoice",
            functional_group_id="IN",
        )
        
        # BIG - Beginning Segment for Invoice
        schema.segment_definitions["BIG"] = SegmentDefinition(
            segment_id="BIG",
            name="Beginning Segment for Invoice",
            elements=[
                ElementDefinition(position=1, name="Date", required=True, data_type="DT", min_length=8, max_length=8),
                ElementDefinition(position=2, name="Invoice Number", required=True, data_type="AN", min_length=1, max_length=22),
                ElementDefinition(position=3, name="Date", required=False, data_type="DT", min_length=8, max_length=8),
                ElementDefinition(position=4, name="Purchase Order Number", required=False, data_type="AN", min_length=1, max_length=22),
            ],
        )
        
        # IT1 - Baseline Item Data (Invoice)
        schema.segment_definitions["IT1"] = SegmentDefinition(
            segment_id="IT1",
            name="Baseline Item Data (Invoice)",
            elements=[
                ElementDefinition(position=1, name="Assigned Identification", required=False, data_type="AN", min_length=1, max_length=20),
                ElementDefinition(position=2, name="Quantity Invoiced", required=True, data_type="N0", min_length=1, max_length=10),
                ElementDefinition(position=3, name="Unit or Basis for Measurement Code", required=True, data_type="ID", min_length=2, max_length=2),
                ElementDefinition(position=4, name="Unit Price", required=True, data_type="N2", min_length=1, max_length=17),
            ],
        )
        
        # TDS - Total Monetary Value Summary
        schema.segment_definitions["TDS"] = SegmentDefinition(
            segment_id="TDS",
            name="Total Monetary Value Summary",
            elements=[
                ElementDefinition(position=1, name="Amount", required=True, data_type="N2", min_length=1, max_length=15),
            ],
        )
        
        schema.segment_definitions["REF"] = self._build_837p_schema().segment_definitions["REF"]
        
        return schema
    
    def _build_855_schema(self) -> TransactionSchema:
        """Build 855 Purchase Order Acknowledgment schema."""
        schema = TransactionSchema(
            version="004010_855",
            transaction_set_id="855",
            name="Purchase Order Acknowledgment",
            functional_group_id="PR",
        )
        
        # BAK - Beginning Segment for Purchase Order Acknowledgment
        schema.segment_definitions["BAK"] = SegmentDefinition(
            segment_id="BAK",
            name="Beginning Segment for PO Acknowledgment",
            elements=[
                ElementDefinition(position=1, name="Transaction Set Purpose Code", required=True, data_type="ID", min_length=2, max_length=2),
                ElementDefinition(position=2, name="Acknowledgment Type", required=True, data_type="ID", min_length=2, max_length=2),
                ElementDefinition(position=3, name="Purchase Order Number", required=True, data_type="AN", min_length=1, max_length=22),
                ElementDefinition(position=4, name="Date", required=True, data_type="DT", min_length=8, max_length=8),
            ],
        )
        
        # ACK - Line Item Acknowledgment
        schema.segment_definitions["ACK"] = SegmentDefinition(
            segment_id="ACK",
            name="Line Item Acknowledgment",
            elements=[
                ElementDefinition(position=1, name="Line Item Status Code", required=True, data_type="ID", min_length=2, max_length=2),
                ElementDefinition(position=2, name="Quantity", required=False, data_type="N0", min_length=1, max_length=15),
                ElementDefinition(position=3, name="Unit or Basis for Measurement Code", required=False, data_type="ID", min_length=2, max_length=2),
            ],
        )
        
        schema.segment_definitions["REF"] = self._build_837p_schema().segment_definitions["REF"]
        schema.segment_definitions["PO1"] = self._build_850_schema().segment_definitions["PO1"]
        
        return schema
    
    def _build_860_schema(self) -> TransactionSchema:
        """Build 860 Purchase Order Change schema."""
        schema = TransactionSchema(
            version="004010_860",
            transaction_set_id="860",
            name="Purchase Order Change Request - Buyer Initiated",
            functional_group_id="PC",
        )
        
        # BCH - Beginning Segment for Purchase Order Change
        schema.segment_definitions["BCH"] = SegmentDefinition(
            segment_id="BCH",
            name="Beginning Segment for PO Change",
            elements=[
                ElementDefinition(position=1, name="Transaction Set Purpose Code", required=True, data_type="ID", min_length=2, max_length=2),
                ElementDefinition(position=2, name="Purchase Order Type Code", required=True, data_type="ID", min_length=2, max_length=2),
                ElementDefinition(position=3, name="Purchase Order Number", required=True, data_type="AN", min_length=1, max_length=22),
                ElementDefinition(position=5, name="Date", required=True, data_type="DT", min_length=8, max_length=8),
            ],
        )
        
        # POC - Line Item Change
        schema.segment_definitions["POC"] = SegmentDefinition(
            segment_id="POC",
            name="Line Item Change",
            elements=[
                ElementDefinition(position=1, name="Assigned Identification", required=False, data_type="AN", min_length=1, max_length=20),
                ElementDefinition(position=2, name="Line Item Change Type", required=True, data_type="ID", min_length=2, max_length=2),
                ElementDefinition(position=3, name="Quantity Ordered", required=False, data_type="N0", min_length=1, max_length=15),
            ],
        )
        
        schema.segment_definitions["REF"] = self._build_837p_schema().segment_definitions["REF"]
        
        return schema
