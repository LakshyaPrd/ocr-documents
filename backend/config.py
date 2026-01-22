"""
Configuration for document types and OCR field templates
"""

DOCUMENT_TYPES = {
    "PASSPORT": {
        "name": "Passport",
        "page1_keywords": ["passport", "republic"],
        "page2_keywords": [],
        "fields": [
            "surname", "given_name", "full_name", "date_of_birth", 
            "place_of_birth", "gender", "nationality", "passport_number", 
            "issue_date", "expiry_date", "issue_place", "country_code"
        ],
        "field_patterns": {
            # Passport number - very flexible patterns
            "passport_number": [
                r"([A-Z][0-9]{7,8})",  # Z0000000 format
                r"passport.*?([A-Z0-9]{6,12})",  # After word "passport"
                r"no\.?\s*([A-Z0-9]{6,12})",  # After "no" or "no."
            ],
            # Names - VERY flexible (catch-all)
            "surname": [
                r"surname[:\s]*([A-Z][A-Z\s]+)",
                r"P<<([A-Z]+)<<",  # MRZ line
                r"([A-Z]{5,})",  # Any capitalized word 5+ letters (SPECIMEN)
            ],
            "given_name": [
                r"given.*?name[:\s]*([A-Z][A-Za-z\s]{2,30})",
                r"<<([A-Z]+)<",  # MRZ middle
                r"([A-Z][a-z]+\s+[A-Z])",  # Kumar G pattern
            ],
            "full_name": [
                r"name[:\s]*([A-Z][A-Z\s]{3,40})",
            ],
            # Dates - very flexible
            "date_of_birth": [
                r"(\d{1,2}[/\-\.]\d{1,2}[/\-\.]\d{4})",  # DD/MM/YYYY
                r"birth.*?(\d{1,2}[/\-\.]\d{1,2}[/\-\.]\d{4})",
            ],
            "issue_date": [
                r"issue.*?(\d{1,2}[/\-\.]\d{1,2}[/\-\.]\d{4})",
                r"date.*?issue.*?(\d{1,2}[/\-\.]\d{1,2}[/\-\.]\d{4})",
            ],
            "expiry_date": [
                r"expiry.*?(\d{1,2}[/\-\.]\d{1,2}[/\-\.]\d{4})",
                r"date.*?expiry.*?(\d{1,2}[/\-\.]\d{1,2}[/\-\.]\d{4})",
            ],
            # Gender
            "gender": [
                r"sex[:\s]*(M|F|MALE|FEMALE)",
                r"(\bM\b|\bF\b)",  # Just M or F
            ],
            # Nationality and country  
            "nationality": [
                r"nationality[:\s]*([A-Z]+)",
                r"national.*?([A-Z]{3,20})",
            ],
            "country_code": [
                r"code[:\s]*([A-Z]{3})",
                r"\b(IND|USA|GBR|UAE)\b",  # Common codes
            ],
            # Place - catch ANY city/state
            "place_of_birth": [
                r"([A-Z]{4,},\s*[A-Z]{4,})",  # MUMBAI, MAHARASHTRA
                r"birth[:\s]*([A-Z][A-Za-z\s,]+)",
            ],
            "issue_place": [
                r"([A-Z]{5,})",  # BANGALORE (standalone city)
                r"issue[:\s]*([A-Z][A-Za-z\s]+)",
            ],
        }
    },
    
    "LABOR_CARD": {
        "name": "Labor Card",
        "page1_keywords": ["work permit", "ministry of human resources"],
        "page2_keywords": [],
        "fields": [
            "full_name", "father_name", "date_of_birth", "nationality", 
            "gender", "work_permit_number", "issue_date", "expiry_date",
            "file_number", "company_name", "position", "salary", 
            "contract_duration", "work_location", "sponsor_name", 
            "sponsor_id", "issue_authority", "passport_number"
        ],
        "field_patterns": {
            "full_name": [r"Name\s*:\s*([A-Z][A-Z\s]+)", r"([A-Z]{4,}\s+[A-Z]{4,}\s+[A-Z]{3,})"],
            "work_permit_number": [r"Personal\s*NO\s*:\s*([A-Z0-9]{6,15})", r"(\d{9})"],
            "passport_number": [r"Work\s*Permit\s*NO\s*:\s*(\d{10,15})", r"(\d{12,14})"],
            "position": [r"Profession\s*:\s*([A-Za-z\s]{3,50})"],
            "nationality": [r"Nationality\s*:\s*([A-Za-z\s]+)", r"(INDIAN|PAKISTANI|BANGLADESHI|FILIPINO)"],
            "company_name": [r"Establishment\s*:\s*([A-Z][A-Z\s\&]+LLC)", r"([A-Z\s]{10,}\s+LLC)"],
            "expiry_date": [r"Expiry\s*Date\s*:\s*(\d{2}/\d{2}/\d{4})", r"(\d{2}/\d{2}/\d{4})"],
            "gender": [r"\b(M|F|MALE|FEMALE)\b"],
        }
    },
    
    "RESIDENCE_VISA": {
        "name": "Residence Visa",
        "page1_keywords": ["residence", "visa", "u.i.d", "sponsor"],
        "page2_keywords": [],
        "fields": [
            "name_on_visa", "uid_number", "file_number", "profession",
            "sponsor", "place_of_issue", "issue_date", "expiry_date"
        ],
        "field_patterns": {}  # Using custom extraction logic, not regex
    },
    
    "EMIRATES_ID": {
        "name": "Emirates ID",
        "page1_keywords": ["federal authority for identity", "citizenship"],
        "page2_keywords": ["card number", "employer"],
        "fields": [
            "full_name", "id_number", "card_number", "date_of_birth",
            "nationality", "gender", "issue_date", "expiry_date",
            "employer_name", "issue_authority"
        ],
        "field_patterns": {
            "id_number": [r"id\s*no\.?\s*[:\-]?\s*(\d{3}\-\d{4}\-\d{7}\-\d)", r"(\d{3}\-\d{4}\-\d{7}\-\d)"],
            "card_number": [r"card\s*no\.?\s*[:\-]?\s*(\d{15})", r"card\s*number\s*[:\-]?\s*(\d{15})"],
        }
    },
    
    "RESIDENCE_VISA": {
        "name": "Residence Visa",
        "page1_keywords": ["residence permit"],
        "page2_keywords": [],
        "fields": [
            "full_name", "date_of_birth", "nationality", "gender",
            "passport_number", "residence_permit_number", "issue_date",
            "expiry_date", "visa_type", "sponsor_name", "sponsor_id",
            "relationship", "entry_date", "port_of_entry", "profession",
            "marital_status", "place_of_issue"
        ],
        "field_patterns": {
            "residence_permit_number": [r"residence\s*permit\s*[:\-]?\s*([A-Z0-9]{6,15})", r"permit\s*no\.?\s*[:\-]?\s*([A-Z0-9]{6,15})"],
            "visa_type": [r"visa\s*type\s*[:\-]?\s*([A-Za-z\s]{3,30})"],
        }
    },
    
    "VISIT_VISA": {
        "name": "Visit Visa",
        "page1_keywords": ["visit visa", "tourist visa", "entry permit"],
        "page2_keywords": [],
        "fields": [
            "visa_type_duration", "entry_permit_number", "date_place_of_issue",
            "uid_number", "full_name", "nationality", "place_of_birth",
            "date_of_birth", "passport_number", "profession"
        ],
        "field_patterns": {}  # Using custom extraction logic
    },
    
    "LABOR_CONTRACT": {
        "name": "Labor Contract",
        "page1_keywords": ["employment contract", "labor contract"],
        "page2_keywords": [],
        "fields": [
            "employee_name", "employee_passport", "employee_nationality",
            "employee_dob", "employer_name", "employer_license", "employer_contact",
            "contract_start_date", "contract_duration", "probation_period",
            "basic_salary", "housing_allowance", "transport_allowance",
            "total_package", "annual_leave_days", "ticket_allowance",
            "medical_insurance", "notice_period", "end_of_service_benefits",
            "working_hours", "position", "job_description", "work_location"
        ],
        "field_patterns": {
            "basic_salary": [r"basic\s*salary\s*[:\-]?\s*(AED|USD)?\s*(\d{1,10})"],
            "contract_start_date": [r"start\s*date\s*[:\-]?\s*(\d{1,2}[\/\-\.]\d{1,2}[\/\-\.]\d{2,4})"],
        }
    },
    
    "HOME_COUNTRY_ID": {
        "name": "Home Country ID",
        "page1_keywords": ["government of india"],
        "page2_keywords": ["unique identification authority of india"],
        "fields": [
            "full_name", "father_name", "mother_name", "date_of_birth",
            "place_of_birth", "gender", "id_number", "aadhaar_number",
            "issue_date", "issue_authority", "permanent_address",
            "district", "state", "pin_code", "mobile_number",
            "biometric_ref", "qr_code_data"
        ],
        "field_patterns": {
            "aadhaar_number": [r"(\d{4}\s\d{4}\s\d{4})", r"aadhaar\s*[:\-]?\s*(\d{12})"],
            "id_number": [r"id\s*no\.?\s*[:\-]?\s*([A-Z0-9]{6,15})"],
        }
    },
    
    "PURCHASE_ORDER": {
        "name": "Purchase Order",
        "page1_keywords": ["purchase order", "po number"],
        "page2_keywords": [],
        "fields": [
            "po_number", "po_date", "reference_number", "vendor_name",
            "vendor_id", "vendor_address", "vendor_contact", "vendor_tax_id",
            "buyer_company", "buyer_address", "buyer_contact", "buyer_department",
            "item_description", "quantity", "unit_price", "total_per_item",
            "subtotal", "tax_amount", "discount", "total_amount",
            "payment_terms", "delivery_date", "shipping_address", "currency"
        ],
        "field_patterns": {
            "po_number": [r"po\s*no\.?\s*[:\-]?\s*([A-Z0-9\-]{4,20})", r"purchase\s*order\s*[:\-]?\s*([A-Z0-9\-]{4,20})"],
            "total_amount": [r"total\s*[:\-]?\s*([A-Z]{3})?\s*(\d{1,15}\.?\d{0,2})"],
        }
    },
    
    "INVOICE": {
        "name": "Invoice",
        "page1_keywords": ["invoice", "invoice number"],
        "page2_keywords": [],
        "fields": [
            "invoice_number", "invoice_date", "due_date", "reference_number",
            "seller_company", "seller_address", "seller_tax_id", "seller_contact",
            "buyer_name", "buyer_address", "buyer_tax_id", "buyer_contact",
            "item_description", "quantity", "unit_price", "total_per_item",
            "subtotal", "tax_amount", "discount", "total_amount_due",
            "amount_paid", "balance_due", "payment_terms", "payment_method",
            "bank_details", "currency"
        ],
        "field_patterns": {
            "invoice_number": [r"invoice\s*no\.?\s*[:\-]?\s*([A-Z0-9\-]{4,20})", r"invoice\s*#\s*([A-Z0-9\-]{4,20})"],
            "total_amount_due": [r"total\s*amount\s*[:\-]?\s*([A-Z]{3})?\s*(\d{1,15}\.?\d{0,2})"],
        }
    },
    
    "COMPANY_LICENSE": {
        "name": "Company License",
        "page1_keywords": ["license"],
        "page2_keywords": [],
        "fields": [
            "license_number", "license_type", "issue_date", "expiry_date",
            "company_name", "trade_name", "legal_entity_type", "business_activity",
            "industry_classification", "registered_address", "business_location",
            "emirates", "issuing_authority", "license_status", "owner_name",
            "manager_name", "authorized_signatory", "capital_amount",
            "phone_number", "email_address"
        ],
        "field_patterns": {
            "license_number": [r"license\s*no\.?\s*[:\-]?\s*([A-Z0-9\-]{4,20})", r"licence\s*number\s*[:\-]?\s*([A-Z0-9\-]{4,20})"],
        }
    },
    
    "COMPANY_VAT_CERTIFICATE": {
        "name": "Company VAT Certificate",
        "page1_keywords": ["federal tax authority"],
        "page2_keywords": [],
        "fields": [
            "vat_registration_number", "trn", "certificate_number", "issue_date",
            "registration_date", "company_name", "trade_name", "legal_form",
            "tax_group", "business_activity", "classification", "registered_address",
            "business_address", "emirates", "email_address", "phone_number",
            "contact_person", "vat_effective_date", "registration_status"
        ],
        "field_patterns": {
            "vat_registration_number": [r"vat\s*no\.?\s*[:\-]?\s*(\d{15})", r"trn\s*[:\-]?\s*(\d{15})"],
            "trn": [r"trn\s*[:\-]?\s*(\d{15})"],
        }
    }
}
