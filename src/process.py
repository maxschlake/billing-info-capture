import os
import cv2
from matplotlib import pyplot as plt


# Function to create a new directory if it does not yet exist
def createDirectory(dir, verbose=False):
    if not os.path.exists(dir):
        os.makedirs(dir, exist_ok=True)
        if verbose:
            print(f"Created directory: {dir}")
    else:
        if verbose:
            print(f"Directory {dir} already exists.")


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