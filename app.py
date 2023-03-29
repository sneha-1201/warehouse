from flask import Flask,render_template,request
import os
import json
from datetime import date
import pandas as pd
import numpy as np


app=Flask(__name__,template_folder='templates')



@app.route('/sign_s3/')
def sign_s3():
  S3_BUCKET = os.environ.get('mubucketwarehouse')

  file_name = request.args.get('file_name')
  file_type = request.args.get('file_type')

  s3 = boto3.client('s3')

  presigned_post = s3.generate_presigned_post(
    Bucket = S3_BUCKET,
    Key = file_name,
    Fields = {"acl": "public-read", "Content-Type": file_type},
    Conditions = [
      {"acl": "public-read"},
      {"Content-Type": file_type}
    ],
    ExpiresIn = 3600
  )

  return json.dumps({
    'data': presigned_post,
    'url': 'https://etb7rnpuvd.execute-api.ap-south-1.amazonaws.com/v1' % ('custom-labels-console-ap-south-1-2e4c496f45','shinchan.jpeg')
  })

if __name__ == "__main__":
    app.run(debug=True)

























