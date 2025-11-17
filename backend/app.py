"""Flask web server for OS Debugging Assistant."""

from flask import Flask, request, jsonify, send_from_directory
from flask_cors import CORS
import os
import sys

# Add current directory to path
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from analyzers.hypothesis_engine import HypothesisEngine

app = Flask(__name__, static_folder='../frontend', static_url_path='')
CORS(app)  # Enable CORS for development

# Initialize the hypothesis engine
engine = HypothesisEngine()


@app.route('/')
def index():
    """Serve the main HTML page."""
    return send_from_directory(app.static_folder, 'index.html')


@app.route('/api/analyze', methods=['POST'])
def analyze():
    """
    Main analysis endpoint.

    Expects JSON: {"text": "...debugging output..."}
    Returns JSON with analysis results.
    """
    try:
        data = request.get_json()
        if not data or 'text' not in data:
            return jsonify({'error': 'Missing "text" field in request'}), 400

        text = data['text']
        if not text or not text.strip():
            return jsonify({'error': 'Empty input text'}), 400

        # Run the analysis
        result = engine.analyze(text)

        # Format response
        response = {
            'success': True,
            'summary': result.get('summary', ''),
            'hypotheses': result.get('hypotheses', []),
            'gdb_analysis': result.get('gdb_analysis'),
            'trapframe_analysis': result.get('trapframe_analysis'),
            'pagetable_analysis': result.get('pagetable_analysis'),
            'all_findings': result.get('all_findings', [])
        }

        return jsonify(response)

    except Exception as e:
        return jsonify({
            'success': False,
            'error': str(e)
        }), 500


@app.route('/api/health', methods=['GET'])
def health():
    """Health check endpoint."""
    return jsonify({'status': 'ok'})


if __name__ == '__main__':
    port = int(os.environ.get('PORT', 5000))
    debug = os.environ.get('DEBUG', 'True').lower() == 'true'

    print(f"Starting OS Debugging Assistant on port {port}")
    print(f"Debug mode: {debug}")
    print(f"Access the application at: http://localhost:{port}")

    app.run(host='0.0.0.0', port=port, debug=debug)
