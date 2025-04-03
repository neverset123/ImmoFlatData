import logging
import os
import requests
import subprocess
from flask_cors import CORS
from flask_limiter import Limiter
from flask_limiter.util import get_remote_address
from flask import Flask, request, jsonify


app = Flask(__name__)
CORS(app)  # Enable CORS for all routes
limiter = Limiter(
    get_remote_address,  # Use the client's IP address for rate limiting
    app=app,
    default_limits=["5 per minute"]  # Default rate limit: 5 requests per minute
)


def trigger():
    logging.info('Azure Function triggered to start GitHub Actions workflow.')

    GITHUB_TOKEN = os.getenv("GITHUB_TOKEN")
    REPO_OWNER = "neverset123"
    REPO_NAME = "ImmoFlatData"
    WORKFLOW_FILE = "Agent_trigger.yaml"

    github_api_url = f"https://api.github.com/repos/{REPO_OWNER}/{REPO_NAME}/actions/workflows/{WORKFLOW_FILE}/dispatches"

    try:
        response = requests.post(
            github_api_url,
            headers={
                "Authorization": f"Bearer {GITHUB_TOKEN}",
                "Accept": "application/vnd.github+json",
            },
            json={"ref": "main"}
        )
        print(response)

        if response.status_code == 204:
            logging.info("GitHub Actions workflow triggered successfully.")

        else:
            logging.error(f"Failed to trigger GitHub Actions workflow: {response.text}")

    except Exception as e:
        logging.error(f"Error triggering GitHub Actions workflow: {str(e)}")

@app.route("/")
def home():
    return "Hello,  ImmoAgent!"

@app.route('/trigger', methods=['POST'])
@limiter.limit("5 per minute")  # Custom rate limit for this route
def run():
    try:
        trigger()
        return jsonify({
            'status': 'success'
        }), 200

    except Exception as e:
        return jsonify({'status': 'error', 'message': str(e)}), 500

if __name__ == '__main__':
    app.run(debug=True)