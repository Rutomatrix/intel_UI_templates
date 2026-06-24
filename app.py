from flask import Flask, render_template, session, request, jsonify
import secrets
import os
import json

app = Flask(__name__)
app.secret_key = secrets.token_hex(16)

# Path to config.js file
CONFIG_PATH = 'static/scripts/config.js'

@app.route('/')
def index():
    """Main dashboard page"""
    if 'session_id' not in session:
        session['session_id'] = secrets.token_hex(8)
    return render_template('index.html')

@app.route('/save-config', methods=['POST'])
def save_config():
    """
    Endpoint to save server configuration to config.js file
    """
    try:
        # Get the content from the request body
        data = request.get_json()
        content = data.get('content')
        
        if not content:
            return jsonify({
                'success': False,
                'error': 'No content provided'
            }), 400
        
        # Ensure the directory exists
        os.makedirs(os.path.dirname(CONFIG_PATH), exist_ok=True)
        
        # Write the content to the file
        with open(CONFIG_PATH, 'w', encoding='utf-8') as f:
            f.write(content)
        
        return jsonify({
            'success': True,
            'message': 'Config saved successfully',
            'path': CONFIG_PATH,
            'content': content
        }), 200
        
    except PermissionError as e:
        return jsonify({
            'success': False,
            'error': f'Permission denied: {str(e)}'
        }), 403
        
    except IOError as e:
        return jsonify({
            'success': False,
            'error': f'IO error: {str(e)}'
        }), 500
        
    except Exception as e:
        return jsonify({
            'success': False,
            'error': f'Unexpected error: {str(e)}'
        }), 500

@app.route('/get-config', methods=['GET'])
def get_config():
    """
    Endpoint to read the current server configuration
    """
    try:
        if os.path.exists(CONFIG_PATH):
            with open(CONFIG_PATH, 'r', encoding='utf-8') as f:
                content = f.read()
            
            # Parse the content to extract server name
            server_name = 'SPR'  # Default
            rpi_ip = '10.208.50.57'  # Default
            
            # Simple parsing to extract values
            if 'serverName:' in content:
                import re
                match = re.search(r"serverName:\s*'([^']+)'", content)
                if match:
                    server_name = match.group(1)
                match = re.search(r"RPI_ip:\s*'([^']+)'", content)
                if match:
                    rpi_ip = match.group(1)
            
            return jsonify({
                'success': True,
                'content': content,
                'serverName': server_name,
                'RPI_ip': rpi_ip,
                'path': CONFIG_PATH
            }), 200
        else:
            return jsonify({
                'success': False,
                'error': 'Config file not found',
                'serverName': 'SPR',
                'RPI_ip': '10.208.50.57'
            }), 404
            
    except Exception as e:
        return jsonify({
            'success': False,
            'error': f'Error reading config: {str(e)}'
        }), 500

@app.route('/api/server-status', methods=['GET'])
def server_status():
    """
    Get current server status
    """
    try:
        if os.path.exists(CONFIG_PATH):
            with open(CONFIG_PATH, 'r', encoding='utf-8') as f:
                content = f.read()
            
            server_name = 'SPR'
            rpi_ip = '10.208.50.57'
            
            import re
            match = re.search(r"serverName:\s*'([^']+)'", content)
            if match:
                server_name = match.group(1)
            match = re.search(r"RPI_ip:\s*'([^']+)'", content)
            if match:
                rpi_ip = match.group(1)
            
            return jsonify({
                'success': True,
                'serverName': server_name,
                'RPI_ip': rpi_ip,
                'status': 'active'
            }), 200
        else:
            return jsonify({
                'success': False,
                'serverName': 'SPR',
                'RPI_ip': '10.208.50.57',
                'status': 'default'
            }), 200
            
    except Exception as e:
        return jsonify({
            'success': False,
            'error': str(e)
        }), 500

if __name__ == '__main__':
    app.run(host='0.0.0.0', port=8080, debug=True)
    