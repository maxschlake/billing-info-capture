import processImage
import processText
import cv2
import pytesseract
import os
import tkinter
import spacy


# Function to create a new directory if it does not yet exist
def createDirectory(dir, verbose: bool=False):
    if not os.path.exists(dir):
        os.makedirs(dir, exist_ok=True)
        if verbose:
            print(f"Created directory: {dir}")
    else:
        if verbose:
            print(f"Directory {dir} already exists.")

# Function which wraps all the different processing functions in order to capture the invoice data with OCR & NER
def createDataDict(imageRawFileName : str, imageRawFileType : str, nerModel : str="fr_core_news_lg", saveImages : bool=False):
    # 0) Setup
    # 0.1) Create additional strings and directories
    imageRawFile = imageRawFileName + "." + imageRawFileType
    imageRawDir = "images/raw"
    imageRawFilePath = os.path.join(imageRawDir, imageRawFile)
    imageModDir = os.path.join(os.path.dirname(imageRawDir), "mod")
    createDirectory(imageModDir)

    # 0.2) Load the image
    img = cv2.imread(imageRawFilePath)

    # 0.3 Compute aspect ratio and detect landscape format
    imageWidth = img.shape[1]
    imageHeight = img.shape[0]
    aspectRatio = imageWidth / imageHeight
    if imageWidth >= imageHeight:
        landscape = True
    else:
        landscape = False

    # 0.4) Get the screen dimensions and adjust the image size if requested
    # (Note: Only for presentation purposes; this will affect the output quality)
    resize = False
    screenPerc = 1.0
    if resize:
        tk = tkinter.Tk()
        screenWidth = tk.winfo_screenwidth()
        screenHeight = tk.winfo_screenheight()
        tk.destroy()
        targetWidth = int(screenWidth * screenPerc)
        targetHeight = int(screenHeight * screenPerc)
        img = processImage.resize(img, targetWidth=targetWidth, targetHeight=targetHeight,
                                aspectRatio=aspectRatio, landscape=landscape)

    # 1) Process the image
    # 1.1) Deskew
    imgDeskwed = processImage.deskew(img)

    # 1.2) Binarize
    img = processImage.grayScale(imgDeskwed) # gray scale facilitates binarization

    # 1.3) Invert
    img = cv2.bitwise_not(img)

    # 1.4) Change font size
    img = processImage.changeFontSize(img, changeType="dilate", kernelSize=2, iterations=1)

    # 1.5) Save output images (if requested)
    if saveImages:
        imageDeskFilePath = os.path.join(imageModDir, imageRawFileName + "_desk" + "." + imageRawFileType)
        imageModFilePath = os.path.join(imageModDir, imageRawFileName + "_mod" + "." + imageRawFileType)
        cv2.imwrite(imageDeskFilePath, imgDeskwed)
        cv2.imwrite(imageModFilePath, img)

    # 2) Apply OCR
    # 2.1) Obtain ROIs from the modified image and save the image with ROI rectangles (if requested)
    roiList, rectDict = processImage.identifyStructure(img, imgDeskwed, kernelSizeBlur=1, stddevBlur=0, landscape=landscape)
    imgRect = cv2.cvtColor(img, cv2.COLOR_GRAY2BGR)
    for roiNum in rectDict:
        x, y, w, h = rectDict[roiNum]
        imgRect = cv2.rectangle(imgRect, (x, y), (x + w, y + h), (36, 255, 12), 2)
    
    if saveImages:
        imageRectFilePath = os.path.join(imageModDir, imageRawFileName + "_rect" + "." + imageRawFileType)
        cv2.imwrite(imageRectFilePath, imgRect)

    # 2.2) Build OCR list and dictionary
    ocrConfig = "--oem 1 --psm 4"
    ocrResultsList = []
    ocrResultsDict = {}
    roiNum = 0
    maxAvCharHeight = 0
    roiNumMaxAvCharHeight = None
    for roi in roiList:
        if roi.any():
            string = pytesseract.image_to_string(roi, config=ocrConfig).strip()
            data = pytesseract.image_to_data(roi, config=ocrConfig, output_type=pytesseract.Output.DICT)
            if string:

                # Identify the ROI with the largest average characterheight
                charHeightList = [data["height"][i] for i, txt in enumerate(data["text"]) if txt.strip()]
                avCharHeight = sum(charHeightList) / len(charHeightList)
                if avCharHeight > maxAvCharHeight:
                    maxAvCharHeight = avCharHeight
                    roiNumMaxAvCharHeight = roiNum
                    
                lineNum = 0
                ocrResultsDict[roiNum] = {}
                for line in string.split("\n"):
                    if line:
                        line = processText.standardize(line)
                        ocrResultsList.append(line)
                        ocrResultsDict[roiNum][lineNum] = line.lower()
                        lineNum += 1
                roiNum += 1
    ocr = "\n".join(ocrResultsList)

    # 3) Apply NER with the selected model
    ner = spacy.load(nerModel)
    nerDoc = ner(ocr)

    # 4) Create the final dictionary from the captured data
    capturedData = processText.extractData(ocrOutput=ocrResultsDict, nerOutput=nerDoc, roiNumSupplier=roiNumMaxAvCharHeight)

    return capturedData