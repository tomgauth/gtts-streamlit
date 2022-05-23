import streamlit as st
from gtts import gTTS
from googletrans import Translator
import os
import cv2
import numpy as np
import requests # to get image from the web
import shutil # to save it locally
# Importing the PIL library
from PIL import Image
from PIL import ImageDraw
from PIL import ImageFont
import glob
from pydub import AudioSegment
from moviepy.editor import VideoFileClip, AudioFileClip, CompositeAudioClip, concatenate_videoclips

translator = Translator()

st.write("""Write French phrases and words you want to learn below. One per line
If you want to add a custom translation to English, add it on the same line after the French phrase, separated by ';' """)
phrases = st.text_area(label="Enter French phrases or words you want to learn", value="", height=None, max_chars=None, key=None, help=None, on_change=None, args=None, kwargs=None, placeholder=None, disabled=False)

phrases = phrases.splitlines()

def get_image(key_word):
    url = f"https://source.unsplash.com/random/500x500/?{key_word}"
    filename = 'images/' + url.split("/")[-1][1:] + ".png"

    # Open the url image, set stream to True, this will return the stream content.
    r = requests.get(url, stream = True)

    # Check if the image was retrieved successfully
    if r.status_code == 200:
        # Set decode_content value to True, otherwise the downloaded image file's size will be zero.
        r.raw.decode_content = True
        
        # Open a local file with wb ( write binary ) permission.
        with open(filename,'wb') as f:
            shutil.copyfileobj(r.raw, f)
            
        print('Image sucessfully Downloaded: ',filename)    
        img = Image.open(filename)
        img.putalpha(127)
        img.save(filename)    
        return filename
    else:
        print('Image Couldn\'t be retreived')    

def get_audio(d):
    myobj = gTTS(text=d['fr'], lang="fr", slow=False)
    formatted = d['fr'].replace(" ", "_") + ".mp3"
    myobj.save(formatted)    
    # audio_file = open(f'{phrases}.ogg', 'rb')
    audios_to_merge = AudioSegment.silent(duration=0)   
    audio = AudioSegment.from_file(formatted)

    milisec_duration = audio.duration_seconds*1000
    buffer_duration = 5000 - milisec_duration
    st.write(f"buffer duration: {buffer_duration}")
    buffer = AudioSegment.silent(duration=buffer_duration)
    audios_to_merge += audio + buffer

    audios_to_merge.export(formatted, format="mp3")
    st.write(formatted)
    st.audio(formatted)
    return formatted

def write_image(d):
    # Open an Image
    # st.write(d['img'])
    img = Image.open(d['img'])
    # st.write(img)
    # Call draw Method to add 2D graphics in an image
    I1 = ImageDraw.Draw(img) 
    fontsize = 50
    myFont = ImageFont.truetype('ARIBL0.ttf', fontsize)    
    st.write(myFont.getsize(d['fr'])[0])
    # Add Text to an image
    while (myFont.getsize(d['fr'])[0] > img.size[0]) and (myFont.getsize(d['en'])[0] > img.size[0]):
        fontsize -= 2
        # myFont = ImageFont.truetype('ARIBL0.ttf', fontsize)
        st.write(myFont.getsize(d['fr'])[0])

    myFont = ImageFont.truetype('ARIBL0.ttf', fontsize)
    I1.text((50, 50), d['fr'], font=myFont, fill=(0, 0, 102))    
    I1.text((50, 120), d['en'], font=myFont, fill=(0, 100, 102))    
    # Save the edited image
    img.save(d['img'])
    return d['img']    

def gen_video(d):
    img_array = []
    #for filename in glob.glob('images/*.png'):
    item = d
    filename = item['img']
    img = cv2.imread(filename)
    height, width, layers = img.shape
    size = (width,height)
    img_array.append(img)

    name = d['en'].replace(" ", "_")

    out = cv2.VideoWriter(f"{name}.mp4",cv2.VideoWriter_fourcc('m', 'p', '4', 'v'), 0.20, (500,500))
    
    for i in range(len(img_array)):
        out.write(img_array[i])
    out.release()
    try:
        video_clip = VideoFileClip(f"{name}.mp4")
        # load the audio
        audio_clip = AudioFileClip(item['audio_fr'])
        # end = audio_clip.end
        # audio_clip = audio_clip.subclip(0.0, end)
        final_clip = video_clip.set_audio(audio_clip)
        final_clip.write_videofile(f"{name}.mp4")
        st.write(final_clip)
    except Exception as e:
        st.write(e)

    st.video(f"{name}.mp4")
    return f"{name}.mp4"

def translate_phrases(phrases):
    items = []
    for phrase in phrases:        
        d = {}
        if ";" in phrase:
            ph = phrase.split(';')
            d['fr'] = ph[0]
            d['en'] = ph[1]
        else:
            d['fr'] = phrase
            d['en'] = translator.translate(phrase, dest='en').text
        try:
            d['img'] = get_image(d['en'])
        except:
            st.write(f"an error occured with {d}")
        try:
            d['audio_fr'] = get_audio(d)
        except:
            st.write(f"cannot generate audio for {d}")
        try:
            d['img_text'] = write_image(d)
        except:
            st.write(f"cannot write to image for {d}")
        try:
            d['video'] = gen_video(d)
        except:
            st.write(f"cannot generate video for {d}")
        items.append(d)
    
    return items        


def write_to_image(d):
    # Open an Image
    # st.write(d['img'])
    img = Image.open(d['img'])
    # st.write(img)
    # Call draw Method to add 2D graphics in an image
    I1 = ImageDraw.Draw(img) 
    fontsize = 50
    myFont = ImageFont.truetype('ARIBL0.ttf', fontsize)    
    st.write(myFont.getsize(d['fr'])[0])
    # Add Text to an image
    while (myFont.getsize(d['fr'])[0] > img.size[0]) and (myFont.getsize(d['en'])[0] > img.size[0]):
        fontsize = int(fontsize*0.8)
        myFont = ImageFont.truetype('ARIBL0.ttf', fontsize)
        st.write(myFont.getsize(d['fr'])[0])

    I1.text((50, 50), d['fr'], font=myFont, fill=(0, 0, 102))    
    I1.text((50, 120), d['en'], font=myFont, fill=(0, 100, 102))    
    # Save the edited image
    img.save(f"{d['img']}")
    st.write(d['img'])
    # st.image(f"{d['img']}")

# for phrase in translated_phrases:
#     write_to_image(phrase)

def generate_audio_track(items):
    audios_to_merge = AudioSegment.silent(duration=0) 

    for d in items:
        audio = AudioSegment.from_file(d['audio_fr'])

        milisec_duration = audio.duration_seconds*1000
        buffer_duration = 5000 - milisec_duration
        buffer = AudioSegment.silent(duration=buffer_duration)
        audios_to_merge += audio + buffer

    audios_to_merge.export("final.mp3", format="mp3")
    st.write(audios_to_merge)
    return "final.mp3"
        

def generate_video(items):
    img_array = []
    #for filename in glob.glob('images/*.png'):
    for item in items:
        filename = item['img']
        img = cv2.imread(filename)
        height, width, layers = img.shape
        size = (width,height)
        img_array.append(img)

    out = cv2.VideoWriter('final.mp4',cv2.VideoWriter_fourcc('m', 'p', '4', 'v'), 0.5, (500,500))
    
    for i in range(len(img_array)):
        out.write(img_array[i])
    out.release()

def generate_final_video(items):
    clips = [VideoFileClip(item['video']) for item in items]

    final = concatenate_videoclips(clips)
    final.write_videofile("final.mp4")
    return "final.mp4"

def main():
    items = translate_phrases(phrases)
    st.write(items)
    final_video = generate_final_video(items)
    # for d in items:
    #     write_to_image(d)
    # generate_audio_track(items)
    # generate_video(items)
    # # load the video
    # video_clip = VideoFileClip("final.mp4")
    # # load the audio
    # audio_clip = AudioFileClip("final.mp3")
    # end = audio_clip.end
    # audio_clip = audio_clip.subclip(0.0, end)
    # final_clip = video_clip.set_audio(audio_clip)
    # final_clip.write_videofile("final.mp4")

main()

video_file = open('final.mp4', 'rb')
video_bytes = video_file.read()
st.video(video_bytes, format="video/mp4")
# st.video(video_file)
with open("final.mp4", 'rb') as v:
    st.video(v)