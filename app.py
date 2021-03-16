import streamlit as st
# To make things easier later, we're also importing numpy and pandas for
# working with sample data.
import numpy as np
import pandas as pd
#import urllib.parse
#import urllib.request
from urllib.request import urlopen
import requests
import json
import re
from PIL import Image, ImageFont, ImageDraw 

tag_url = 'http://gpt-gen:8000/api'
moat_url = 'http://moat-search:8000/api'
unsplash_url = 'http://unsplash-search:8000/api'

prefix = "./moat-images/moat_full_imgs/"
postfix = ".png"

# return a list of taglines

def Sorting(list): 
    list.sort(key=len) 
    return list

@st.cache
def load_gpt3_taglines (product, desc):

   object = {'prompt': product + " - " + desc, 'num': 4}
   res = requests.post(tag_url, json=object)
   data = res.json()

   nl = lambda x: x.replace('\n', '') 
   sl = lambda x: x.replace('Slogan:', '') 
   
   # clean the GPT-3 output
   list1 = [nl(tagline) for tagline in data]              # remove /n     
   list2 = [sl(tagline) for tagline in list1]             # remove leftover words    
   list3 = [re.sub(r'^ *- *', '', i) for i in list2 if i] # remove empty strings, dashes
   return Sorting(list3)                                  # prefer shorter lines

@st.cache
def load_moat_images (tagline, num=3):
   
   object = {'prompt': [tagline], 'num': num}
   res = requests.post(moat_url, json=object)
   data = res.json() 
   return(data)

@st.cache
def load_unsplash_images (tagline, moat_selected=[], num=3):
   
   object = {'prompt': [tagline], 'moat_selected': moat_selected, 'num': num}
   res = requests.post(unsplash_url, json=object)
   data = res.json() 
   return(data)

# Main Program

st.title('CS329S commercial ad generator')

product_template = ("Bad Brothers Coffee")
product_input = st.text_input("Enter product name", product_template)

desc_template = "Coffee sustainably grown in Costa Rica and roasted in our barn in Seattle"
desc_input = st.text_area("Enter product description", desc_template) 


if (product_input != product_template and desc_input != desc_template):

   # generate and select tagline
   waiting = st.text("Loading taglines...")
   data = load_gpt3_taglines(product_input, desc_input) 
   waiting.text("GPT-3 taglines ready:")
   tagline_candidate = st.radio("Choose a tagline to find matching images:", data)
  
   tagline = st.text_input("Edit the tagline: ", tagline_candidate)

   # display moat images
   moat_image_indices = load_moat_images(tagline, 4)    
   image_filenames = [ prefix+index+postfix for index in moat_image_indices]
   commercial = st.text("Loading commercial images similar to tagline...")
   moat_images = [ Image.open(filename).convert('RGB') for filename in image_filenames ] 
   moat_captions = moat_image_indices
   for index, image in enumerate(moat_images):
      st.image(image, caption=moat_captions[index])
   commercial.text("CLIP semantic search results for commercial images:")

   # select moat images to search unsplash
   moat_selected = st.multiselect("Choose commercial images to find similar examples", moat_captions)

   # download unsplash material
   templates = st.text("Searching Unsplash for royalty-free images...")
   unsplash_ids = load_unsplash_images(tagline, moat_selected, 4)   
   unsplash_image_urls = [ f"https://unsplash.com/photos/{photo_id}/download?w=640" for photo_id in unsplash_ids]
   unsplash_images = [Image.open(urlopen(url)) for url in unsplash_image_urls]

   # convert images to editable format
   editable_images = [ ImageDraw.Draw(my_image) for my_image in unsplash_images]

   # for every image collect parameters and render
   # note caching will not work well here

   for index, image in enumerate(editable_images):

      # order: color, size, x, y
      col1, col2, col3, col4 = st.beta_columns(4)
      width, height = unsplash_images[index].size
      with col1:
         color = st.text_input("Color: web name or #RRGGBB", "white", key=str(index))
      with col2:
         font_size = st.slider("Font size:", min_value=10, max_value=100, value=20,key=str(index))
      with col3:
         x = st.slider("X coordinate:", min_value=0, max_value=width, value=15,key=str(index))
      with col4:
         y = st.slider("Y coordinate:", min_value=0, max_value=height, value=15,key=str(index))
      # render
      tag_font = ImageFont.truetype('fonts/Roboto-Light.ttf', font_size)
      image.text((x,y), tagline, fill=color, font=tag_font) 
      st.image(unsplash_images[index])
   
   # all done
   templates.text("Loaded Unsplash images.")
