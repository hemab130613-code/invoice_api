from fastapi import FastAPI
from pydantic import BaseModel
from fastapi.middleware.cors import CORSMiddleware
from dateutil import parser
import re

app = FastAPI()

# Enable CORS
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


class InvoiceInput(BaseModel):
    invoice_text: str


def extract_value(patterns, text):
    for p in patterns:
        m = re.search(p, text, re.IGNORECASE | re.MULTILINE)
        if m:
            return m.group(1).strip()
    return None


def extract_money(patterns, text):
    for p in patterns:
        m = re.search(p, text, re.IGNORECASE | re.MULTILINE)
        if m:
            try:
                return float(m.group(1).replace(",", ""))
            except:
                pass
    return None


@app.post("/extract")
def extract(data: InvoiceInput):

    text = data.invoice_text

    result = {
        "invoice_no": None,
        "date": None,
        "vendor": None,
        "amount": None,
        "tax": None,
        "currency": None
    }

    # -----------------------------
    # Invoice Number
    # -----------------------------
    invoice_patterns = [
        r"Invoice\s*No\.?\s*[:#-]?\s*([A-Za-z0-9/_-]+)",
        r"Invoice\s*Number\s*[:#-]?\s*([A-Za-z0-9/_-]+)",
        r"Invoice\s*#\s*[:#-]?\s*([A-Za-z0-9/_-]+)",
        r"INV\s*No\.?\s*[:#-]?\s*([A-Za-z0-9/_-]+)",
        r"INV\s*#\s*[:#-]?\s*([A-Za-z0-9/_-]+)",
        r"Invoice\s*ID\s*[:#-]?\s*([A-Za-z0-9/_-]+)"
    ]

    result["invoice_no"] = extract_value(invoice_patterns, text)

    # -----------------------------
    # Vendor
    # -----------------------------
    vendor_patterns = [
        r"Vendor\s*[:\-]\s*(.+)",
        r"Seller\s*[:\-]\s*(.+)",
        r"Supplier\s*[:\-]\s*(.+)",
        r"From\s*[:\-]\s*(.+)",
        r"Company\s*[:\-]\s*(.+)"
    ]

    vendor = extract_value(vendor_patterns, text)

    if vendor:
        vendor = vendor.split("\n")[0].strip()

    result["vendor"] = vendor

    # -----------------------------
    # Date
    # -----------------------------
    date_patterns = [
        r"Date\s*[:\-]\s*(.+)",
        r"Invoice\s*Date\s*[:\-]\s*(.+)"
    ]

    raw_date = extract_value(date_patterns, text)

    if raw_date:
        raw_date = raw_date.split("\n")[0].strip()
        try:
            result["date"] = parser.parse(raw_date, dayfirst=True).strftime("%Y-%m-%d")
        except:
            pass

    # -----------------------------
    # Amount (Subtotal BEFORE TAX)
    # -----------------------------
    amount_patterns = [
        r"Subtotal.*?(?:Rs\.?|INR|USD|EUR|GBP|\$|₹|€|£)?\s*([\d,]+\.\d+)",
        r"Sub\s*Total.*?(?:Rs\.?|INR|USD|EUR|GBP|\$|₹|€|£)?\s*([\d,]+\.\d+)",
        r"Net\s*Amount.*?(?:Rs\.?|INR|USD|EUR|GBP|\$|₹|€|£)?\s*([\d,]+\.\d+)",
        r"Amount\s*Before\s*Tax.*?(?:Rs\.?|INR|USD|EUR|GBP|\$|₹|€|£)?\s*([\d,]+\.\d+)"
    ]

    result["amount"] = extract_money(amount_patterns, text)

    # -----------------------------
    # Tax
    # -----------------------------
    tax_patterns = [
        r"GST.*?(?:Rs\.?|INR|USD|EUR|GBP|\$|₹|€|£)?\s*([\d,]+\.\d+)",
        r"VAT.*?(?:Rs\.?|INR|USD|EUR|GBP|\$|₹|€|£)?\s*([\d,]+\.\d+)",
        r"CGST.*?(?:Rs\.?|INR|USD|EUR|GBP|\$|₹|€|£)?\s*([\d,]+\.\d+)",
        r"SGST.*?(?:Rs\.?|INR|USD|EUR|GBP|\$|₹|€|£)?\s*([\d,]+\.\d+)",
        r"IGST.*?(?:Rs\.?|INR|USD|EUR|GBP|\$|₹|€|£)?\s*([\d,]+\.\d+)",
        r"Tax.*?(?:Rs\.?|INR|USD|EUR|GBP|\$|₹|€|£)?\s*([\d,]+\.\d+)"
    ]

    result["tax"] = extract_money(tax_patterns, text)

    # -----------------------------
    # Currency
    # -----------------------------
    if re.search(r"\bINR\b|₹|Rs\.?", text, re.IGNORECASE):
        result["currency"] = "INR"
    elif re.search(r"\bUSD\b|\$", text, re.IGNORECASE):
        result["currency"] = "USD"
    elif re.search(r"\bEUR\b|€", text, re.IGNORECASE):
        result["currency"] = "EUR"
    elif re.search(r"\bGBP\b|£", text, re.IGNORECASE):
        result["currency"] = "GBP"

    return result