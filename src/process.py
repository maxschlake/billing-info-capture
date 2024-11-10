import os
import cv2
from matplotlib import pyplot as plt
import numpy as np
from PIL import Image


# Function to create a new directory if it does not yet exist
def createDirectory(dir, verbose: bool=False):
    if not os.path.exists(dir):
        os.makedirs(dir, exist_ok=True)
        if verbose:
            print(f"Created directory: {dir}")
    else:
        if verbose:
            print(f"Directory {dir} already exists.")

# Funcion to resize an image
def resize(image, scale : float = 1.0):
    width = int(image.shape[1] * scale)
    height = int(image.shape[0] * scale)
    image = cv2.resize(image, (width, height))
    return image

# Function to display the entire image
def display(imagePath):
    
    dpi = 80
    imageData = plt.imread(imagePath)
    height, width, depth = imageData.shape

    # Compute size
    figSize = width / float(dpi), height / float(dpi)

    # Create figure
    fig = plt.figure(figsize=figSize)
    ax = fig.add_axes([0, 0, 1, 1])

    # Hide spines, ticks, etc.
    ax.axis('off')

    # Display the image 
    ax.imshow(imageData, cmap='gray')
    plt.show()


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
    newImage = resize(newImage, 1.0)
    # cv2.imshow("newImage", newImage)
    # cv2.waitKey(0)
    # Prepare image, convert to gray scale, blur, and threshold
    if len(newImage.shape) == 3:
        gray = cv2.cvtColor(src=newImage, code=cv2.COLOR_BGR2GRAY)
    else:
        gray = newImage
    blur = cv2.GaussianBlur(src=gray, ksize=(1, 1), sigmaX=0)
    # cv2.imshow("blur", blur)
    # cv2.waitKey(0)
    thresh = cv2.threshold(src=blur, thresh=0, maxval=255, type=cv2.THRESH_BINARY_INV + cv2.THRESH_OTSU)[1]
    # cv2.imshow("thresh", thresh)
    # cv2.waitKey(0)

    # Apply dilate to merge text into meaningful lines/paragraphs
    # Use larger kernel on x axis to merge characters into single line, cancelling out any spaces
    # Use smaller kernel on y axis to separate between different blocks of text
    kernel = cv2.getStructuringElement(shape=cv2.MORPH_RECT, ksize=(30, 5))
    dilate = cv2.dilate(src=thresh, kernel=kernel, iterations=1)
    # cv2.imshow("dilate", dilate)
    # cv2.waitKey(0)

    # Find all contours
    contours, hierarchy = cv2.findContours(image=dilate, mode=cv2.RETR_LIST, method=cv2.CHAIN_APPROX_SIMPLE)
    contours = sorted(contours, key=cv2.contourArea, reverse=True)
    test = cv2.drawContours(image=dilate, contours=contours, contourIdx=-1, color=(0, 255, 0))
    # cv2.imshow("test", test)  # Display the image with the contour
    # cv2.waitKey(0)  # Wait for a key press to close the window
    # for c in contours:
    #     rect = cv2.boundingRect(c)
    #     x, y, w, h = rect
    #     cv2.rectangle(img=newImage, pt1=(x, y), pt2=(x + w, y + h), color=(0, 255, 0), thickness=2)
    
    # Find largest contour and surround in min area box
    largestContour = contours[0]
    # cv2.imshow("Largest Contour", resizedImage)  # Display the image with the contour
    # cv2.waitKey(0)  # Wait for a key press to close the window
    # cv2.destroyAllWindows()
    # im = Image.open(test)
    # im.show()
    if verbose == True:
        print(f"Number of contours: {len(contours)}")
    minAreaRect = cv2.minAreaRect(largestContour)
    box = cv2.boxPoints(minAreaRect)  # Get the four corners of the rectangle
    box = np.int0(box)  # Convert to integer coordinates
    # cv2.drawContours(newImage, [box], 0, (255, 0, 0), 2)  # Draw the rectangle on the image
    # cv2.imshow("box", newImage)
    # cv2.waitKey(0)
    angle = minAreaRect[-1]
    print(f"angle: {angle}")
    # if height > width, the (distorted) rotation is likely clockwise
    if minAreaRect[1][1] > minAreaRect[1][0]: 
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
    contours, hierarchy = cv2.findContours(image, mode=cv2.RETR_EXTERNAL, method=cv2.CHAIN_APPROX_SIMPLE)
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