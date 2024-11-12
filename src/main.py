import cv2
import process
from PIL import Image
import pytesseract
import os
import tkinter

# 0) Setup
# 0.1) Select the image to be processed and create additional directories
imageRawFileName = "facture1"
imageRawFileType = "jpg"
imageRawFile = imageRawFileName + "." + imageRawFileType
imageRawDir = "images/raw"
imageRawFilePath = os.path.join(imageRawDir, imageRawFile)
imageModDir = os.path.join(os.path.dirname(imageRawDir), "mod")
process.createDirectory(imageModDir)

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
    img = process.resize(img, targetWidth=targetWidth, targetHeight=targetHeight)

# 1) Start automatic image processing

# 1.1) Deskew
mod = "_deskew"
img_deskwed = process.deskew(img)

# 1.1) Binarize
mod = "_binarize"
img = process.grayScale(img_deskwed) # gray scale facilitates binarization

mod = "_invert"
img = cv2.bitwise_not(img)

# img = process.changeFontSize(img, changeType="dilate", kernelSize=1, iterations=1)
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

# 3) Save output file
imageModFilePath = os.path.join(imageModDir, imageRawFileName + mod + "." + imageRawFileType)
cv2.imwrite(imageModFilePath, img)

# Show output file
# imgMod = cv2.imread(imageModFilePath)
# cv2.imshow("modified image", imgMod)
# cv2.waitKey(0)

# Apply OCR

ocr_result1 = pytesseract.image_to_string(imageRawFilePath)
ocr_result2 = pytesseract.image_to_string(imageModFilePath)

img_mod = cv2.imread(imageModFilePath)
roiList = process.identifyStructure(img_mod, img_deskwed, kernelSizeBlur=1, stddevBlur=0)
ocr_results = []
for roi in roiList:
    config = "--oem 1 --psm 4"
    text = pytesseract.image_to_string(roi, config=config).strip()
    if text:
        for line in text.split("\n"):
            if line:
                ocr_results.append(line)
ocr_result3 = "\n".join(ocr_results)
print(ocr_result3)
