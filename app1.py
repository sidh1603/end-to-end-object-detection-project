import sys
import os
from flask import Flask, request, jsonify, render_template, Response
from flask_cors import CORS, cross_origin
from signLanguage.pipeline.training_pipeline import TrainPipeline
from signLanguage.exception import SignException
from signLanguage.utils.main_utils import decodeImage, encodeImageIntoBase64
import cv2
from PIL import Image
import numpy as np

app = Flask(__name__)
CORS(app)

class ClientApp:
    def __init__(self):
        self.filename = "inputImage.jpg"

@app.route("/")
def home():
    return render_template("index.html")

@app.route("/train")
def trainRoute():
    obj = TrainPipeline()
    obj.run_pipeline()
    return "Training Successful!!"

def detect_objects(frame):
    # Load YOLOv5 model
    net = cv2.dnn.readNet("yolov5/sid_model.pt", "yolov5s.yaml")

    # Get model output layer names
    layer_names = net.getLayerNames()
    output_layers = [layer_names[i[0] - 1] for i in net.getUnconnectedOutLayers()]

    # Prepare the frame for object detection
    blob = cv2.dnn.blobFromImage(frame, 0.00392, (416, 416), (0, 0, 0), True, crop=False)
    net.setInput(blob)
    outs = net.forward(output_layers)

    # Initialize variables for counting objects
    class_ids = []
    confidences = []
    boxes = []
    detected_objects = {}

    # Process outputs
    for out in outs:
        for detection in out:
            scores = detection[5:]
            class_id = np.argmax(scores)
            confidence = scores[class_id]
            if confidence > 0.5:
                # Object detected
                detected_objects[class_id] = detected_objects.get(class_id, 0) + 1

    return detected_objects

@app.route("/predict", methods=['POST','GET'])
@cross_origin()
def predictRoute():
    try:
        image = request.json['image']
        decodeImage(image, clApp.filename)

        # Capture frame from webcam
        cap = cv2.VideoCapture(0)
        ret, frame = cap.read()

        # Detect objects in the frame
        detected_objects = detect_objects(frame)

        # Display object counts on the frame
        for class_id, count in detected_objects.items():
            cv2.putText(frame, f"Class {class_id}: {count}", (50, 50), cv2.FONT_HERSHEY_SIMPLEX, 1, (0, 255, 0), 2)

        # Encode the resulting image
        _, buffer = cv2.imencode('.jpg', frame)
        frame_as_text = buffer.tobytes()
        opencodedbase64 = encodeImageIntoBase64(frame_as_text)

        # Clean up
        cap.release()
        cv2.destroyAllWindows()

        result = {"image": opencodedbase64.decode('utf-8')}
        return jsonify(result)

    except ValueError as val:
        print(val)
        return Response("Value not found inside  json data")
    except KeyError:
        return Response("Key value error incorrect key passed")
    except Exception as e:
        print(e)
        result = "Invalid input"
        return jsonify(result)

if __name__ == "__main__":
    clApp = ClientApp()
    app.run(host="0.0.0.0", port=8080)
