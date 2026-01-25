# Invoice extraction logic (integrated from user's proven code)
# Located at end of ocr_service.py - to be added

def _extract_invoice_proven(self, text: str) -> Dict:
    """
    Extract invoice fields using proven logic - optimized for speed
    Based on user's invoice extraction code with patterns
    """
    extracted = {}
    lines = text.split('\n')
    
    # Invoice Number
    inv_num_pattern = r'(?:invoice\s*(?:number|no|#)|inv\s*(?:no|#))[:\s]*([A-Z0-9\-/]+)'
    match = re.search(inv_num_pattern, text, re.IGNORECASE)
    if match:
        extracted['invoice_number'] = {'value': match.group(1).strip(), 'confidence': 90.0, 'source': 'INVOICE_OCR'}
    
    # Invoice Date  
    inv_date_pattern = r'(?:invoice\s*date|date)[:\s]*(\d{1,2}[/-]\d{1,2}[/-]\d{2,4}|\d{4}[/-]\d{1,2}[/-]\d{1,2})'
    match = re.search(inv_date_pattern, text, re.IGNORECASE)
    if match:
        extracted['invoice_date'] = {'value': match.group(1), 'confidence': 88.0, 'source': 'INVOICE_OCR'}
    
    # Due Date
    due_date_pattern = r'(?:due\s*date|payment\s*due)[:\s]*(\d{1,2}[/-]\d{1,2}[/-]\d{2,4}|\d{4}[/-]\d{1,2}[/-]\d{1,2})'
    match = re.search(due_date_pattern, text, re.IGNORECASE)
    if match:
        extracted['due_date'] = {'value': match.group(1), 'confidence': 88.0, 'source': 'INVOICE_OCR'}
    
    # Invoice Type
    inv_type_pattern = r'(tax\s*invoice|proforma\s*invoice|credit\s*note|debit\s*note|commercial\s*invoice)'
    match = re.search(inv_type_pattern, text, re.IGNORECASE)
    if match:
        extracted['invoice_type'] = {'value': match.group(1), 'confidence': 92.0, 'source': 'INVOICE_OCR'}
    
    # Tax ID / GST / VAT
    tax_ids = []
    tax_id_pattern = r'(?:GST|VAT|TIN|TAX\s*ID)[:\s]*([A-Z0-9]{8,15})'
    for match in re.finditer(tax_id_pattern, text, re.IGNORECASE):
        tax_ids.append(match.group(1).strip())
    
    if len(tax_ids) > 0:
        extracted['supplier_tax_id'] = {'value': tax_ids[0], 'confidence': 85.0, 'source': 'INVOICE_OCR'}
    if len(tax_ids) > 1:
        extracted['customer_tax_id'] = {'value': tax_ids[1], 'confidence': 85.0, 'source': 'INVOICE_OCR'}
    
    # Email addresses
    emails = re.findall(r'\b([a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,})\b', text)
    if len(emails) > 0:
        extracted['supplier_email'] = {'value': emails[0], 'confidence': 90.0, 'source': 'INVOICE_OCR'}
    if len(emails) > 1:
        extracted['customer_email'] = {'value': emails[1], 'confidence': 90.0, 'source': 'INVOICE_OCR'}
    
    # Phone numbers
    phone_pattern = r'(?:phone|tel|mobile|contact)[:\s]*([+\d\s\-\(\)]{10,20})'
    phones = re.findall(phone_pattern, text, re.IGNORECASE)
    if len(phones) > 0:
        extracted['supplier_phone'] = {'value': phones[0].strip(), 'confidence': 85.0, 'source': 'INVOICE_OCR'}
    if len(phones) > 1:
        extracted['customer_phone'] = {'value': phones[1].strip(), 'confidence': 85.0, 'source': 'INVOICE_OCR'}
    
    # Currency
    currency_pattern = r'\b(USD|EUR|GBP|INR|AUD|CAD|SGD|JPY|CNY|AED)\b'
    match = re.search(currency_pattern, text)
    if match:
        extracted['currency'] = {'value': match.group(1), 'confidence': 95.0, 'source': 'INVOICE_OCR'}
    
    # Subtotal
    subtotal_pattern = r'(?:subtotal|sub\s*total)[:\s]*([₹$€£¥]?\s*[\d,]+\.?\d*)'
    match = re.search(subtotal_pattern, text, re.IGNORECASE)
    if match:
        extracted['subtotal'] = {'value': match.group(1).strip(), 'confidence': 88.0, 'source': 'INVOICE_OCR'}
    
    # Tax Amount
    tax_amt_pattern = r'(?:tax|vat|gst)[:\s]*([₹$€£¥]?\s*[\d,]+\.?\d*)'
    match = re.search(tax_amt_pattern, text, re.IGNORECASE)
    if match:
        extracted['tax_amount'] = {'value': match.group(1).strip(), 'confidence': 88.0, 'source': 'INVOICE_OCR'}
    
    # Tax Rate
    tax_rate_pattern = r'(?:tax|vat|gst).*?(\d+(?:\.\d+)?)\s*%'
    match = re.search(tax_rate_pattern, text, re.IGNORECASE)
    if match:
        extracted['tax_rate'] = {'value': match.group(1) + '%', 'confidence': 90.0, 'source': 'INVOICE_OCR'}
    
    # Grand Total
    total_pattern = r'(?:grand\s*total|total\s*amount|net\s*total|total)[:\s]*([₹$€£¥]?\s*[\d,]+\.?\d*)'
    match = re.search(total_pattern, text, re.IGNORECASE)
    if match:
        extracted['grand_total'] = {'value': match.group(1).strip(), 'confidence': 90.0, 'source': 'INVOICE_OCR'}
    
    # Payment Terms
    terms_pattern = r'(?:payment\s*terms|terms)[:\s]*(net\s*\d+|due\s*on\s*receipt|[^.\n]{5,50})'
    match = re.search(terms_pattern, text, re.IGNORECASE)
    if match:
        extracted['payment_terms'] = {'value': match.group(1).strip(), 'confidence': 80.0, 'source': 'INVOICE_OCR'}
    
    # PO Number
    po_pattern = r'(?:PO|purchase\s*order)[:\s#]*([A-Z0-9\-/]+)'
    match = re.search(po_pattern, text, re.IGNORECASE)
    if match:
        extracted['po_number'] = {'value': match.group(1).strip(), 'confidence': 88.0, 'source': 'INVOICE_OCR'}
    
    # Company Names (supplier and customer)
    # Split into sections
    supplier_section, customer_section = self._split_invoice_sections(text)
    
    supplier_name = self._extract_company_name(supplier_section)
    if supplier_name:
        extracted['supplier_name'] = {'value': supplier_name, 'confidence': 80.0, 'source': 'INVOICE_OCR'}
    
    customer_name = self._extract_company_name(customer_section)
    if customer_name:
        extracted['customer_name'] = {'value': customer_name, 'confidence': 80.0, 'source': 'INVOICE_OCR'}
    
    # Addresses
    supplier_addr = self._extract_address(supplier_section)
    if supplier_addr:
        extracted['supplier_address'] = {'value': supplier_addr, 'confidence': 75.0, 'source': 'INVOICE_OCR'}
    
    customer_addr = self._extract_address(customer_section)
    if customer_addr:
        extracted['customer_address'] = {'value': customer_addr, 'confidence': 75.0, 'source': 'INVOICE_OCR'}
    
    # Bank Details
    bank_details = self._extract_bank_details(text)
    if bank_details:
        extracted['bank_details'] = {'value': json.dumps(bank_details), 'confidence': 85.0, 'source': 'INVOICE_OCR'}
    
    # Notes
    notes_pattern = r'(?:notes?|remarks?|comments?)[:\s]*([^\n]{10,200})'
    match = re.search(notes_pattern, text, re.IGNORECASE)
    if match:
        extracted['notes'] = {'value': match.group(1).strip(), 'confidence': 75.0, 'source': 'INVOICE_OCR'}
    
    # Line Items (simplified - extract count)
    line_items = self._extract_line_items_count(text)
    if line_items > 0:
        extracted['line_items'] = {'value': f"{line_items} items", 'confidence': 70.0, 'source': 'INVOICE_OCR'}
    
    return extracted

def _split_invoice_sections(self, text: str) -> tuple:
    """Split invoice text into supplier and customer sections"""
    lines = text.split('\n')
    supplier_section = ""
    customer_section = ""
    
    in_customer = False
    for line in lines:
        lower_line = line.lower()
        if any(word in lower_line for word in ['bill to', 'customer', 'client', 'buyer', 'billed to']):
            in_customer = True
        elif any(word in lower_line for word in ['seller', 'vendor', 'from', 'supplier', 'invoice from']):
            in_customer = False
        
        if in_customer:
            customer_section += line + "\n"
        else:
            supplier_section += line + "\n"
    
    return supplier_section, customer_section

def _extract_company_name(self, text: str) -> Optional[str]:
    """Extract company name from section"""
    lines = [l.strip() for l in text.split('\n') if l.strip()]
    
    if not lines:
        return None
    
    # Look for capitalized company names in first 10 lines
    for line in lines[:10]:
        if len(line) > 3 and not line.startswith(('Phone', 'Email', 'Address', 'Tax', 'GST', 'VAT')):
            if line.isupper() or line.istitle():
                return line
    
    return lines[0] if lines else None

def _extract_address(self, text: str) -> Optional[str]:
    """Extract address from text"""
    lines = text.split('\n')
    address_lines = []
    
    for line in lines:
        line = line.strip()
        if line and re.search(r'\d+|,|street|road|avenue|city|state|zip|pincode', line, re.IGNORECASE):
            address_lines.append(line)
            if len(address_lines) >= 3:
                break
    
    return ', '.join(address_lines) if address_lines else None

def _extract_bank_details(self, text: str) -> Optional[dict]:
    """Extract bank account details"""
    bank_details = {}
    
    # IBAN
    iban_match = re.search(r'IBAN[:\s]*([A-Z0-9]{15,34})', text, re.IGNORECASE)
    if iban_match:
        bank_details['iban'] = iban_match.group(1)
    
    # SWIFT
    swift_match = re.search(r'SWIFT[:\s]*([A-Z0-9]{8,11})', text, re.IGNORECASE)
    if swift_match:
        bank_details['swift'] = swift_match.group(1)
    
    # Account Number
    acc_match = re.search(r'(?:account|acc)(?:\s*no|\s*number)[:\s]*(\d{8,18})', text, re.IGNORECASE)
    if acc_match:
        bank_details['account_number'] = acc_match.group(1)
    
    return bank_details if bank_details else None

def _extract_line_items_count(self, text: str) -> int:
    """Count line items in invoice"""
    lines = text.split('\n')
    count = 0
    
    # Look for table header
    header_idx = -1
    for i, line in enumerate(lines):
        lower_line = line.lower()
        if ('description' in lower_line or 'item' in lower_line) and \
           ('quantity' in lower_line or 'qty' in lower_line) and \
           ('price' in lower_line or 'rate' in lower_line or 'amount' in lower_line):
            header_idx = i
            break
    
    if header_idx == -1:
        return 0
    
    # Count rows after header until totals
    for i in range(header_idx + 1, len(lines)):
        line = lines[i].strip()
        if not line:
            continue
        lower_line = line.lower()
        if any(word in lower_line for word in ['subtotal', 'total', 'tax', 'discount', 'grand']):
            break
        # If line has numeric values, likely a line item
        if re.search(r'\d+', line):
            count += 1
    
    return count
