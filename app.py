# from flask import Flask, render_template, request, jsonify

# app = Flask(__name__)

# # Location modifiers for percentage increase based on body part
# location_modifiers = {
#     "arm": 0.0, "leg": 0.0, "back": 0.1, "chest": 0.1,
#     "neck": 0.35, "ribcage": 0.2, "hand": 0.25, "foot": 0.15
# }

# # Feature modifiers for different styles
# style_modifiers = {
#     "outline_simple": 0.0, "outline_detailed": 0.1,
#     "outline_shading_simple": 0.15, "outline_shading_detailed": 0.20,
#     "outline_color_simple": 0.25, "outline_color_detailed": 0.3,
#     "realism": 0.25, "color_realism": 0.35
# }

# # Function to calculate the tattoo price
# def calculate_price(height, width, location, style):
#     min_price = 150
#     price_per_sq_cm = 4.5
#     total_area = height * width

#     base_price = max(min_price, total_area * price_per_sq_cm)
#     location_modifier = location_modifiers.get(location, 0.0)
#     style_modifier = style_modifiers.get(style, 0.0)

#     final_price = base_price * (1 + location_modifier)
#     final_price *= (1 + style_modifier)

#     # Apply discount for larger tattoos
#     discount = min(total_area * 0.01, 0.5)  # Cap discount to 50%
#     final_price *= (1 - discount)

#     # Ensure the price is not negative and round to the nearest $10
#     final_price = max(final_price, min_price)
#     final_price = round(final_price / 10) * 10

#     return final_price

# # Route to render the main page with the form
# @app.route('/')
# def index():
#     return render_template('index.html')

# # Route to generate pricing quote
# @app.route('/generate_quote', methods=['POST'])
# def generate_quote():
#     try:
#         data = request.json
#         height = float(data['height'])
#         width = float(data['width'])
#         location = data.get('location', 'arm')
#         style = data.get('style', 'simple_color')

#         price = calculate_price(height, width, location, style)
#         return jsonify({"quote": f"Estimated Price: ${price:.2f}"})
#     except Exception as e:
#         print(f"Error generating quote: {e}")
#         return jsonify({"error": str(e)}), 400
       
# # Route to render the AI generator page
# @app.route('/generator')
# def generator():
#     return render_template('generator.html')

# if __name__ == '__main__':
#     app.run(debug=True)
