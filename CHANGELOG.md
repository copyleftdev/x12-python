# Changelog

All notable changes to this project will be documented in this file.

The format is based on [Keep a Changelog](https://keepachangelog.com/en/1.1.0/),
and this project adheres to [Semantic Versioning](https://semver.org/spec/v2.0.0.html).

## [Unreleased]

## [0.1.0] - 2024-11-28

### Added

#### Core Components
- `Parser` - Full X12 EDI parsing with automatic delimiter detection
- `Generator` - EDI generation with proper envelope wrapping
- `X12Validator` - Multi-level validation (syntax, semantic, HIPAA)
- `Tokenizer` - Low-level EDI tokenization
- `Delimiters` - ISA-based delimiter detection

#### Models
- `Segment`, `Element` - Core EDI building blocks
- `Loop` - Hierarchical loop structures
- `Interchange`, `FunctionalGroup`, `TransactionSet` - Envelope models

#### Healthcare Transactions (HIPAA 5010)
- 837P Professional Claim (005010X222A1)
- 837I Institutional Claim (005010X223A3)
- 837D Dental Claim (005010X224A3)
- 835 Remittance Advice (005010X221A1)
- 270/271 Eligibility Inquiry/Response (005010X279A1)
- 276/277 Claim Status Request/Response (005010X212)
- 834 Benefit Enrollment (005010X220A1)
- 278 Prior Authorization (005010X217)
- 820 Premium Payment (005010X218)

#### Supply Chain Transactions (4010)
- 850 Purchase Order
- 856 Ship Notice/Manifest (ASN)
- 810 Invoice
- 855 Purchase Order Acknowledgment
- 860 Purchase Order Change

#### Acknowledgments
- 997 Functional Acknowledgment generation
- 999 Implementation Acknowledgment generation

#### Code Sets
- Entity Identifier Codes (NM101)
- Place of Service Codes
- Claim Status Codes
- Claim Adjustment Reason Codes (CARC)
- Remittance Advice Remark Codes (RARC)
- Service Type Codes (270/271)
- Diagnosis Type Qualifiers
- Procedure Code Qualifiers
- Claim Frequency Codes
- Provider Taxonomy Codes
- Revenue Codes (UB-04)
- Modifier Codes
- Unit of Measure Codes
- Adjustment Group Codes
- Eligibility/Benefit Information Codes
- Time Period Qualifier Codes

#### Streaming
- `StreamingSegmentReader` - Memory-bounded streaming for large files
- `StreamingTransactionParser` - Stream-based transaction parsing

#### Validation
- NPI validation with Luhn check
- Tax ID (EIN) validation
- ICD-10 diagnosis code format validation
- CPT/HCPCS procedure code validation

#### Trading Partners
- `TradingPartner` - Partner configuration
- `PartnerRegistry` - Partner management
- Custom delimiter support per partner

### Testing
- 393 passing tests
- 83% code coverage
- Unit, integration, property, compliance, and performance tests
- Hypothesis property-based testing

[Unreleased]: https://github.com/donjohnson/x12-edi-tools/compare/v0.1.0...HEAD
[0.1.0]: https://github.com/donjohnson/x12-edi-tools/releases/tag/v0.1.0
