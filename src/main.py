import cv2
import process
from PIL import Image
import pytesseract
import os

imageRawFileName = "test"
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
img = process.resize(img, 0.3)

# 1) Invert
mod = "_invert"
# invertedImage = cv2.bitwise_not(img)
# outputImage = invertedImage

# 2) Rescale
mod = "_rescale"
# outputImage = rescaledImage

# 3) Binarize
mod = "_binarize"

# Turn image into gray scale image as it facilitates binarization
# grayImage = process.grayScale(img)
# thresh = 127.0
# maxVal = 255
# thresh, bwImage = cv2.threshold(grayImage, thresh=thresh, maxval=maxVal, type=cv2.THRESH_BINARY)
# outputImage = bwImage

# 4) Remove noise
# mod = "_denoise"
# denoisedImage = process.removeNoise(bwImage, kernelSizeDil=2, iterationsDil=1, kernelSizeEr=1, iterationsEr=1, kernelSizeMorph=1, kernelSizeBlur=1)
# outputImage = denoisedImage
# cv2.imshow("denoised image", outputImage)
# cv2.waitKey(0)

# 5) Adjust font sizes with erosion and dilation
mod = "_fontChange"
# fontChangeImage = process.changeFontSize(img, changeType="dilate", kernelSize=2, iterations=1)
# outputImage = fontChangeImage

# 6) Add borders
# mod = "_withBorders"
# withBordersImage = process.addBorders(denoisedImage, borderWidth=150, maxVal=255)
# outputImage = withBordersImage

# 7) Remove borders
mod = "_withoutBorders"
# withoutBordersImage = process.removeBorders(img)
# outputImage = withoutBordersImage

# 8) Deskew
mod = "_deskew"
deskewedImage = process.deskew(img)
outputImage = deskewedImage

# Save output file
imageModFilePath = os.path.join(imageModDir, imageRawFileName + mod + "." + imageRawFileType)
cv2.imwrite(imageModFilePath, outputImage)

# SHow output file
imgMod = cv2.imread(imageModFilePath)
cv2.imshow("modified image", imgMod)
cv2.waitKey(0)

