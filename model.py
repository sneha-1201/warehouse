from fastapi import FastAPI, File, UploadFile
from fastapi.encoders import jsonable_encoder
from fastapi.middleware.cors import CORSMiddleware
import uvicorn
import numpy as np
from io import BytesIO
from PIL import Image
import io
import os
import boto3
import PIL
from PIL import Image, ImageDraw, ExifTags, ImageColor, ImageFont

# Configure with AWS using access key
os.environ['AWS_ACCESS_KEY_ID'] = 'AKIA2QMGQOEA33IL7ESN'
os.environ['AWS_SECRET_ACCESS_KEY'] = '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'
print('Configuration Successful')

# define bucket,photo,model and min_confidance
bucket='custom-labels-console-ap-south-1-2e4c496f45'
photo='trk.jpg'
model='arn:aws:rekognition:ap-south-1:722373472513:project/Truck_ANPR_1/version/Truck_ANPR_1.2023-02-10T19.53.03/1676038984170'
min_confidence=5
print('Done!')

client = boto3.client('rekognition',region_name='ap-south-1') # Connecting with model
# response = client.detect_custom_labels(Image={'S3Object': {'Bucket': bucket, 'Name': photo}},
#         MinConfidence=min_confidence,
#         ProjectVersionArn=model) # using detect_custom_label method to run inference on wild data

def read_file_as_image(data) -> np.ndarray:
    img = np.array(Image.open(BytesIO(data)))
    return img

# start the model

def start_model(project_arn, model_arn, version_name, min_inference_units):
    client = boto3.client('rekognition', region_name='ap-south-1')

    try:
        # Start the model
        print('Starting model: ' + model_arn)
        response = client.start_project_version(ProjectVersionArn=model_arn, MinInferenceUnits=min_inference_units)
        # Wait for the model to be in the running state
        project_version_running_waiter = client.get_waiter('project_version_running')
        project_version_running_waiter.wait(ProjectArn=project_arn, VersionNames=[version_name])

        # Get the running status
        describe_response = client.describe_project_versions(ProjectArn=project_arn,
                                                             VersionNames=[version_name])
        for model in describe_response['ProjectVersionDescriptions']:
            print("Status: " + model['Status'])
            print("Message: " + model['StatusMessage'])
    except Exception as e:
        print(e)

    print('Done...')


def main():
    project_arn = 'arn:aws:rekognition:ap-south-1:722373472513:project/Truck_ANPR_1/1675947482860'
    model_arn = 'arn:aws:rekognition:ap-south-1:722373472513:project/Truck_ANPR_1/version/Truck_ANPR_1.2023-02-10T19.53.03/1676038984170'
    min_inference_units = 1
    version_name = 'Truck_ANPR_1.2023-02-10T19.53.03'
    start_model(project_arn, model_arn, version_name, min_inference_units)


if __name__ == "__main__":
    main()




print('done')


app = FastAPI()

# origins = [
#     "http://localhost",
#     "http://localhost:3000",
# ]
# app.add_middleware(
#     CORSMiddleware,
#     allow_origins=origins,
#     allow_credentials=True,
#     allow_methods=["*"],
#     allow_headers=["*"],
# )

# Setting up s3 connection
s3_connection = boto3.resource('s3')

s3_object = s3_connection.Object(bucket,photo)
s3_response = s3_object.get()
s3_response['Body']

stream = io.BytesIO(s3_response['Body'].read())

# img=Image.open(stream)

@app.get("/ping")
async def ping():
    return "Hello, I am alive"


@app.post("/predict")
async def predict():
#     file: UploadFile = File(...)
# ):
#     image =await file.read()

    response = client.detect_custom_labels(Image={'S3Object': {'Bucket': bucket, 'Name': photo}},
                                           MinConfidence=min_confidence,
                                           ProjectVersionArn=model)  # using detect_custom_label method to run inference on wild data

    # response = client.detect_custom_labels(Image={'Bytes': stream},
    #                                        MinConfidence=min_confidence,
    #                                        ProjectVersionArn=model)

    # return jsonable_encoder({'result': response['CustomLabels']})

    # img = Image.open(io.BytesIO(stream))
    img=Image.open(stream)

    labels = response["CustomLabels"]

    for label in labels:
        box = label["Geometry"]["BoundingBox"]
        xmin = box["Left"] * img.size[0]
        ymin = box["Top"] * img.size[1]
        xmax = xmin + (box["Width"] * img.size[0])
        ymax = ymin + (box["Height"] * img.size[1])




    cropped_image = img.crop((xmin, ymin, xmax, ymax))  # used the bounding box parameters obtained from response

    cropped_image_bytes = io.BytesIO()
    cropped_image.save(cropped_image_bytes, format="JPEG")
    cropped_image_bytes = cropped_image_bytes.getvalue()

    detect_text = client.detect_text(Image={"Bytes": cropped_image_bytes})

    detected_text = detect_text["TextDetections"]

    output = jsonable_encoder({'result':detected_text[0:2]})
    string = ""
    for diction in output['result']:
        string += diction['DetectedText']

    return string


if __name__ == "__main__":
    uvicorn.run(app, host='localhost', port=8000)

