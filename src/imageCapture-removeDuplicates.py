import os
import io
from PIL import Image, ImageOps
import numpy as np
from skimage import data, img_as_float, io as skio
from skimage.metrics import structural_similarity as ssim

ssimCompareThreshold = float(os.environ.get('SSIM_THRESHOLD', 0.8))
imageDirectory = os.environ.get('CAMERA_THUMBNAIL_DIR', '')

lastImageData = None

#Get files in target directory
for fileEntry in os.listdir(imageDirectory):
    fullPath = os.path.join(imageDirectory, fileEntry)
    if os.path.isfile(fullPath):
        print(fileEntry)

        imageData = skio.imread(fullPath)

        if lastImageData is not None:
            ssim_compare = ssim(imageData, lastImageData, data_range=lastImageData.max() - lastImageData.min())
            if ssim_compare < ssimCompareThreshold:
                print("{0} SSIM value is {1} - Image change detected".format(fileEntry, ssim_compare))
            else:
                print("{0} SSIM value is {1}".format(fileEntry, ssim_compare))
                os.remove(fullPath)

        #Save for next iteration
        lastImageData = imageData