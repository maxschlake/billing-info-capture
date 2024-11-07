import cv2
import process
from PIL import Image
import pytesseract
import os

imageRawFileName = "book"
imageRawFileType = "jpg"
imageRawFile = imageRawFileName + "." + imageRawFileType
imageRawDir = "images/raw"
imageRawFilePath = os.path.join(imageRawDir, imageRawFile)
imageModDir = os.path.join(os.path.dirname(imageRawDir), "mod")
process.createDirectory(imageModDir)

# With pillow
# im = Image.open(imageFile)
# im.rotate(90).show()
# im.save("images/mod/")

# With OpenCV
img = cv2.imread(imageRawFilePath)
# cv2.imshow("original image", img)
# cv2.waitKey(0)

# 1) Invert
mod = "_invert"
invertedImage = cv2.bitwise_not(img)
outputImage = invertedImage

# 2) Rescale
mod = "_rescale"
# outputImage = rescaledImage

# 3) Binarize
mod = "_binarize"

# Turn first into gray scale image as it facilitates binarization
grayImage = process.grayScale(img)
thresh = 127.0
maxVal = 255
thresh, bwImage = cv2.threshold(grayImage, thresh=thresh, maxval=maxVal, type=cv2.THRESH_BINARY)
outputImage = bwImage


# Save output file
imageModFilePath = os.path.join(imageModDir, imageRawFileName + mod + "." + imageRawFileType)
cv2.imwrite(imageModFilePath, outputImage)


