# YouTube Transcript API Service
# This is a simple Flask server that fetches YouTube transcripts
# Install: pip install youtube-transcript-api flask flask-cors
# Run: python transcript_server.py

from flask import Flask, request, jsonify
from flask_cors import CORS
from youtube_transcript_api import YouTubeTranscriptApi
from youtube_transcript_api.formatters import TextFormatter
import re

app = Flask(__name__)
CORS(app)  # Enable CORS for all routes

def extract_video_id(url_or_id):
    """Extract video ID from various YouTube URL formats"""
    patterns = [
        r'(?:youtube\.com\/watch\?v=|youtu\.be\/|youtube\.com\/embed\/|youtube\.com\/v\/)([a-zA-Z0-9_-]{11})',
        r'^([a-zA-Z0-9_-]{11})$'
    ]
    
    for pattern in patterns:
        match = re.search(pattern, url_or_id)
        if match:
            return match.group(1)
    return None

@app.route('/transcript', methods=['GET', 'POST'])
def get_transcript():
    try:
        # Get video URL/ID from request
        if request.method == 'POST':
            data = request.json
            video_url = data.get('url') or data.get('video_id')
        else:
            video_url = request.args.get('url') or request.args.get('video_id')
        
        if not video_url:
            return jsonify({'error': 'No video URL or ID provided'}), 400
        
        # Extract video ID
        video_id = extract_video_id(video_url)
        if not video_id:
            return jsonify({'error': 'Invalid YouTube URL or video ID'}), 400
        
        # Initialize API
        ytt_api = YouTubeTranscriptApi()
        
        # Try to get transcript in preferred languages
        try:
            transcript_list = ytt_api.list(video_id)
            
            # Try to find English transcript first, then any available
            transcript = None
            try:
                transcript = transcript_list.find_transcript(['en', 'en-US', 'en-GB'])
            except:
                # Get first available transcript
                for t in transcript_list:
                    transcript = t
                    break
            
            if transcript:
                # Fetch the transcript
                fetched = transcript.fetch()
                
                # Format as plain text
                formatter = TextFormatter()
                text_transcript = formatter.format_transcript(fetched)
                
                return jsonify({
                    'success': True,
                    'video_id': video_id,
                    'language': transcript.language,
                    'language_code': transcript.language_code,
                    'is_generated': transcript.is_generated,
                    'transcript': text_transcript,
                    'snippets': fetched.to_raw_data()
                })
            else:
                return jsonify({'error': 'No transcript available for this video'}), 404
                
        except Exception as e:
            return jsonify({'error': f'Failed to fetch transcript: {str(e)}'}), 500
            
    except Exception as e:
        return jsonify({'error': str(e)}), 500

@app.route('/health', methods=['GET'])
def health_check():
    return jsonify({'status': 'ok', 'service': 'YouTube Transcript API'})

if __name__ == '__main__':
    print("=" * 60)
    print("YouTube Transcript API Server")
    print("=" * 60)
    print("Starting server on http://localhost:5001")
    print("")
    print("Endpoints:")
    print("  GET  /transcript?url=<youtube_url>")
    print("  POST /transcript with JSON body: {\"url\": \"<youtube_url>\"}")
    print("  GET  /health - Health check")
    print("")
    print("Example:")
    print("  curl http://localhost:5001/transcript?url=https://youtu.be/dQw4w9WgXcQ")
    print("=" * 60)
    app.run(host='0.0.0.0', port=5001, debug=True)
