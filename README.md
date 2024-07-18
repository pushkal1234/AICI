
# Translation and Sentiment Analysis API

This project provides a Flask-based API for performing text translation and sentiment analysis using custom controllers. The API supports two main functionalities:
1. Translating text to German.
2. Analyzing the sentiment of a given text.

## Project Structure

```
project/
│
├── config.json
├── controllers/
│   ├── __init__.py
│   ├── translation_controller.py
│   └── sentiment_controller.py
├── utils.py
├── app.py
└── main.py
```

### Files Description
- **config.json:** Configuration file for the project.
- **controllers/translation_controller.py:** Contains the `TranslationController` class for text translation.
- **controllers/sentiment_controller.py:** Contains the `SentimentController` class for sentiment analysis.
- **controllers/__init__.py:** Initializes the controllers package.
- **utils.py:** Utility functions including `load_config` and `class_factory`.
- **app.py:** Flask application setup and endpoint definitions.
- **main.py:** Main script for generating responses using the controllers.

## Setup

### Prerequisites

- Python 3.x
- pip (Python package installer)

### Installation

1. Clone the repository:

   ```sh
   git clone https://github.com/your-username/your-repo.git
   cd your-repo
   ```

2. Install required packages:

   ```sh
   pip install -r requirements.txt
   ```

3. Ensure the `config.json` file is correctly set up in the project root.

### Running the Flask API

Run the Flask application using the following command:

```sh
python app.py
```

The API will be available at `http://127.0.0.1:5000`.

## API Endpoints

### 1. Translate Text

- **URL:** `/translate`
- **Method:** `POST`
- **Description:** Translates the given text to German.
- **Request Body:**
  ```json
  {
    "text": "Text to be translated",
    "model": "model_name"  // optional, default is 'default_model'
  }
  ```
- **Response:**
  ```json
  {
    "translated_text": "Translated text"
  }
  ```

### 2. Analyze Sentiment

- **URL:** `/sentiment`
- **Method:** `POST`
- **Description:** Analyzes the sentiment of the given text.
- **Request Body:**
  ```json
  {
    "text": "Text for sentiment analysis",
    "model": "model_name"  // optional, default is 'default_model'
  }
  ```
- **Response:**
  ```json
  {
    "positive": count,
    "negative": count,
    "neutral": count
  }
  ```

## Example Usage

### Translation Example
```sh
curl -X POST http://127.0.0.1:5000/translate -H "Content-Type: application/json" -d '{"text": "I am good", "model": "phi3"}'
```

### Sentiment Analysis Example
```sh
curl -X POST http://127.0.0.1:5000/sentiment -H "Content-Type: application/json" -d '{"text": "I am very happy. I am very sad", "model": "phi3"}'
```

## License

This project is licensed under the MIT License. See the [LICENSE](LICENSE) file for details.

## Acknowledgements

- [Flask](https://flask.palletsprojects.com/)
- [LangID](https://github.com/saffsd/langid.py)
- [Langchain Community](https://github.com/langchain-community)
