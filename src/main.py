import cv2
import processImage
import processText
from PIL import Image
import pytesseract
import os
import tkinter
import pandas as pd
import spacy
import json


# 0) Setup
# 0.1) Select the image to be processed and create additional directories
imageRawFileName = "facture2"
imageRawFileType = "jpg"
imageRawFile = imageRawFileName + "." + imageRawFileType
imageRawDir = "images/raw"
imageRawFilePath = os.path.join(imageRawDir, imageRawFile)
imageModDir = os.path.join(os.path.dirname(imageRawDir), "mod")
processImage.createDirectory(imageModDir)

# 0.2) Load the image
img = cv2.imread(imageRawFilePath)

# 0.3) Get the screen dimensions and adjust the image size if requested
resize = False
screenPerc = 1.0
if resize:
    tk = tkinter.Tk()
    screenWidth = tk.winfo_screenwidth()
    screenHeight = tk.winfo_screenheight()
    tk.destroy()
    targetWidth = int(screenWidth * screenPerc)
    targetHeight = int(screenHeight * screenPerc)
    img = processImage.resize(img, targetWidth=targetWidth, targetHeight=targetHeight)

# 1) Process the image

# 1.1) Deskew
img_deskwed = processImage.deskew(img)

# 1.2) Binarize
img = processImage.grayScale(img_deskwed) # gray scale facilitates binarization

# 1.3) Invert
img = cv2.bitwise_not(img)

# 1.4) Change font size
img = processImage.changeFontSize(img, changeType="dilate", kernelSize=2, iterations=1)
mod = "_mod"

# cv2.imshow("2", img)
# cv2.waitKey(0)

# 3) Remove noise
# mod = "_denoise"
# img = process.removeNoise(img, kernelSizeDil=2, iterationsDil=1, kernelSizeEr=2, iterationsEr=1, kernelSizeMorph=1, kernelSizeBlur=1)
# cv2.imshow("denoised image", img)
# cv2.waitKey(0)

# thresh = 220.0
# maxVal = 255
# img = cv2.threshold(img, thresh=thresh, maxval=maxVal, type=cv2.THRESH_BINARY)[1]
# cv2.imshow("2", img)
# cv2.waitKey(0)

# 4) Adjust font sizes with erosion and dilation
# mod = "_fontChange"
# fontChangeImage = process.changeFontSize(img, changeType="dilate", kernelSize=2, iterations=1)
# outputImage = fontChangeImage

# 5) Add borders
# mod = "_withBorders"
# withBordersImage = process.addBorders(denoisedImage, borderWidth=150, maxVal=255)
# outputImage = withBordersImage

# 1.1) Binarize
# mod = "_binarize"
# img = process.grayScale(img) # gray scale facilitates binarization
# thresh = 210.0
# maxVal = 255
# img = cv2.threshold(img, thresh=thresh, maxval=maxVal, type=cv2.THRESH_BINARY)[1]
# cv2.imshow("1", img)
# cv2.waitKey(0)

# 1.2) Remove borders
# mod = "_withoutBorders"
# img = process.removeBorders(img)

# 1.5) Save output image
imageModFilePath = os.path.join(imageModDir, imageRawFileName + mod + "." + imageRawFileType)
cv2.imwrite(imageModFilePath, img)

# Show output file
# imgMod = cv2.imread(imageModFilePath)
# cv2.imshow("modified image", imgMod)
# cv2.waitKey(0)

# 2) Apply OCR

# 2.1) Obtain ROIs from the modified image
img_mod = cv2.imread(imageModFilePath)
roiList = processImage.identifyStructure(img_mod, img_deskwed, kernelSizeBlur=1, stddevBlur=0)

# 2.2) Build OCR list and dictionary
ocrResultsList = []
ocrResultsDict = {}
roiNum = 0
ocrConfig = "--oem 1 --psm 4"
for roi in roiList:
    if roi.any():
        text = pytesseract.image_to_string(roi, config=ocrConfig).strip()
        if text:
            lineNum = 0
            ocrResultsDict[roiNum] = {}
            for line in text.split("\n"):
                if line:
                    line = processText.standardize(line)
                    ocrResultsList.append(line)
                    ocrResultsDict[roiNum][lineNum] = line.lower()
                    lineNum += 1
            roiNum += 1
ocr = "\n".join(ocrResultsList)
print(ocr)
print(ocrResultsDict)

# 3) Apply NER with the selected model
model_sm = "fr_core_news_sm"
model_md = "fr_core_news_md"
model_lg = "fr_core_news_lg"
model_trf = "fr_dep_news_trf"
ner = spacy.load(model_lg)
nerDoc = ner(ocr)

# 4) Create the final JSON file from the extracted invoice data

# 4.1) Build the invoice data dictionary from OCR and NER results
invoiceData = processText.extractData(ocrOutput=ocrResultsDict, nerOutput=nerDoc)

for ent in nerDoc.ents:
    print(ent.text, ent.label_)

print(invoiceData)

# 4.2) Create JSON file from the invoice data dictionary