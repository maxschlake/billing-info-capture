import re
import spacy
import spacy.tokens


def standardize(text):
    # Replace any '|' character with a space
    text = re.sub(r'\|', ' ', text)
    
    # Replace any whitespace character (including tab and newline) by a space, then remove extra whitespaces
    text = re.sub(r'\s+', ' ', text).strip()

    # Standardize dates to YYYY-MM-DD format
    text = re.sub(r'(\d{2})[-/\.](\d{2})[-/\.](\d{4})', r'\3-\2-\1', text) # YYYY/MM/DD or YYYY.MM.DD
    text = re.sub(r'(\d{4})[-/\.](\d{2})[-/\.](\d{2})', r'\1-\2-\3', text) # DD/MM/YYYY or DD.MM.YYYY

    # Remove unwanted characters
    text = re.sub(r'[^\w\s€£¥$-@#,.%-]', '', text)

    # Show monetary values in a standard format: XX.XX CUR
    # XX.XX EUR
    text = re.sub(r'(\d+(?:\.\d+)?)\s?€', r'\1 EUR', text)  # XX.XX€ or XX:XX €
    text = re.sub(r'€\s?(\d+(?:\.\d+)?)', r'\1 EUR', text)   # € XX.XX or €XX.XX
    text = re.sub(r'\bEUR\s?(\d+(?:\.\d+)?)\b', r'\1 EUR', text)   # EURXX.XX, EUR XX.XX
    text = re.sub(r'\b(\d+(?:\.\d+)?)\s?EUR\b', r'\1 EUR', text)   # XX.XXEUR
    # XX.XX USD
    text = re.sub(r'(\d+(?:\.\d+)?)\s?\$', r'\1 USD', text)  # XX.XX$ or XX:XX $
    text = re.sub(r'\$\s?(\d+(?:\.\d+)?)', r'\1 USD', text)   # $ XX.XX or $XX.XX
    text = re.sub(r'\bUSD\s?(\d+(?:\.\d+)?)\b', r'\1 USD', text)   # USDXX.XX, USD XX.XX
    text = re.sub(r'\b(\d+(?:\.\d+)?)\s?USD\b', r'\1 USD', text)   # XX.XXUSD
    # XX.XX GBP
    text = re.sub(r'(\d+(?:\.\d+)?)\s?£', r'\1 GBP', text)  # XX.XX£ or XX:XX £
    text = re.sub(r'£\s?(\d+(?:\.\d+)?)', r'\1 GBP', text)   # £ XX.XX or £XX.XX
    text = re.sub(r'\bGBP\s?(\d+(?:\.\d+)?)\b', r'\1 GBP', text)   # GBPXX.XX, GBP XX.XX
    text = re.sub(r'\b(\d+(?:\.\d+)?)\s?GBP\b', r'\1 GBP', text)   # XX.XXGBP
    # XX.XX RMB
    text = re.sub(r'(\d+(?:\.\d+)?)\s?¥', r'\1 RMB', text)  # XX.XX¥ or XX:XX ¥
    text = re.sub(r'¥\s?(\d+(?:\.\d+)?)', r'\1 RMB', text)   # ¥ XX.XX or ¥XX.XX
    text = re.sub(r'\bRMB\s?(\d+(?:\.\d+)?)\b', r'\1 RMB', text)   # RMBXX.XX, RMB XX.XX
    text = re.sub(r'\b(\d+(?:\.\d+)?)\s?RMB\b', r'\1 RMB', text)   # XX.XXRMB

    # Convert to a format without thousands separators but with decimal points (and '00' if there are no decimals)
    text = re.sub(
        # Set up three capturing groups (automatically indexed by 1):
            # Group 1: (\d{1,3}(?:\.\d{3})*|\d+) -> Integer part of the number which may contain thousands separators
            # Group 2: (\.\d+)? -> Optional decimals
            # Group 3: (EUR|USD|GBP|RMB) -> Currency
        r'(\d{1,3}(?:\.\d{3})*|\d+)(\.\d+)?\s?(EUR|USD|GBP|RMB)',
        lambda m: (
            # If no decimal part or three digits after the last dot -> add '.00'
            f"{m.group(1).replace('.', '')}.00 {m.group(3)}" if not m.group(2) or len(m.group(2)) == 4 else
            # If one digit after the decimal -> replace the decimal separator by '.' and add '0'
            f"{m.group(1).replace('.', '')}.{m.group(2)[1]}0 {m.group(3)}" if len(m.group(2)) == 2 else
            # If two digits after the decimal -> replace the decimal separator by '.' and add nothing
            f"{m.group(1).replace('.', '')}.{m.group(2)[1:]} {m.group(3)}"
        ), text)
    
    return text

# Context lists
contextInvoiceNumber = ["facture#", "facturation#", "#facture", "#facturation", "facture #", "facturation #",
                        "# facture", "# facturation", "numéro de facture", "numero de facture"]
contextSupplierName = ["e.i.", "eurl", "e.u.r.l.", "sarl", "s.a.r.l.", "sasu", "s.a.s.u.", "sas", "s.a.s.", 
                       "s.a.", "sci", "s.c.i.", "snc", "s.n.c.", "scs", "s.c.s.", "sca", "s.c.a."] # excluded: "ei", "sa"
contextClientName = ["m.", "mme", "mm", "mrs", "monsieur", "madame", "client", "titulaire", "facturer à", "facturer a"]
contextInvoiceAmount = ["ttc", "t.t.c.", "toutes taxes comprises"]
contextInvoiceDate = ["date de facture", "date de la facture", "date de facturation", "date de la facturation"]
contextDueDate = ["échéance", "echeance", "payable jusqu'au", "à payer jusqu'à", "a payer jusqu'a", "due", "prélevé", "preleve"]

# Function to check if a given string appears with context in any of the ROI lines
def checkContextRelevance(text : str, context : list, ocrOutput : dict):
    for roiNum in ocrOutput:
        for lineNum in ocrOutput[roiNum]:
            line = ocrOutput[roiNum][lineNum]
            if text.lower() in line.lower() and any (term in line.lower() for term in context):
                return True, roiNum, lineNum
    return False, None, None

# Function to extract the relevant invoice data from the OCR and NER output (with the help of context rules)
def extractData(ocrOutput : dict, nerOutput : spacy.tokens.Doc, roiNumSupplier : int):
    
    # Initialize the dictionary for the captured data
    capturedData = {
    "invoiceNumber": None,
    "supplierName": None,
    "clientName": None,
    "invoiceAmount": None,
    "invoiceDate": None,
    "dueDate": None
    }

    # If available, extract supplier and client information from both the OCR and the NER output
    for ent in nerOutput.ents:
        if ent.label_ == "ORG":
            if capturedData["supplierName"] is None and ent.text not in contextClientName:
                relevantContext = checkContextRelevance(text=ent.text, context=contextSupplierName, ocrOutput=ocrOutput)
                if relevantContext[0] == True:
                    legalForm = [term for term in contextSupplierName if term in ocrOutput[relevantContext[1]][relevantContext[2]]][0].upper().replace('.', '')
                    capturedData["supplierName"] = ent.text + " " + legalForm
                elif ent.text.lower() in ocrOutput[roiNumSupplier].values():
                    capturedData["supplierName"] = ent.text
        elif (ent.label_ == "MISC"):
            if capturedData["supplierName"] is None and ent.text not in contextClientName:
                relevantContext = checkContextRelevance(text=ent.text, context=contextSupplierName, ocrOutput=ocrOutput)
                if relevantContext[0] == True:
                    legalForm = [term for term in contextSupplierName if term in ocrOutput[relevantContext[1]][relevantContext[2]]][0].upper().replace('.', '')
                    capturedData["supplierName"] = ent.text + " " + legalForm
        elif ent.label_ == "PER":
            if capturedData["clientName"] is None and checkContextRelevance(text=ent.text, context=contextClientName, ocrOutput=ocrOutput)[0]:
                capturedData["clientName"] = ent.text
    
    # Extract the remaining information from the OCR dictionary, using only the context rules
    for roiNum in ocrOutput:
        for lineNum in ocrOutput[roiNum]:
            line = ocrOutput[roiNum][lineNum]
            
            # Extract invoice number
            if capturedData['invoiceNumber'] is None and any(term in line for term in contextInvoiceNumber):
                match = re.search(r"\b(\d+)\b", line)
                if match:
                    capturedData["invoiceNumber"] = match.group(1)

            # Extract supplier name (if not found through NER)
            if capturedData['supplierName'] is None and any(term in line for term in contextSupplierName):
                capturedData["supplierName"] = line

            # Extract client name (if not found through NER)
            if capturedData['clientName'] is None and any(term in line for term in contextClientName):
                capturedData["clientName"] = ' '.join([word for word in line.split() if word not in contextClientName]).title()
            
            # Extract the invoice amount
            if capturedData["invoiceAmount"] is None and any(term in line for term in contextInvoiceAmount):
                match = re.search(r"([\d,.]+)\s(eur)", line)
                if match:
                    capturedData["invoiceAmount"] = f"{match.group(1)} {match.group(2).upper()}"

            # Extract the invoice date
            if capturedData["invoiceDate"] is None and any(term in line for term in contextInvoiceDate):
                match = re.search(r"\b(\d{4}-\d{2}-\d{2})\b", line)
                if match:
                    capturedData["invoiceDate"] = match.group(1)
            
            # Extract the due date
            if capturedData["dueDate"] is None and any(term in line for term in contextDueDate):
                match = re.search(r"\b(\d{4}-\d{2}-\d{2})\b", line)
                if match:
                    capturedData["dueDate"] = match.group(1)

    return capturedData