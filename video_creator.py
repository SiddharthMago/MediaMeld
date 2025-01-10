from moviepy.editor import *
from imageio import imread
from pydub import AudioSegment

import os
import base64
import cv2
import io
import numpy as np

import matplotlib.pyplot as plt


DEFAULT_IMAGE_LENGTH = 3
DEFAULT_SIZE = (1080, 1920)
DEFAULT_FPS = 24
TEMP_PATH = f'{os.getcwd()}/static/Resources/temp'

def convert_base64_to_mp3(audio_data, user_email):
    audio_encoded = audio_data.encode()
    audio_content = base64.b64decode(audio_encoded)

    audio = AudioSegment.from_file(io.BytesIO(audio_content), format="mp3")
    audio.export(f'{TEMP_PATH}/{user_email}.mp3', format="mp3")


def resize_with_padding(image, shape_out, DO_PADDING=True, TINY_FLOAT=1e-5):
    """
    Resizes an image to the specified size,
    adding padding to preserve the aspect ratio.
    """
    if image.ndim == 3 and len(shape_out) == 2:
        shape_out = [*shape_out, 3]
    hw_out, hw_image = [np.array(x[:2]) for x in (shape_out, image.shape)]
    resize_ratio = np.min(hw_out / hw_image)
    hw_wk = (hw_image * resize_ratio + TINY_FLOAT).astype(int)

    # Resize the image
    resized_image = cv2.resize(
        image, tuple(hw_wk[::-1]), interpolation=cv2.INTER_NEAREST
    )
    if not DO_PADDING or np.all(hw_out == hw_wk):
        return resized_image

    # Create a black image with the target size
    padded_image = np.zeros(shape_out, dtype=np.uint8)
    
    # Calculate the number of rows/columns to add as padding
    dh, dw = (hw_out - hw_wk) // 2
    # Add the resized image to the padded image, with padding on the left and right sides
    padded_image[dh : hw_wk[0] + dh, dw : hw_wk[1] + dw] = resized_image

    return padded_image


def convert_base64_to_cv(image_data):
    img = imread(io.BytesIO(base64.b64decode(image_data)))
    cv2_img = cv2.cvtColor(cv2.cvtColor(img, cv2.COLOR_RGB2BGR), cv2.COLOR_BGR2RGB)

    return resize_with_padding(cv2_img, DEFAULT_SIZE)


def create_video(image_list, audio = None, user_email = ""):
    if audio:
        convert_base64_to_mp3(audio, user_email)

    cv_images = [convert_base64_to_cv(image) for image in image_list]
    
    # Create a video from the images
    clips = [ImageClip(img).set_duration(DEFAULT_IMAGE_LENGTH) for img in cv_images]
    print(clips)
    video = concatenate_videoclips(clips, method="compose")

    # If audio is provided, set it as the audio of the clip
    if audio:
        temp = AudioFileClip(f'{TEMP_PATH}/{user_email}.mp3').set_duration(video.duration)
        audio_clip = CompositeAudioClip([temp]) 
        video = video.set_audio(audio_clip)

    # Write the result to a file
    video.write_videofile(f'{TEMP_PATH}/{user_email}.mp4', codec='libx264', fps=DEFAULT_FPS)

    return f'{TEMP_PATH}/output.mp4'


    
