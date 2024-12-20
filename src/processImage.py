import cv2
import numpy as np


# Funcion to resize an image to targetWidth and targetHeight while preserving the aspect ratio
def resize(image, targetWidth : int, targetHeight : int, aspectRatio : float, landscape : bool=False):
    if landscape:
        targetHeight = int(targetWidth / aspectRatio)
    else: 
        targetWidth = int(targetHeight * aspectRatio)
    image = cv2.resize(image, (targetWidth, targetHeight))
    return image

# Funtion to obtain a gray scale image
def grayScale(image):
    return cv2.cvtColor(image, cv2.COLOR_BGR2GRAY)

# Function to remove noise
def removeNoise(image, kernelSizeDil : int, iterationsDil : int, kernelSizeEr : int, iterationsEr : int, kernelSizeMorph : int, kernelSizeBlur : int):
    kernel = np.ones((kernelSizeDil, kernelSizeDil), np.uint8)
    image = cv2.dilate(src=image, kernel=kernel, iterations=iterationsDil)
    kernel = np.ones((kernelSizeEr, kernelSizeEr), np.uint8)
    image = cv2.erode(src=image, kernel=kernel, iterations=iterationsEr)
    kernel = np.ones((kernelSizeMorph, kernelSizeMorph), np.uint8)
    image = cv2.morphologyEx(src=image, op=cv2.MORPH_CLOSE, kernel=kernel)
    image = cv2.medianBlur(src=image, ksize=kernelSizeBlur)
    return image

# Function to change the font size
def changeFontSize(image, changeType: str, kernelSize: int, iterations: int):

    # Invert image (required for the erode command) and set kernel
    image = cv2.bitwise_not(image)
    kernel = np.ones((kernelSize, kernelSize), np.uint8)

    if changeType == "erode":
        image = cv2.erode(src=image, kernel=kernel, iterations=iterations)
    elif changeType == "dilate":
        image = cv2.dilate(src=image, kernel=kernel, iterations=iterations)

    # Revert image back
    image = cv2.bitwise_not(image)

    return image

# Function to get the skew angle of an image
# Corrected version of the original by: Leo Ertuna (https://becominghuman.ai/how-to-automatically-deskew-straighten-a-text-image-using-opencv-a0c30aed83df)
# see changes in the cv2.minAreaRect() function since version 4.5.1: https://github.com/opencv/opencv/issues/19472
def getSkewAngle(image, verbose: bool=False) -> float:

    newImage = image.copy()

    # Prepare image, convert to gray scale, blur, and threshold
    if len(newImage.shape) == 3:
        gray = cv2.cvtColor(src=newImage, code=cv2.COLOR_BGR2GRAY)
    else:
        gray = image
    blur = cv2.GaussianBlur(src=gray, ksize=(1, 1), sigmaX=0)
    thresh = cv2.threshold(src=blur, thresh=0, maxval=255, type=cv2.THRESH_BINARY_INV + cv2.THRESH_OTSU)[1]
    kernel = cv2.getStructuringElement(shape=cv2.MORPH_RECT, ksize=(30, 5))
    dilate = cv2.dilate(src=thresh, kernel=kernel, iterations=1)

    # Find all contours
    contours = cv2.findContours(image=dilate, mode=cv2.RETR_LIST, method=cv2.CHAIN_APPROX_SIMPLE)[0]
    contours = sorted(contours, key=cv2.contourArea, reverse=True)
    newImage = cv2.drawContours(image=newImage, contours=contours[-1], contourIdx=-1, color=(0, 255, 0))

    # Check if we have any contours at all
    if len(contours) == 0:
        print("No contours found.")
        return 0
    
    # Find largest contour and surround in min area box
    largestContour = contours[0]
    newImage = cv2.drawContours(newImage, [largestContour], -1, (255, 0, 0), 2) 
    minAreaRect = cv2.minAreaRect(largestContour)
    angle = minAreaRect[-1]

    # if height > width, the (distorted) rotation is likely clockwise
    if angle < 45: 
        return -angle
    # if width > height, the (distorted) rotation is likely counterclockwise
    else:
        return 90.0 - angle

# Function to rotate an image
# Source: Leo Ertuna (https://becominghuman.ai/how-to-automatically-deskew-straighten-a-text-image-using-opencv-a0c30aed83df)
def rotate(image, angle: float):
    (h, w) = image.shape[:2]
    center = (w // 2, h // 2)
    M = cv2.getRotationMatrix2D(center=center, angle=angle, scale=1.0)
    image = cv2.warpAffine(src=image, M=M, dsize=(w, h), flags=cv2.INTER_CUBIC, borderMode=cv2.BORDER_REPLICATE)
    return image

# Function to get the skew angle and rotate the image accordingly
# Source: Leo Ertuna (https://becominghuman.ai/how-to-automatically-deskew-straighten-a-text-image-using-opencv-a0c30aed83df)
def deskew(image, verbose: bool=False):
    angle = getSkewAngle(image, verbose)
    return rotate(image, angle=-angle)

# Function to remove borders
def removeBorders(image):
    contours = cv2.findContours(image, mode=cv2.RETR_EXTERNAL, method=cv2.CHAIN_APPROX_SIMPLE)[0]
    contoursSorted = sorted(contours, key=lambda x:cv2.contourArea(x))
    largestContour = contoursSorted[-1]
    x, y, w, h = cv2.boundingRect(largestContour)
    image = image[y:y + h, x:x + w]
    return image

# Function to add borders
def addBorders(image, borderWidth : int, maxVal : int=255):
    color = [maxVal, maxVal, maxVal]
    top, bottom, left, right = [borderWidth] * 4
    image = cv2.copyMakeBorder(src=image, top=top, bottom=bottom, left=left, right=right, borderType=cv2.BORDER_CONSTANT, value=color)
    return image

# Function to identify regions of interest (ROI) in an image and create a sorted list thereof
def identifyStructure(image, imageDeskewed, kernelSizeBlur : int, stddevBlur : float, landscape : bool=False):
    roiList = []
    if len(imageDeskewed.shape) == 3:
        gray = cv2.cvtColor(src=imageDeskewed, code=cv2.COLOR_BGR2GRAY)
    else:
        gray = imageDeskewed
    blur = cv2.GaussianBlur(src=gray, ksize=(kernelSizeBlur, kernelSizeBlur), sigmaX=stddevBlur)
    thresh = cv2.threshold(src=blur, thresh=0, maxval=255, type=cv2.THRESH_BINARY_INV + cv2.THRESH_OTSU)[1]
    if landscape:
        kernel = cv2.getStructuringElement(cv2.MORPH_RECT, (75, 30))
    else:
        kernel = cv2.getStructuringElement(cv2.MORPH_RECT, (65, 20)) #65/45
    dilate = cv2.dilate(src=thresh, kernel=kernel, iterations=1)
    contours = cv2.findContours(image=dilate, mode=cv2.RETR_EXTERNAL, method=cv2.CHAIN_APPROX_SIMPLE)
    contours = contours[0] if len(contours) == 2 else contours[1]
    contours = sorted(contours, key=lambda x: (cv2.boundingRect(x)[1], cv2.boundingRect(x)[0]))
    rectDict = {}
    for i, c in enumerate(contours):
        x, y, w, h = cv2.boundingRect(c)
        if h > 10 and w > 10:
            rectDict[i] = x, y, w, h
            roi = image[y:y+h, x:x+w]
            roiList.append(roi)
    return roiList, rectDict
