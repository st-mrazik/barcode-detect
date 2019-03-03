import argparse
import logging
import sys
import time

import cv2
import imutils.video

from pyzbar import pyzbar

parser = argparse.ArgumentParser(description='Detects barcodes and QR codes.')
parser.add_argument("--image", type=str, metavar="PATH",
                    help='Path to source image file')
parser.add_argument("-o", "--output", type=str, metavar="PATH",
                    help="Output path to file")
parser.add_argument("-c", "--use-camera", action="store_true",
                    help="Use camera input")
parser.add_argument("--use-pi-camera", action="store_true",
                    help="Set raspbery pi camera option")

args = parser.parse_args()

root = logging.getLogger()
root.setLevel(logging.INFO)

handler = logging.StreamHandler(sys.stdout)
handler.setLevel(logging.INFO)
formatter = logging.Formatter('%(levelname)s - %(message)s')
handler.setFormatter(formatter)
root.addHandler(handler)

# detect on image
if args.image:
    logging.info("Reading image: {path}".format(path=args.image))
    image = cv2.imread(args.image)
    barcodes = pyzbar.decode(image)

    for barcode in barcodes:
        (x, y, w, h) = barcode.rect
        cv2.rectangle(image, (x, y), (x + w, y + h), (0, 0, 255), 2)
 
        # the barcode data is a bytes object so if we want to draw it on
        # our output image we need to convert it to a string first
        barcodeData = barcode.data.decode("utf-8")
        barcodeType = barcode.type

        # draw the barcode data and barcode type on the image
        text = "{} ({})".format(barcodeData, barcodeType)
        cv2.putText(image, text, (x, y - 10), cv2.FONT_HERSHEY_SIMPLEX,
            0.5, (0, 0, 255), 2)
 
        logging.info("Found {type_} barcode: {data}".format(type_=barcodeType, data=barcodeData))

    if args.output:
        logging.info("Wrtiting output to: {path}".format(path=args.output))
        cv2.imwrite(args.output, image)
    else:
        logging.info("Display image")
        cv2.imshow("Image", image)
        cv2.waitKey(0)

elif args.use_camera:
    logging.info("Capturing stream from camera...")
    if args.use_pi_camera:
        vs = imutils.video.VideoStream(usePiCamera=True).start()
    else:
        vs = imutils.video.VideoStream().start()
    time.sleep(2)
    while True:
        # grab the frame from the threaded video stream and resize it to
        # have a maximum width of 400 pixels
        frame = vs.read()
        frame = imutils.resize(frame, width=400)
        
        # find the barcodes in the frame and decode each of the barcodes
        barcodes = pyzbar.decode(frame)

        for barcode in barcodes:
            (x, y, w, h) = barcode.rect
            cv2.rectangle(frame, (x, y), (x + w, y + h), (0, 0, 255), 2)
     
            # the barcode data is a bytes object so if we want to draw it on
            # our output image we need to convert it to a string first
            barcodeData = barcode.data.decode("utf-8")
            barcodeType = barcode.type

            # draw the barcode data and barcode type on the image
            text = "{} ({})".format(barcodeData, barcodeType)
            cv2.putText(frame, text, (x, y - 10), cv2.FONT_HERSHEY_SIMPLEX,
                0.5, (0, 0, 255), 2)
     
            logging.debug("Found {type_} barcode: {data}".format(type_=barcodeType, data=barcodeData))

        cv2.imshow('frame',frame)
        if cv2.waitKey(1) & 0xFF == ord('q'):
            break
