import os
import io
import subprocess
import shutil
import time
import json
import pika
from PIL import Image, ImageOps
import numpy as np
from skimage import data, img_as_float, io as skio
from skimage.metrics import structural_similarity as ssim

#Collect environment variables
interval = int(os.environ.get('CAPTURE_INTERVAL_SECONDS', '300'))
camName = os.environ.get('CAMERA_NAME')
rtspUrl = os.environ.get('CAMERA_RTSP_URL')
ssimCompareThreshold = float(os.environ.get('SSIM_THRESHOLD', 0.9))

optionalThumbnailSaveDirectory = os.environ.get('CAMERA_THUMBNAIL_DIR', '')
optionalNativeSaveDirectory = os.environ.get('CAMERA_NATIVE_DIR', '')

rabbitMqHost = os.environ.get("RABBITMQ_HOST", '')
rabbitMqPort = int(os.environ.get("RABBITMQ_PORT", 5672))
rabbitMqVDir = os.environ.get("RABBITMQ_VDIR", '/')
rabbitMqUser = os.environ.get("RABBITMQ_USER")
rabbitMqPass = os.environ.get("RABBITMQ_PASS")
rabbitMqExchange = os.environ.get("RABBITMQ_EXCHANGE", "knighware.cameraImages")
rabbitMqRoutingKey = os.environ.get("RABBITMQ_ROUTING_KEY", "actions.write")

currentNativeImageFile = "./capture-current-native.jpg"
currentImageFile = "./capture-current.jpg"
lastImageFile = "./capture-last.jpg"

def writeRabbitMessage(messageBody):

    if rabbitMqHost is None:
        return

    try:
        rabbitCreds = pika.PlainCredentials(rabbitMqUser, rabbitMqPass)
        rabbitParams = pika.ConnectionParameters(rabbitMqHost, rabbitMqPort, rabbitMqVDir, rabbitCreds)
        rabbitConn = pika.BlockingConnection(rabbitParams)
        rabbitChannel = rabbitConn.channel()
        rabbitChannel.exchange_declare(exchange=rabbitMqExchange, exchange_type='topic', durable=True)

        print("Writing to RabbitMQ {0}{1}:{2}".format(rabbitMqHost, rabbitMqVDir, rabbitMqRoutingKey))        
        rabbitChannel.basic_publish(exchange=rabbitMqExchange, 
            routing_key=rabbitMqRoutingKey, 
            body=json.dumps(messageBody), 
            properties=pika.BasicProperties(content_type="application/json"))

        rabbitConn.close()
    except Exception as e:
        print("Failed to write RabbitMQ message: {0}".format(e))


#Run in infinite loop
while True:

    #Capture frame of video using FFMPEG
    timestamp = time.strftime("%Y-%m-%d_%H-%M-%S")
    print("{0}: Obtaining next video frame for '{1}'".format(timestamp, camName))
    p = subprocess.Popen(["ffmpeg", "-y", "-i", str(rtspUrl), "-loglevel", "panic", "-hide_banner", "-vframes", "1", str(currentNativeImageFile)])
    p.wait()
    if p.returncode == 0:
    
        #Scale image down and convert to grayscale
        image = Image.open(currentNativeImageFile)
        image.thumbnail((512,512), Image.ANTIALIAS)
        image = ImageOps.grayscale(image)
        image.save(currentImageFile)

        #Compare to previously captured image
        if os.path.isfile(lastImageFile):
            lastImageData = skio.imread(lastImageFile)
            imageData = skio.imread(currentImageFile)
            ssim_compare = ssim(imageData, lastImageData, data_range=lastImageData.max() - lastImageData.min())
            if ssim_compare < ssimCompareThreshold:
                print("{0} Image change detected - SSIM value is {1}".format(camName, ssim_compare))

                #Optionally write thumbnail to output directory
                if optionalThumbnailSaveDirectory != '' and os.path.isdir(optionalThumbnailSaveDirectory):
                    thumbPath = os.path.join(optionalThumbnailSaveDirectory, timestamp+".jpg")
                    print("Writing thumbnail to {0}".format(thumbPath))
                    shutil.copyfile(currentImageFile, thumbPath)

                #Optionally write native image to output directory
                if optionalNativeSaveDirectory != '' and os.path.isdir(optionalNativeSaveDirectory):
                    nativePath = os.path.join(optionalNativeSaveDirectory, timestamp+".jpg")
                    print("Writing native image to {0}".format(nativePath))
                    shutil.copyfile(currentNativeImageFile, nativePath)

                #Optionally write message to message queue to process
                if rabbitMqHost is not None:
                    imageBytes = io.BytesIO()
                    image.save(imageBytes, format='JPEG')
                    messageBody = {
                        "captureTime": timestamp,
                        "camName": camName,
                        "imageData": imageBytes.getvalue().hex()
                    }
                    writeRabbitMessage(messageBody)


        #Store current image as last image
        #We do this even if the image hasn't changed, as it allows for slow change (daylight to night, for example)
        shutil.copyfile(currentImageFile, lastImageFile)

    else:
        print("Failed to capture image: {0}".format(p.returncode))

    #Wait for next iteration
    time.sleep(interval)
