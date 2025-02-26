from flask import Flask, request, jsonify
import pandas as pd
from datetime import datetime
import threading
from controllers.sentiment_controller import SentimentController
from controllers.translation_controller import TranslationController
from controllers.poem_controller import PoemController
from controllers.json_controller import JSONController
from controllers.sql_controller import SQLController
from utils import load_config, class_factory
from controllers.benchmark_controller import BenchmarkController

app = Flask(__name__)

# Load configuration
CONFIG = load_config()

logs_csv = pd.read_csv('logs/input_output.csv', index_col=0)
lock = threading.Lock()


@app.route('/translate', methods=['POST'])
def translate():
    try:
        data = request.get_json()
        if not data or 'text' not in data:
            return jsonify({
                'error': 'Missing text field',
                'status': 'error',
                'timestamp': datetime.now().isoformat()
            }), 400

        # Create input data dictionary
        input_data = {
            'text': data['text'],
            'target_language': data.get('target_language', 'german')  # Default to German
        }
        
        model = data.get('model', 'phi3')  # Default to phi3 if not specified
        controller_name = 'TranslationController'
        
        translated_text, total_token = generate_response(input_data, model, controller_name)
        
        if isinstance(translated_text, str) and not translated_text.startswith('Error'):
            return jsonify({
                'translation': translated_text,
                'target_language': input_data['target_language'],
                'tokens_used': total_token,
                'status': 'success',
                'timestamp': datetime.now().isoformat()
            }), 200
        else:
            return jsonify({
                'error': translated_text,
                'status': 'error',
                'timestamp': datetime.now().isoformat()
            }), 500

    except Exception as e:
        return jsonify({
            'error': str(e),
            'status': 'error',
            'timestamp': datetime.now().isoformat()
        }), 500


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

@app.route('/process-json', methods=['POST'])
def process_json():
    try:
        data = request.get_json()
        
        # Validate required fields in request
        required_fields = ['text', 'date', 'schema']
        missing_fields = [field for field in required_fields if field not in data]
        
        if missing_fields:
            return jsonify({
                'error': f'Missing required fields: {", ".join(missing_fields)}',
                'status': 'error',
                'timestamp': datetime.now().isoformat()
            }), 400

        model_name = data.get('model', 'phi3')
        
        json_output, total_tokens = generate_response(
            data,  # Passing the entire data object including schema
            model_name,
            "JSONController"
        )

        if json_output:
            if "error" in json_output:
                return jsonify(json_output), json_output.get("code", 500)
                
            response = {
                'result': json_output,
                'tokens_used': total_tokens,
                'status': 'success',
                'timestamp': datetime.now().isoformat()
            }
            return jsonify(response), 200
        else:
            return jsonify({
                'error': 'Failed to process data',
                'status': 'error',
                'timestamp': datetime.now().isoformat()
            }), 500

    except Exception as e:
        return jsonify({
            'error': str(e),
            'status': 'error',
            'timestamp': datetime.now().isoformat()
        }), 500

@app.route('/generate-sql', methods=['POST'])
def generate_sql():
    try:
        data = request.get_json()
        if not data or 'text' not in data:
            return jsonify({
                'error': 'Missing required fields',
                'status': 'error',
                'timestamp': datetime.now().isoformat()
            }), 400

        model = data.get('model', 'phi3')
        controller_name = 'SQLController'
        
        sql_output, total_tokens = generate_response(data, model, controller_name)
        
        if isinstance(sql_output, dict) and sql_output.get('status') == 'success':
            return jsonify({
                'result': sql_output,
                'tokens_used': total_tokens,
                'status': 'success',
                'timestamp': datetime.now().isoformat()
            }), 200
        else:
            return jsonify(sql_output), sql_output.get('code', 500)

    except Exception as e:
        return jsonify({
            'error': str(e),
            'status': 'error',
            'timestamp': datetime.now().isoformat()
        }), 500

@app.route('/benchmark', methods=['POST'])
def run_benchmark():
    try:
        data = request.get_json()
        if not data or 'test_cases' not in data:
            return jsonify({
                'error': 'Missing test cases',
                'status': 'error',
                'timestamp': datetime.now().isoformat()
            }), 400

        benchmark = BenchmarkController()
        model = data.get('model', 'phi3')
        
        # Create controllers for each test case
        for test in data['test_cases']:
            if test['type'] == 'translation':
                test['controller'] = TranslationController(CONFIG[model])
            elif test['type'] == 'sql':
                test['controller'] = SQLController(CONFIG[model])
            elif test['type'] == 'json':
                test['controller'] = JSONController(CONFIG[model])
            elif test['type'] == 'sentiment':
                test['controller'] = SentimentController(CONFIG[model])

        results = benchmark.run_benchmark(data['test_cases'], model)
        
        return jsonify({
            'results': results,
            'status': 'success',
            'timestamp': datetime.now().isoformat()
        }), 200

    except Exception as e:
        return jsonify({
            'error': str(e),
            'status': 'error',
            'timestamp': datetime.now().isoformat()
        }), 500

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
            
        elif isinstance(controller, JSONController):
            json_output, total_token = controller.process_financial_data(text)
            new_row = [current_time, str(text), str(json_output)]
            return json_output, total_token

        elif isinstance(controller, SQLController):
            sql_output, total_token = controller.generate_sql_query(text)
            new_row = [current_time, str(text), str(sql_output)]
            return sql_output, total_token

        else:
            raise ValueError(f"Unsupported controller type: {controller_name}")

    except Exception as e:
        print(f"\033[91mAn error occurred: {e}\033[0m")  # Print in red
        return None, 0  # Return tuple with None and 0 tokens
    
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

