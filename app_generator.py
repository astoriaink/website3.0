import base64
from flask import Flask, render_template, request, jsonify
from dotenv import load_dotenv
from openai import OpenAI
import os
import requests
from werkzeug.utils import secure_filename

# Conditionally load environment variables from .env when not on Railway
if not os.getenv("RAILWAY_ENVIRONMENT"):
    load_dotenv()

# Create Flask app and configure secret key
app = Flask(__name__)
app.secret_key = os.getenv("FLASK_SECRET_KEY")  # Secure key loaded from environment

# Define upload folder and make sure it exists
UPLOAD_FOLDER = 'uploads'
os.makedirs(UPLOAD_FOLDER, exist_ok=True)
app.config['UPLOAD_FOLDER'] = UPLOAD_FOLDER

# Set up OpenAI credentials
openai_api_key = os.getenv("OPENAI_API_KEY")
if not openai_api_key:
    raise ValueError("Missing OPENAI_API_KEY environment variable")
openai_client = OpenAI(api_key=openai_api_key)

# Route to render the main page with the form
@app.route('/index')
def index():
    return render_template('index.html')

# Route to render the AI Generator page
@app.route('/generator')
def generator():
    return render_template('generator.html')

# Route to render the homepage as the default page
@app.route('/')
def homepage():
    return render_template('homepage.html')

# Route to generate tattoo design
@app.route('/generate_tattoo', methods=['POST'])
def generate_tattoo():
    try:
        data = request.form
        main_concept = data.get('mainConcept', '')
        details = data.get('details', '')
        background = data.get('background', '')
        style = data.get('style', "I'll choose my own!")
        custom = data.get('custom', '')
        black_and_grey = 'yes' if data.get('blackAndGrey') == 'yes' else 'no'
        color = data.get('color', '')
        image_format = data.get('imageFormat', 'square')

        customer_prompt = f"Create an image design that is {main_concept}. Details: {details}. Background: {background}"
        color_prompt = f"with color {color}" if color else ""
        black_and_grey_prompt = "in black and grey" if black_and_grey == 'yes' else ""

        size = "1024x1792" if image_format == "portrait" else "1792x1024" if image_format == "landscape" else "1024x1024"

        prompt = f"""{customer_prompt}. {color_prompt} {black_and_grey_prompt}. In the style of {custom.lower() if style == "I'll choose my own!" else style.lower()}"""

        # Call OpenAI to generate image
        response = openai_client.images.generate(
            model="dall-e-3",
            prompt=prompt,
            n=1,
            size=size,
        )

        # Retrieve image URL from the response
        image_url = response.data[0].url

        return jsonify({"imageUrl": image_url})
    except Exception as e:
        print(f"Error generating tattoo: {e}")
        return jsonify({"error": "Failed to generate tattoo. Please try again."}), 400

# Route to generate pricing quote
@app.route('/generate_quote', methods=['POST'])
def generate_quote():
    try:
        data = request.json
        height = float(data['height'])
        width = float(data['width'])
        location = data.get('location', 'arm')
        style = data.get('style', 'outline_simple')

        price = calculate_price(height, width, location, style)

        # Add note for high price suggesting full-day session
        note = ""
        if price > 1200:
            note = " Request full day session for better pricing"

        return jsonify({"quote": f"Estimated Price: ${price:.2f}{note}"})
    except Exception as e:
        print(f"Error generating quote: {e}")
        return jsonify({"error": str(e)}), 400

# Function to calculate the tattoo price
def calculate_price(height, width, location, style):
    min_price = 150
    price_per_sq_cm = 5
    total_area = height * width

    base_price = max(min_price, total_area * price_per_sq_cm)
    location_modifier = location_modifiers.get(location, 0.0)
    style_modifier = style_modifiers.get(style, 0.0)

    final_price = base_price * (1 + location_modifier)
    final_price *= (1 + style_modifier)

    discount = min(total_area * 0.002, 0.5)  # Cap discount to 50%
    final_price *= (1 - discount)

    final_price = max(final_price, min_price)
    final_price = round(final_price / 10) * 10

    return final_price

# Location modifiers for percentage increase based on body part
location_modifiers = {
    "arm": 0.0, "leg": 0.0, "back": 0.1, "chest": 0.1,
    "neck": 0.35, "ribcage": 0.2, "hand": 0.25, "foot": 0.15
}

# Feature modifiers for different style
style_modifiers = {
    "outline_simple": 0.0, "outline_detailed": 0.1,
    "outline_shading_simple": 0.15, "outline_shading_detailed": 0.20,
    "outline_color_simple": 0.25, "outline_color_detailed": 0.3,
    "realism": 0.25, "color_realism": 0.35
}

@app.route('/book')
def book():
    return render_template('book.html')

# Route to handle booking form submission and send an email
@app.route('/submit_booking', methods=['POST'])
def submit_booking():
    try:
        # Extract form data
        booking_data = {
            "client_email": request.form.get('clientEmail'),
            "additional_details": request.form.get('additionalDetails'),
            "preferred_dates": request.form.get('preferredDates')  # Get the comma-separated preferred dates
        }

        # Extract multiple quotes
        quotes = []
        index = 0
        while request.form.get(f'height_{index}'):
            quote = {
                "height": request.form.get(f'height_{index}'),
                "width": request.form.get(f'width_{index}'),
                "location": request.form.get(f'location_{index}'),
                "style": request.form.get(f'style_{index}'),
                "quote": request.form.get(f'quote_{index}'),
                "artist": request.form.get(f'artist_{index}')
            }
            quotes.append(quote)
            index += 1

        booking_data["quotes"] = quotes

        print(f"Booking Data Received: {booking_data}")

        # Handle photo uploads
        photo_paths = []
        photos = request.files.getlist('photos[]')  # Get all uploaded photos
        for photo in photos:
            if photo:
                filename = secure_filename(photo.filename)
                photo_path = os.path.join(app.config['UPLOAD_FOLDER'], filename)
                photo.save(photo_path)
                photo_paths.append(photo_path)
                print(f"Photo saved at: {photo_path}")

        # Send email notification with the booking details using Mailjet
        send_email_with_mailjet(booking_data, photo_paths)

        # Respond with a success message
        return jsonify({"success": True})
    except Exception as e:
        print(f"Error submitting booking: {e}")
        return jsonify({"success": False, "error": str(e)}), 400

def send_email_with_mailjet(booking_data, photo_paths=[]):
    mailjet_api_key = os.getenv("MAILJET_API_KEY")
    mailjet_secret_key = os.getenv("MAILJET_SECRET_KEY")
    sender_email = os.getenv("SENDER_EMAIL")
    recipient_email = os.getenv("RECIPIENT_EMAIL")
    client_email = booking_data.get('client_email')

    url = "https://api.mailjet.com/v3.1/send"
    headers = {
        "Content-Type": "application/json"
    }

    # Prepare the attachments if photos are available
    attachments = []
    for photo_path in photo_paths:
        with open(photo_path, "rb") as photo_file:
            base64_encoded = base64.b64encode(photo_file.read()).decode("utf-8")
            attachments.append({
                "ContentType": "image/jpeg",
                "Filename": os.path.basename(photo_path),
                "Base64Content": base64_encoded
            })

    preferred_dates_str = booking_data["preferred_dates"] if booking_data["preferred_dates"] else "No preferred dates provided"

    quotes_str = ""
    for idx, quote in enumerate(booking_data["quotes"], start=1):
        quotes_str += f"<h3>Quote #{idx}</h3>"
        quotes_str += f"<p><strong>Height:</strong> {quote['height']} cm"
        quotes_str += f"<p><strong>Width:</strong> {quote['width']} cm"
        quotes_str += f"<p><strong>Location:</strong> {quote['location']}</p>"
        quotes_str += f"<p><strong>Style:</strong> {quote['style']}</p>"
        quotes_str += f"<p><strong>Estimated Price:</strong> {quote['quote']}</p>"
        quotes_str += f"<p><strong>Artist:</strong> {quote['artist']}</p>"

    payload = {
        "Messages": [
            {
                "From": {
                    "Email": sender_email,
                    "Name": "Tattoo Booking Service"
                },
                "To": [
                    {
                        "Email": recipient_email,
                        "Name": "Tattoo Studio"
                    }
                ],
                "Cc": [
                    {
                        "Email": client_email,
                        "Name": "Client"
                    }
                ],
                "Subject": "New Tattoo Booking Request",
                "TextPart": f"""
                New Tattoo Booking Request:
                {quotes_str}
                Additional Details: {booking_data['additional_details']}
                Preferred Dates: {preferred_dates_str}
                """,
                "HTMLPart": f"""
                <html>
                    <body style="font-family: Arial, sans-serif; padding: 20px; line-height: 1.6;">
                        <h2 style="text-align: center;">New Tattoo Booking Request</h2>
                        {quotes_str}
                        <p><strong>Additional Details:</strong> {booking_data['additional_details']}</p>
                        <p><strong>Preferred Dates:</strong> {preferred_dates_str}</p>
                    </body>
                </html>
                """,
                "Attachments": attachments
            }
        ]
    }

    print("Mailjet Payload:", payload)  # Log the payload

    response = requests.post(url, headers=headers, json=payload, auth=(mailjet_api_key, mailjet_secret_key))
    if response.status_code == 200:
        print("Email sent successfully")
    else:
        print(f"Failed to send email: {response.status_code} {response.text}")

@app.route('/artist_profile')
def artist_profile():
    # Serve the static artist profile page
    return render_template('artist_profile.html')


if __name__ == '__main__':
    if os.getenv("RAILWAY_ENVIRONMENT"):  # Check if running on Railway
        app.run(host='0.0.0.0', port=os.getenv("PORT", 5000))
    else:  # If not on Railway, use the local debug server
        app.run(debug=True)