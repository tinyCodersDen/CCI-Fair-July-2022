import os
from flask import Flask, render_template, request, flash, redirect, Response
import cv2
from werkzeug.utils import secure_filename
import time
from PIL import Image
import numpy as np
import tensorflow as tf
import tensorflow_hub as hub
app = Flask(__name__)

camera = cv2.VideoCapture(0)
images = []
camera_pics = []
snap = False
c = 0
os.environ["TFHUB_DOWNLOAD_PROGRESS"] = "True"
ALLOWED_EXTENSIONS = {'png', 'jpg', 'jpeg', 'svg'}
SAVED_MODEL_PATH = "https://tfhub.dev/captain-pool/esrgan-tf2/1"
app.config['UPLOAD_FOLDER'] = 'static/images'

def preprocess_image(image_path):
  """ Loads image from path and preprocesses to make it model ready
      Args:
        image_path: Path to the image file
  """
  hr_image = tf.image.decode_image(tf.io.read_file(image_path))
  # If PNG, remove the alpha channel. The model only supports
  # images with 3 color channels.
  if hr_image.shape[-1] == 4:
    hr_image = hr_image[...,:-1]
  hr_size = (tf.convert_to_tensor(hr_image.shape[:-1]) // 4) * 4
  hr_image = tf.image.crop_to_bounding_box(hr_image, 0, 0, hr_size[0], hr_size[1])
  hr_image = tf.cast(hr_image, tf.float32)
  return tf.expand_dims(hr_image, 0)

def save_image(image, filename):
  """
    Saves unscaled Tensor Images.
    Args:
      image: 3D image tensor. [height, width, channels]
      filename: Name of the file to save.
  """
  if not isinstance(image, Image.Image):
    image = tf.clip_by_value(image, 0, 255)
    image = Image.fromarray(tf.cast(image, tf.uint8).numpy())
  image.save("static/images/%s" % filename)
  print("Saved as %s.jpg" % filename)
def superes(path,file):
  IMAGE_PATH = path
  print(IMAGE_PATH)
  hr_image = preprocess_image(IMAGE_PATH)
  # Plotting Original Resolution image
  # save_image(tf.squeeze(hr_image), filename="Original Image")
  model = hub.load(SAVED_MODEL_PATH)
  start = time.time()
  print('model loaded')
  fake_image = model(hr_image)
  fake_image = tf.squeeze(fake_image)
  print("Time Taken: %f" % (time.time() - start))
  save_image(tf.squeeze(fake_image), filename='superes_'+file)
  camera_pics.append([path,"static/images/superes_"+file])
  images.append([path,"static/images/superes_"+file])
  print(camera_pics)
def gen_frames():  # generate frame by frame from camera
    global snap
    global c
    while True:
        # Capture frame-by-frame
        success, frame = camera.read()  # read the camera frame
        # if snap==True:
        #   snap = False
        #   cv2.imwrite('static/images/camera'+c+'.png',frame)
        #   c+=1
        if not success:
            break
        else:
            if snap==True:
              snap = False
              cv2.imwrite('static/images/camera'+str(c)+'.png',frame)
              superes(str('static/images/camera'+str(c)+'.png'),str('camera'+str(c)+'.png'))
              c+=1
            ret, buffer = cv2.imencode('.jpg', frame)
            frame = buffer.tobytes()
            yield (b'--frame\r\n'
                   b'Content-Type: image/jpeg\r\n\r\n' + frame + b'\r\n')

def allowed_file(filename):
    return '.' in filename and \
           filename.rsplit('.', 1)[1].lower() in ALLOWED_EXTENSIONS
@app.route('/')
def upload_file():
   global images
   return render_template('home.html',images=images)
@app.route('/video_feed')
def video_feed():
    #Video streaming route. Put this in the src attribute of an img tag
    return Response(gen_frames(), mimetype='multipart/x-mixed-replace; boundary=frame')
@app.route('/snap',methods=['GET','POST'])
def snap():
  global camera_pics
  global images
  global snap
  if request.method=='POST':
    snap = True
  print(camera_pics)
  return render_template('camera.html',camera_pics=images)
@app.route('/uploader', methods = ['GET', 'POST'])
def uploader_file():
   if request.method == 'POST':
      f = request.files['file']
      if f.filename == '':
        return redirect('/')
      if allowed_file(f.filename):
        f.save(os.path.join(app.config['UPLOAD_FOLDER'],secure_filename(f.filename)))
        IMAGE_PATH = "static/images/"+f.filename
        print(IMAGE_PATH)
        hr_image = preprocess_image(IMAGE_PATH)
        # Plotting Original Resolution image
        # save_image(tf.squeeze(hr_image), filename="Original Image")
        model = hub.load(SAVED_MODEL_PATH)
        start = time.time()
        print('model loaded')
        fake_image = model(hr_image)
        fake_image = tf.squeeze(fake_image)
        print("Time Taken: %f" % (time.time() - start))
        save_image(tf.squeeze(fake_image), filename='superes_'+f.filename)
        images.append(["static/images/"+f.filename,"static/images/superes_"+f.filename])
        print(images)
        redirect('/')
        # flash('file uploaded successfully')
      else:
        return redirect('/')
        # flash('Invalid type. You must upload a png, jpg, jpeg, or an svg file.')
      return redirect('/')
if __name__ == '__main__':
   app.run(debug = True)