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
            # Passport number - VERY flexible
            "passport_number": [
                r"([A-Z]\d{7,8})",  # Z0000000, D1234567
                r"([A-Z]{1,2}\d{6,9})",  # AB123456
                r"no\.?\s*[:\-]?\s*([A-Z0-9]{6,12})",
                r"passport.*?([A-Z0-9]{6,12})",
                r"([0-9]{8,9})",
            ],
            "surname": [
                r"surname[:\s]*([A-Z][A-Z\s]+)",
                r"P<<([A-Z]+)<<",
                r"([A-Z]{5,})",
            ],
            "given_name": [
                r"given.*?name[:\s]*([A-Z][A-Za-z\s]{2,30})",
                r"<<([A-Z]+)<",
                r"([A-Z][a-z]+\s+[A-Z])",
            ],
            "full_name": [
                r"name[:\s]+([A-Z][A-Z\s]{3,40})",
                r"([A-Z]{3,}\s+[A-Z]{1,2}\b)",
            ],
            "date_of_birth": [
                r"(\d{2}/\d{2}/\d{4})",
                r"(\d{2}-\d{2}-\d{4})",
                r"birth.*?(\d{2}[/\-\.]\d{2}[/\-\.]\d{4})",
            ],
            "issue_date": [
                r"(\d{2}/\d{2}/\d{4})",
                r"issue.*?(\d{2}[/\-\.]\d{2}[/\-\.]\d{4})",
            ],
            "expiry_date": [
                r"(\d{2}/\d{2}/\d{4})",
                r"expiry.*?(\d{2}[/\-\.]\d{2}[/\-\.]\d{4})",
            ],
            "gender": [
                r"\b(M|F)\b",
                r"sex[:\s]*(M|F|MALE|FEMALE)",
            ],
            "nationality": [
                r"(INDIAN|AMERICAN|BRITISH|EMIRATI)",
                r"nationality[:\s]*([A-Z]+)",
            ],
            "country_code": [
                r"\b(IND|USA|GBR|UAE|PKT|BGD)\b",
                r"code[:\s]*([A-Z]{3})",
            ],
            "place_of_birth": [
                r"([A-Z]{4,},\s*[A-Z]{4,})",
                r"birth[:\s]*([A-Z][A-Za-z\s,]+)",
            ],
            "issue_place": [
                r"([A-Z]{5,})",
                r"issue[:\s]*([A-Z][A-Za-z\s]+)",
            ],
        }
    },

    "LABOR_CARD": {
        "name": "Labor Card",
        "page1_keywords": ["work permit", "ministry"],
        "page2_keywords": [],
        "fields": [
            "full_name", "work_permit_number", "passport_number", "position",
            "nationality", "company_name", "expiry_date", "issue_date", "gender"
        ],
        "field_patterns": {
            # Based on: "Name : CHURCHIL SUNDAR RAJ..."
            "full_name": [
                r"Name\s*:\s*([A-Z][A-Z\s]+)",
                r"([A-Z]{3,}\s+[A-Z]{3,}\s+[A-Z]{3,})",
            ],
            # "Work Permit NO : 10021099682055"
            "work_permit_number": [
                r"Work\s*Permit\s*NO\s*:\s*(\d{10,15})",
                r"Permit\s*NO\s*:\s*([A-Z0-9]{10,15})",
                r"(\d{12,14})",
            ],
            # "Personal NO : 102033033"
            "passport_number": [
                r"Personal\s*NO\s*:\s*([A-Z0-9]{6,15})",
                r"([0-9]{9})",
            ],
            # "Profession : ..."
            "position": [
                r"Profession\s*:\s*([A-Za-z\s]{3,50})",
            ],
            # "Nationality : ..."
            "nationality": [
                r"Nationality\s*:\s*([A-Za-z\s]+)",
                r"(INDIAN|PAKISTANI|BANGLADESHI|FILIPINO)",
            ],
            # "Establishment : ENGISOFT TECHNICAL SERVICES LLC"
            "company_name": [
                r"Establishment\s*:\s*([A-Z][A-Z\s\&]+LLC)",
                r"([A-Z\s]{10,}\s+LLC)",
            ],
            # "Expiry Date : 27/01/2023"
            "expiry_date": [
                r"Expiry\s*Date\s*:\s*(\d{2}/\d{2}/\d{4})",
                r"(\d{2}/\d{2}/\d{4})",
            ],
            "issue_date": [
                r"(\d{2}/\d{2}/\d{4})",
            ],
            "gender": [
                r"\b(M|F|MALE|FEMALE)\b",
            ],
        }
    },
}