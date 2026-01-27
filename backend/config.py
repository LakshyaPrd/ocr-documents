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
    
    "INVOICE": {
        "name": "Invoice",
        "page1_keywords": ["invoice", "tax invoice", "commercial invoice", "proforma"],
        "page2_keywords": [],
        "fields": [
            "invoice_number", "invoice_date", "due_date", "invoice_type",
            "supplier_name", "supplier_address", "supplier_email", "supplier_phone", "supplier_tax_id",
            "customer_name", "customer_address", "customer_email", "customer_phone", "customer_tax_id",
            "line_items", "subtotal", "tax_amount", "tax_rate", "grand_total",
            "payment_terms", "currency", "po_number", "bank_details", "notes"
        ],
        "field_patterns": {}  # Using custom invoice extraction logic
    },
    
    "PURCHASE_ORDER": {
        "name": "Purchase Order",
        "page1_keywords": ["purchase order", "PO", "P.O.", "order"],
        "page2_keywords": [],
        "fields": [
            "po_number", "po_date", "expiry_date", "delivery_date", "po_type",
            "buyer_name", "buyer_address", "buyer_email", "buyer_phone", "buyer_tax_id",
            "supplier_name", "supplier_address", "supplier_email", "supplier_phone", "supplier_tax_id",
            "line_items", "subtotal", "tax_amount", "discount", "grand_total", "currency",
            "payment_terms", "payment_method",
            "delivery_address", "shipping_method", "shipping_charges",
            "contract_number", "quotation_number", "remarks"
        ],
        "field_patterns": {}  # Using custom PO extraction logic
    },
    
    "COMPANY_LICENSE": {
        "name": "Company License",
        "page1_keywords": ["license", "company license", "business license", "commercial license"],
        "page2_keywords": [],
        "fields": [
            "license_type", "license_no", "company_name", "business_name", "legal_type",
            "issue_date", "expiry_date", "duns_number", "main_license_no", "register_no", "dcci_no",
            "license_members", "license_activities",
            "full_address", "phone", "fax", "mobile", "po_box", "parcel_id", "email",
            "partners"
        ],
        "field_patterns": {}  # Using custom license extraction logic
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
        "page1_keywords": ["trade license", "commercial license", "professional license", "license type"],
        "page2_keywords": [],
        "fields": [
            "license_type", "license_no", "main_license_no", "register_no",
            "dcci_no", "duns_no", "company_name", "company_name_ar",
            "business_name", "legal_type", "issue_date", "expiry_date",
            "address", "po_box", "phone", "fax", "mobile", "parcel_id", "email",
            "members_table", "partners_table"
        ],
        "field_patterns": {}  # Using custom extraction logic
    },
    
    "COMPANY_VAT_CERTIFICATE": {
        "name": "Company VAT Certificate",
        "page1_keywords": ["federal tax authority", "tax registration certificate", "vat"],
        "page2_keywords": [],
        "fields": [
            "registration_number", "certificate_number", "legal_name_english",
            "legal_name_arabic", "registered_address", "contact_number",
            "effective_registration_date", "date_of_issue",
            "first_vat_return_period", "vat_return_due_date", "tax_period_start_end"
        ],
        "field_patterns": {}  # Using custom extraction logic
    },
    
    "VISA_CANCELLATION": {
        "name": "Visa Cancellation",
        "page1_keywords": ["visa cancellation", "residence cancellation", "application for cancellation", "cancellation transaction"],
        "page2_keywords": [],
        "fields": [
            "full_name", "passport_number", "nationality", "date_of_birth",
            "visa_type", "visa_number", "issuing_emirate", "profession",
            "sponsor_name", "sponsor_id", "establishment_number",
            "cancellation_date", "cancellation_ref", "application_number"
        ],
        "field_patterns": {}  # Using custom extraction logic
    },
    
    "ENTRY_PERMIT": {
        "name": "Entry Permit",
        "page1_keywords": ["entry permit", "permit number", "permit no"],
        "page2_keywords": [],
        "fields": [
            "permit_number", "visa_number", "file_number", "uid_number",
            "application_number", "reference_number", "full_name", "nationality",
            "gender", "date_of_birth", "passport_number", "passport_issue_date",
            "passport_expiry_date", "passport_issue_place", "permit_type",
            "permit_category", "entry_type", "number_of_entries", "duration",
            "issue_date", "expiry_date", "valid_from", "valid_until",
            "port_of_entry", "purpose_of_visit", "sponsor_name", "sponsor_id",
            "employer_name", "job_title", "email", "phone", "address",
            "status", "approval_status", "issued_by", "issuing_office",
            "qr_code", "barcode_number"
        ],
        "field_patterns": {}  # Using custom extraction logic
    }
}
