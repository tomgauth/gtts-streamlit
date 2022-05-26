from sre_parse import SPECIAL_CHARS
import streamlit as st
from gtts import gTTS
from googletrans import Translator
import os
import cv2
import csv
import pandas as pd
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
import time
VIDEO_FORMAT = [1920,1080]
SLIDE_DURATION = '00:00:10.00' # duration of a slide in seconds
FONT_SIZE = 100
FONT = 'ARIBL0.ttf'
SPECIAL_CHARS = "!#/.?:$%^&*()"
COLOR_TXT_FR = (52, 229, 235)
COLOR_TXT_EN = (235, 52, 52)



translator = Translator()

st.write("""Write French phrases and words you want to learn below. One per line
If you want to add a custom translation to English, add it on the same line after the French phrase, separated by ';' or by a tab """)
phrases = st.text_area(label="Enter French phrases or words you want to learn", value="", height=None, max_chars=None, key=None, help=None, on_change=None, args=None, kwargs=None, placeholder=None, disabled=False)

phrases = phrases.splitlines()

uploaded_file = st.file_uploader("Choose a file")
if uploaded_file is not None:

    dataframe = pd.read_csv(uploaded_file)
    st.write(dataframe)
    phrases = dataframe.to_dict('records')


def clean_string(txt):
    specialChars = SPECIAL_CHARS 
    for specialChar in specialChars:
        txt = txt.replace(specialChar, '_')
    return txt



def get_image(key_word):
    key_word = clean_string(key_word)
    url = f"https://source.unsplash.com/random/{VIDEO_FORMAT[0]}x{VIDEO_FORMAT[1]}/?{key_word}"
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
            # img2.putalpha(127)
            # img.paste(img2, img)
        # print(img)

        new = Image.new(mode="RGB", size=tuple(VIDEO_FORMAT), color=(255, 255, 255))
        print(new)
        img2 = img.copy()
        mask = Image.new("L", img2.size, 128)
        print(mask)
        final = Image.composite(new, img2, mask)
        print(final)
        # print(img2)

        final.save(filename)
        return filename
    else:
        print('Image Couldn\'t be retreived')    


def get_audio(d):
    if 'audio_fr' in d:
        doc = requests.get(d['audio_fr'])        
        formatted = clean_string(d['fr']) + ".mp3"
        with open(f"audio/{formatted}", 'wb') as f:
            f.write(doc.content)
    else:
        myobj = gTTS(text=d['fr'], lang="fr", slow=False)
        formatted = clean_string(d['fr']) + ".mp3"
        myobj.save(f"audio/{formatted}")    
    # audio_file = open(f'{phrases}.ogg', 'rb')
    audios_to_merge = AudioSegment.silent(duration=0)   
    audio = AudioSegment.from_file(f"audio/{formatted}")

    milisec_duration = audio.duration_seconds*1000
    buffer_duration = 10000 - milisec_duration
    # st.write(f"buffer duration: {buffer_duration}")
    buffer = AudioSegment.silent(duration=buffer_duration)
    audios_to_merge += audio + buffer

    audios_to_merge.export(f"audio/{formatted}", format="mp3")
    # st.write(f"audio/{formatted}")
    # st.audio(f"audio/{formatted}")
    return f"audio/{formatted}"

def write_image(d):
    # Open an Image
    # st.write(d['img'])
    img = Image.open(d['img'])
    print(img)
    # Call draw Method to add 2D graphics in an image
    I1 = ImageDraw.Draw(img) 
    fontsize = FONT_SIZE
    def_padding = FONT_SIZE
    myFont = ImageFont.truetype(FONT, fontsize)    

    while (myFont.getsize(d['fr'])[0]+def_padding >= img.size[0]) or (myFont.getsize(d['en'])[0]+def_padding >= img.size[0]):
        fontsize -= 2
        myFont = ImageFont.truetype(FONT, int(fontsize))

    myFont = ImageFont.truetype(FONT, fontsize)    
    I1.text((fontsize, fontsize), d['fr'], font=myFont, fill=COLOR_TXT_FR)    
    I1.text((fontsize, fontsize*3), d['en'], font=myFont, fill=COLOR_TXT_EN)    
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

    name = clean_string(d['en'])

    out = cv2.VideoWriter(f"video/{name}.mp4",cv2.VideoWriter_fourcc('m', 'p', '4', 'v'), 0.10, tuple(VIDEO_FORMAT))
    
    for i in range(len(img_array)):
        out.write(img_array[i])
    out.release()
    try:
        video_clip = VideoFileClip(f"video/{name}.mp4")
        video_clip.set_duration(SLIDE_DURATION)
        st.write(f"video duration: {video_clip.duration}")
        # load the audio
        audio_clip = AudioFileClip(f"{item['audio_fr']}")
        audio_clip.set_duration(SLIDE_DURATION)
        st.write(f"audio duration: {audio_clip.duration}")
        # end = audio_clip.end
        # audio_clip = audio_clip.subclip(0.0, end)
        final_clip = video_clip.set_audio(audio_clip)
        final_clip.write_videofile(f"video/{name}.mp4")
    except Exception as e:
        st.write(e)

    # st.video(f"video/{name}.mp4")
    return f"video/{name}.mp4"

def translate_phrases(phrases):
    items = []          
    my_bar = st.progress(0) 
    len_phrases = len(phrases)
    for phrase in phrases:
        dir_path = 'video'
        if type(phrase) == dict:
            d = phrase
        else:
            d = {}        
            if "\t" in phrase:
                ph = phrase.split('\t')
                d['fr'] = ph[0]
                d['en'] = ph[1]
            elif ";" in phrase:
                ph = phrase.split(";")
                d['fr'] = ph[0]
                d['en'] = ph[1]
            else:
                d['fr'] = phrase
                d['en'] = translator.translate(phrase, src="fr", dest='en').text        
        try:
            d['img'] = get_image(d['en'])
        except:
            st.write(f"an error creating the image for {d}")
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
        num_videos = len([entry for entry in os.listdir(dir_path) if os.path.isfile(os.path.join(dir_path, entry))])             
        my_bar.progress(num_videos/len_phrases)           
    
    return items        
        

def generate_final_video(items):
    clips = [VideoFileClip(item['video']) for item in items]
    clips = [clip.set_duration("00:00:10.00") for clip in clips]
    
    try:
        final = concatenate_videoclips(clips, method='compose')
        final.write_videofile("final.mp4")        
        return "final.mp4"
    except:
        pass

def clean_up_media():
    dirs = ['audio','images','video']
    for dir in dirs :
        for f in os.listdir(dir):
            os.remove(os.path.join(dir, f))

def show_video(video_name):
    video_file = open(video_name, 'rb')
    video_bytes = video_file.read()
    st.video(video_bytes, format="video/mp4")

def main():
    items = translate_phrases(phrases) 
    final_video = generate_final_video(items)
    clean_up_media()
    show_video(final_video)
    st.write(items) 

main()




