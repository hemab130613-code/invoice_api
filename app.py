from fastapi import FastAPI
from pydantic import BaseModel
from fastapi.middleware.cors import CORSMiddleware

import re
from dateutil import parser

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


def extract_invoice(text):

    result = {
        "invoice_no": None,
        "date": None,
        "vendor": None,
        "amount": None,
        "tax": None,
        "currency": "INR"
    }

    # Invoice Number
    m = re.search(r"Invoice\s*No[:\-]?\s*(.+)", text, re.I)
    if m:
        result["invoice_no"] = m.group(1).strip()

    # Vendor
    m = re.search(r"Vendor[:\-]?\s*(.+)", text, re.I)
    if m:
        result["vendor"] = m.group(1).strip()

    # Date
    m = re.search(r"Date[:\-]?\s*(.+)", text, re.I)
    if m:
        try:
            d = parser.parse(m.group(1))
            result["date"] = d.strftime("%Y-%m-%d")
        except:
            pass

    # Subtotal
    m = re.search(r"Subtotal[:\-]?\s*(?:Rs\.?|INR)?\s*([\d,]+\.\d+)", text, re.I)
    if m:
        result["amount"] = float(m.group(1).replace(",", ""))

    # GST
    m = re.search(r"(?:GST|Tax).*?(?:Rs\.?|INR)?\s*([\d,]+\.\d+)", text, re.I)
    if m:
        result["tax"] = float(m.group(1).replace(",", ""))

    return result


@app.post("/extract")
def extract(data: InvoiceInput):
    return extract_invoice(data.invoice_text)