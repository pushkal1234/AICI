from flask import Flask, request, jsonify
import pandas as pd
from datetime import datetime
import threading
from controllers.sentiment_controller import SentimentController
from controllers.translation_controller import TranslationController
from controllers.poem_controller import PoemController
from utils import load_config, class_factory

app = Flask(__name__)

# Load configuration
CONFIG = load_config()

logs_csv = pd.read_csv('logs/input_output.csv', index_col=0)
lock = threading.Lock()


@app.route('/translate', methods=['POST'])
def translate_text():
    try:
        data = request.get_json()
        text = data['text']
        model = data.get('model', 'phi3')  # Use a default model if not provided
        controller_name = 'TranslationController'
        translated_text, total_token = generate_response(text, model, controller_name)
        return jsonify({'response': translated_text, "total_token" : total_token})
    except Exception as e:
        return jsonify({'error': str(e)}), 400


@app.route('/sentiment', methods=['POST'])
def analyze_sentiment():
    try:
        data = request.get_json()
        text = data['text']
        model = data.get('model', 'phi3')  # Use a default model if not provided
        controller_name = 'SentimentController'
        sentiment_result, total_token = generate_response(text, model, controller_name)
        return jsonify({'response': sentiment_result, "total_token" : total_token})
    except Exception as e:
        return jsonify({'error': str(e)}), 400

@app.route('/poem', methods=['POST'])
def generate_poem():
    try:
        data = request.get_json()
        text = data['text']      
        model = data.get('model', 'phi3')  # Use a default model if not provided
        controller_name = 'PoemController'
        poem_result, total_token = generate_response(text, model, controller_name)
        return jsonify({'response': poem_result, "total_token" : total_token})
    except Exception as e:
        return jsonify({'error': str(e)}), 400

def generate_response(text, model, controller_name):
    try:
        model = CONFIG[model]
        controller = class_factory(controller_name, model)
        current_time = datetime.now()

        if isinstance(controller, TranslationController):
            translated_text, total_token = controller.generate_translation(text)
            new_row = [current_time, text, translated_text]
            
            return translated_text, total_token

        elif isinstance(controller, SentimentController):
            sentiment_result, total_token = controller.generate_sentiment(text)
            new_row = [current_time, text, sentiment_result]

            return sentiment_result, total_token
        
        elif isinstance(controller, PoemController):
            poem_result, total_token = controller.generate_poem(text)
            new_row = [current_time, text, poem_result]
            
            return poem_result, total_token
            
        else:
            raise ValueError(f"Unsupported controller type: {controller_name}")

    except Exception as e:
        print(f"\033[91mAn error occurred: {e}\033[0m")  # Print in red
        return None
    
    finally:
            # Use a lock to ensure thread safety
            with lock:
                try:
                    logs_csv.loc[len(logs_csv)] = new_row
                    logs_csv.to_csv('logs/input_output.csv')
                    print(f"\033[92mLog saved successfully.\033[0m")  
                    
                except Exception as save_error:
                    print(f"\033[91mFailed to save log: {save_error}\033[0m")  



if __name__ == '__main__':
    app.run(host='0.0.0.0', port=5000)

