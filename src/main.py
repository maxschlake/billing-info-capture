from pipeline import createDataDict
import json


# Demonstration with two example invoices:
invoiceList = []

# Run each invoice throug the pipeline and append the captured data to the invoice list
for invoice in [["facture1", "jpg"], ["facture2", "jpg"]]:

    capturedData = createDataDict(invoice[0], invoice[1], nerModel="fr_core_news_lg", saveImages=True)
    invoiceList.append(capturedData)

# Write athe list of invoices into a JSON file
with open("invoiceData.json", "w") as jsonFile:
    json.dump(invoiceList, jsonFile, indent=4)
