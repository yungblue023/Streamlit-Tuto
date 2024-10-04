import json
import os
import re

import google.generativeai as genai
import openai
import PIL.Image
import requests
import streamlit as st


st.markdown("""<style>/*Set Background color*/.stApp {background-color: #787872 ;}</style>""",unsafe_allow_html=True)

# Configure the Gemini API and OpenAI API
genai.configure(api_key=os.getenv('GEMINI_API_KEY'))
openai.api_key = os.getenv('OPENAI_API_KEY')
youtube_api_key = os.getenv('YOUTUBE_API_KEY')

# System prompt for the hairstylist AI
SYSTEM_PROMPT = '''
You are an expert man hairstylist only for man... you wont suggest any women hairstyle. only mans hairstyle

You are an expert man hairstylist. Analyze the given face photo and provide the following information in valid JSON format:

{
    "Face shape": "",
    "Hair texture": "",
    "Current Hairstyle": "",
    "3 new hairstyles": [
        "",
        "",
        ""
    ]
}

Suggest 3 hairstyle names for the user based on the analyzed data and their additional prompt (if provided). Ensure your entire response is a valid JSON object without any additional text.

**Examples:**

* **Face Shape:** Round, Hair Texture: Wavy, Current Hairstyle: Short Straight
    * 3 new hairstyles:
        1. Textured Bob
        2. Layered Cut
        3. French Braid

* **Face Shape:** Oval, Hair Texture: Straight, Current Hairstyle: Pompadour
    * 3 new hairstyles:
        1. Blunt Cut
        2. Long Layers
        3. Pixie Cut

* **Face Shape:** Long, Hair Texture: Thick, Current Hairstyle: Long and Straight and then elaborate those hairstyles.
    * 3 new hairstyles:
        1. Side Braid (showcases long hair)
        2. Layered Cut with Highlights (adds volume and dimension)
        3. Half-Up Half-Down (versatile for everyday wear)

* **Face Shape:** Square, Hair Texture: Fine, Current Hairstyle: Short and Wavy and then elaborate those hairstyles.
    * 3 new hairstyles:
        1. Lob (elongates the face shape)
        2. Long Layers with Angled Ends (adds softness)
        3. Wavy Pixie with Side Swept Bangs (stylish and flattering)

Please note that these are just examples, and the best hairstyle for you will depend on your individual preferences and hair characteristics.

**Additional Prompt:** Consider the user's ethnicity (if provided) alongside the image analysis to further refine suggestions.

**Limitations:**
* Please avoid suggesting hairstyles that are not suitable for the user's hair length or texture. For example, don't suggest a super long hairstyle for someone with short hair.
* Prioritize suggestions based on their suitability for the user's face shape and hair texture. Don't suggest women hairstyles.
'''

# Function to analyze image and suggest hairstyles
def analyze_image(image, additional_prompt=""):
    model = genai.GenerativeModel('gemini-1.5-flash')
    response = model.generate_content([SYSTEM_PROMPT, additional_prompt, image])
    return response.text

# Function to extract JSON from the AI response
def extract_json(text):
    json_match = re.search(r'\{.*\}', text, re.DOTALL)
    if json_match:
        return json_match.group()
    return None

# Function to parse the AI response
def parse_response(response_text):
    json_str = extract_json(response_text)
    if json_str:
        try:
            return json.loads(json_str)
        except json.JSONDecodeError:
            st.error("Sorry, there was an error processing the AI response. Please try again.")
            return None
    else:
        st.error("Sorry, there was an error processing the AI response. Please try again.")
        return None

# Function to generate hairstyle images using OpenAI's DALL-E
def generate_hairstyle_image(hairstyle_text, ethnicity):
    response = openai.Image.create(
        prompt=f"{hairstyle_text} hairstyle for {ethnicity}",
        n=1,
        size="1024x1024"
    )
    return response.data[0].url

# Function to find related YouTube videos
def find_related_video(query):
    youtube_search_url = f"https://www.googleapis.com/youtube/v3/search?part=snippet&q={query}&key={youtube_api_key}"
    response = requests.get(youtube_search_url)
    if response.status_code == 200:
        data = response.json()
        if data['items']:
            video_ids = [item['id']['videoId'] for item in data['items']]
            video_links = [f"https://www.youtube.com/watch?v={video_id}" for video_id in video_ids[:3]]  # Limit to 3 videos
            return video_links
        else:
            return "No related videos found on YouTube."
    else:
        return "Error fetching videos from YouTube."

# Function to generate chatbot response
def generate_response(prompt):
    response = openai.ChatCompletion.create(
        model="gpt-3.5-turbo",
        messages=[
            {"role": "system", "content": "You are a world-renowned 50-year experienced cool barber..."},
            {"role": "user", "content": prompt}
        ],
        temperature=0.7,
        max_tokens=150
    )
    return response.choices[0].message.content

# Streamlit app main function
def main():
    st.logo("logo.jpeg")
    st.title("GentleMan")
 
    # Tabbed interface for the two functionalities
    tab1, tab2, tab3 = st.tabs(["Popular Hairstyle","Hairstyle Suggestions", "Barber Chatbot"])
    with tab1:
        # Display the image and description centered
        st.header("Hairstyles")
        
        st.image('curly.jpg')
        st.write("This haircut is curly and long. It's a must-have for any man looking to add some volume to their figure.")
        st.image('straight.jpg')
        st.write("This haircut is straight and flat. It's perfect for men who want to add a touch of elegance")
        
    # Hairstyle Suggestions Tab
    with tab2:
        st.header("Hairstyle Suggestion AI")
        input_method = st.radio("Choose input method:", ("Upload Image", "Take Photo"))

        image = None
        if input_method == "Upload Image":
            uploaded_file = st.file_uploader("Choose an image...", type=["jpg", "jpeg", "png"])
            if uploaded_file is not None:
                image = PIL.Image.open(uploaded_file)
        else:
            camera_photo = st.camera_input("Take a photo")
            if camera_photo is not None:
                image = PIL.Image.open(camera_photo)

        if image is not None:
            st.image(image, caption='Your Image', use_column_width=True)

            additional_prompt = st.text_input("Ethnicity (optional):", placeholder="e.g., Asian, Caucasian, etc.")

            if st.button("Analyze and Suggest"):
                with st.spinner("Analyzing image..."):
                    response_text = analyze_image(image, additional_prompt)
                    result = parse_response(response_text)

                    if result:
                        st.subheader("Analysis Results:")
                        st.write(f"*Face Shape:* {result.get('Face shape', 'Not specified')}")
                        st.write(f"*Hair Texture:* {result.get('Hair texture', 'Not specified')}")
                        st.write(f"*Current Hairstyle:* {result.get('Current Hairstyle', 'Not specified')}")

                        st.subheader("Suggested Hairstyles:")
                        new_hairstyles = result.get('3 new hairstyles', [])
                        if isinstance(new_hairstyles, list):
                            for i, style in enumerate(new_hairstyles, 1):
                                st.write(f"{i}. {style}")
                                hairstyle_image = generate_hairstyle_image(style, additional_prompt)
                                st.image(hairstyle_image, caption=f"Generated image for {style}")
                        else:
                            st.write(new_hairstyles)

    # Barber Chatbot Tab
    with tab3:
        st.header("Cool Barber Chatbot")
        user_input = st.text_input("Ask me anything about men's hair care!")

        if st.button("Ask"):
            response = generate_response(user_input)
            video_links = find_related_video(user_input)
            st.text_area("Response:", value=response)

            if video_links:
                st.write("Here are some related videos on YouTube:")
                for video_link in video_links:
                    st.video(video_link)

if __name__ == "__main__":

    main()
