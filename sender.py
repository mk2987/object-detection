"""
Sender reads image from a camera and pushes them to a server
"""

import cv2
import zmq
import base64
import argparse

def dbgPrint(msg):
    global dbg
    if dbg:
        print(msg)

def parseArgs():
    parser = argparse.ArgumentParser(description="Send camera images to server")

    parser.add_argument('-s', '--server-addr', required = True,
                        dest = 'serverAddr',
                        help = 'server address')

    parser.add_argument('-i', '--identity', required = True,
                        help = 'sender\'s identity')

    parser.add_argument('-r', '--resolution', type = int,
                        default = (640, 480),
                        nargs = 2, metavar = ('hres', 'vres'),
                        help = 'resolution for sending video')

    parser.add_argument('-f', '--flip', action = 'store_true',
                        help = 'flip image; useful for debugging')

    parser.add_argument('-v', '--verbose', action = 'store_true',
                        help = 'verbose message logs')

    args = parser.parse_args()
    return args

def setupComms(serverAddr):
    context = zmq.Context()

    # Create a zmq socket to push images
    socket = context.socket(zmq.PUSH)

    # Connect to server
    socket.connect("tcp://" + serverAddr)

    return socket

def setupCamera():
    # Connect to the first available webcam
    for i in range(5):
        cap = cv2.VideoCapture(i)
        if cap.isOpened():
            break
        if i == 4:
            raise OSError("Could not find any camera device")
    
    return cap

def sendBuffers(cam, socket, senderName, args):
    while True:
        ret, frame = cam.read()

        frame = cv2.resize(frame, tuple(args.resolution))
        if args.flip:
            frame = cv2.flip(frame, 1)

        encoded, buf = cv2.imencode('.jpg', frame)

        #buf = base63.b64encode(buf)

        # Send sender's name and frame as a multipart message
        socket.send_multipart([senderName, buf])

def cleanup(cam):
    cam.release()
    cv2.destroyAllWindows()

if __name__ == "__main__":
    global dbg

    args = parseArgs()
    dbg = args.verbose

    try:
        senderName = args.identity.encode('ascii')

        socket = setupComms(args.serverAddr)

        cam = setupCamera()

        dbgPrint("Sending video from {} to {} at resolution {}". \
                 format(args.identity, args.serverAddr, tuple(args.resolution)))

        sendBuffers(cam, socket, senderName, args)
    finally:
        cleanup(cam)
