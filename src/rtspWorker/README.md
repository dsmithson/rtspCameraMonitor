# What is RtspCameraMonitor?

RtspCaperaCapture is an application which uses FFMPEG to grab an image from an RTSP enabled camera at a specified interval.  Upon capturing an image, the application compares the image to the prior captured image.  If the content of the image has changed by more than a certain amount, then the image will optionally be (1) saved to a file, (2) have it's grayscale thumbnail image saved to a file, or (3) write a JSON encoded message to a RabbitMQ server.

### Quick reference

- [RtspCameraMonitor github repo](https://github.com/dsmithson/rtspCameraMonitor)

### How to use this image

##### Save image changes to local image files (volume mounted)
```console
$ docker run -d -e CAMERA_RTSP_URL=rtsp://test:test@192.168.1.10/live -e CAMERA_THUMBNAIL_DIR=/images/thumb -e CAMERA_NATIVE_DIR=/images/native -v /mnt/data/:/images dsmithson/rtspCameraMonitor
```

##### Publish image changes to RabbitMQ
```console
$ docker run -d -e CAMERA_RTSP_URL=rtsp://test:test@192.168.1.10/live -e RABBITMQ_HOST=myrabbit.local -e RABBITMQ_USER=user -e RABBITMQ_PASS=pass -e RABBITMQ_EXCHANGE=my.exchange -e RABBITMQ_ROUTING_KEY=actions.write dsmithson/rtspCameraMonitor
```

Environment Variables
- RABBITMQ_HOST: [Optional] hostname of machine hosting RabbitMQ
- RABBITMQ_USER: [Optional] username for connecting to RabbitMQ
- RABBITMQ_PASS: [Optional] password for connecting to RabbitMQ
- RABBITMQ_EXCHANGE: [Optional] Exchange to publish messages to in RabbitMQ
- RABBITMQ_ROUTING_KEY: [Optional] Routing key to publish messages with in RabbitMQ
- CAMERA_NAME: Friendly name for camera.  Included in logs and RabbitMQ published messages
- CAMERA_RTSP_URL: Takes form = rtsp://<user>:<pass>@<cameraIP>
- CAPTURE_INTERVAL_SECONDS: [Optional] Sets interval between image captures.  Defaults to 300 seconds
- CAMERA_THUMBNAIL_DIR: [Optional] If specified, specifies a path to save thumbnail images of changes
- CAMERA_NATIVE_DIR: [Optional] If specified, specifies a path to save native images of changes
