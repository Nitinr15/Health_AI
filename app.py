from flask import Flask, request, jsonify, render_template
from PIL import Image
import pytesseract
import openai
import os
import json
from dotenv import load_dotenv
import pinecone
from pinecone_help import store_data_in_pinecone




app = Flask(__name__)

# Load environment variables from a .env file if it exists
load_dotenv()

# Path to the Tesseract-OCR executable
pytesseract.pytesseract.tesseract_cmd = r'/usr/bin/tesseract'

# Set OpenAI API key
openai.api_key = os.getenv("OPENAI_API_KEY")

def extract_text_from_image(image_path):
    try:
        # Open the image file
        img = Image.open(image_path)
       
        # Use pytesseract to do OCR on the image
        text = pytesseract.image_to_string(img)
       
        return text
    except Exception as e:
        print(f"Error: {e}")
        return None
    
def transcribe_audio(audio_path):
    try:
        with open(audio_path, "rb") as audio_file:
            transcription = openai.Audio.transcribe(
                model="whisper-1",
                file=audio_file
            )
        return transcription['text']
    except Exception as e:
        print(f"Error in transcribe_audio: {e}")
        return None

def detect_and_translate(text):
    prompt = f"""
    You are a language detection and translation assistant.
    First, detect the language of the following text: "{text}".
    If the detected language is not English, translate it into the English language.
    Return the detected language and the translated text in the following format:
    {{
        "detected_language": "DETECTED_LANGUAGE",
        "translated_text": "TRANSLATED_TEXT"
    }}
    """

    response = openai.ChatCompletion.create(
        model="gpt-4",
        messages=[
            {"role": "system", "content": "You are a language detection and translation assistant."},
            {"role": "user", "content": prompt}
        ]
    )

    result = json.loads(response['choices'][0]['message']['content'].strip())
    return result

def get_icd_codes_and_treatment_and_soap_notes(text):
    try:
        prompt = f"""
        From the given prescription either it is audio or an image, extract the ICD-10 codes and provide the corresponding treatment or medication recommendations. 
        treatment or medication recommendations should be short as much as possible in answer to manage the disease.
        Finally, generate SOAP notes based on the extracted ICD codes in the prescribed format.
        format should be in dictionary format.
        
        Text: {text}
        
        Format:
        {{
            "ICD Code": "ICD_CODE",
            "Treatment": "TREATMENT",
            "SOAP Notes": "SOAP_NOTES"
        }}
        """
       
        response = openai.ChatCompletion.create(
            model="gpt-4o",
            messages=[
                {"role": "system", "content": "You are a helpful assistant knowledgeable in medical terminologies."},
                {"role": "user", "content": prompt}
            ],
            max_tokens=500
        )
       
        return response.choices[0].message['content'].strip()
        
    except Exception as e:
        print(f"Error: {e}")
        return None
def create_embedding(text):
    try:
        response = openai.Embedding.create(
            model="text-embedding-ada-002",
            input=text
        )
        embedding = response['data'][0]['embedding']
        return embedding
    except Exception as e:
        print(f"Error in create_embedding: {e}")
        return None
    
@app.route('/')
def index():
    return render_template('index.html')

@app.route('/extract', methods=['POST'])
def extract():
    if 'file' not in request.files:
        return jsonify({"error": "No file found in the request"}), 400

    file = request.files['file']
    if file.filename == '':
        return jsonify({"error": "No selected file"}), 400

    # Ensure the static directory exists
    if not os.path.exists('static'):
        os.makedirs('static')

    # Save the file to the static directory
    file_path = os.path.join('static', file.filename)
    file.save(file_path)    

    if file.filename.lower().endswith(('.png', '.jpg', '.jpeg', '.tiff', '.bmp', '.gif')):
        extracted_text = extract_text_from_image(file_path)
    elif file.filename.lower().endswith(('.mp3', '.wav', '.flac')):
        extracted_text = transcribe_audio(file_path)
        if not extracted_text:
            return jsonify({"error": "Failed to transcribe audio"}), 500
        
    
    else:
        return jsonify({"error": "Unsupported file type"}), 400

    if not extracted_text:
        return jsonify({"error": "Failed to extract text"}), 500

    # Get ICD codes and treatment
    icd_and_treatment_and_soap = get_icd_codes_and_treatment_and_soap_notes(extracted_text)
    if not icd_and_treatment_and_soap:
        return jsonify({"error": "Failed to get ICD codes and treatments"}), 500
    

     # Create embedding
    embedding = create_embedding(extracted_text)
    if embedding:
        metadata = {
            'id': os.path.basename(file_path),
            'text': extracted_text,
            'icd_and_treatment': icd_and_treatment_and_soap
        }
        store_data_in_pinecone(embedding, metadata)
        return jsonify({"extracted_text": extracted_text, "icd_and_treatment": icd_and_treatment_and_soap})
    else:
        return jsonify({"error": "Failed to create embedding"}), 500


if __name__ == '__main__':
    app.run(debug=True)
