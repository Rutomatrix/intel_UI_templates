from flask import Flask, render_template, session, request, jsonify
import secrets
import os
import re

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
    Only updates the serverName field, keeps everything else as is
    """
    try:
        data = request.get_json()
        server_name = data.get('serverName')
        usb_ip = data.get('usbIp')
        
        if not server_name:
            return jsonify({
                'success': False,
                'error': 'No server name provided'
            }), 400
        
        # Read existing config file
        if os.path.exists(CONFIG_PATH):
            with open(CONFIG_PATH, 'r', encoding='utf-8') as f:
                content = f.read()
        else:
            # Create default config if file doesn't exist
            content = """const SERVER_CONFIG = {
    serverName: 'SPR',
    rpiIp: window.location.hostname,
    usbIp: '10.208.50.60'
};"""
        
        # Update only the serverName field
        # Pattern to match serverName: 'XXX'
        pattern = r"(serverName:\s*)'[^']*'"
        replacement = r"\1'" + server_name + "'"
        content = re.sub(pattern, replacement, content)
        
        # If usbIp is provided, update it too
        if usb_ip:
            usb_pattern = r"(usbIp:\s*)'[^']*'"
            usb_replacement = r"\1'" + usb_ip + "'"
            content = re.sub(usb_pattern, usb_replacement, content)
        
        # Ensure the directory exists
        os.makedirs(os.path.dirname(CONFIG_PATH), exist_ok=True)
        
        # Write the updated content back to file
        with open(CONFIG_PATH, 'w', encoding='utf-8') as f:
            f.write(content)
        
        return jsonify({
            'success': True,
            'message': 'Config updated successfully',
            'path': CONFIG_PATH
        }), 200
        
    except PermissionError as e:
        return jsonify({
            'success': False,
            'error': f'Permission denied: {str(e)}'
        }), 403
        
    except Exception as e:
        return jsonify({
            'success': False,
            'error': f'Unexpected error: {str(e)}'
        }), 500

@app.route('/update-usb-ip', methods=['POST'])
def update_usb_ip():
    """
    Separate endpoint to update only the USB IP in config.js
    """
    try:
        data = request.get_json()
        usb_ip = data.get('usbIp')
        
        if not usb_ip:
            return jsonify({
                'success': False,
                'error': 'No USB IP provided'
            }), 400
        
        # Validate IP format (simple validation)
        ip_pattern = r'^(\d{1,3}\.){3}\d{1,3}$'
        if not re.match(ip_pattern, usb_ip):
            return jsonify({
                'success': False,
                'error': 'Invalid IP address format'
            }), 400
        
        # Read existing config file
        if os.path.exists(CONFIG_PATH):
            with open(CONFIG_PATH, 'r', encoding='utf-8') as f:
                content = f.read()
        else:
            # Create default config if file doesn't exist
            content = """const SERVER_CONFIG = {
    serverName: 'SPR',
    rpiIp: window.location.hostname,
    usbIp: '10.208.50.60'
};"""
        
        # Update only the usbIp field
        usb_pattern = r"(usbIp:\s*)'[^']*'"
        
        if re.search(usb_pattern, content):
            # Replace existing usbIp
            usb_replacement = r"\1'" + usb_ip + "'"
            content = re.sub(usb_pattern, usb_replacement, content)
        else:
            # Add usbIp if it doesn't exist
            # Find the closing brace of SERVER_CONFIG
            config_obj_pattern = r'const\s+SERVER_CONFIG\s*=\s*\{([\s\S]*?)\}'
            config_match = re.search(config_obj_pattern, content)
            
            if config_match:
                config_body = config_match.group(1).strip()
                needs_comma = not config_body.endswith(',') and config_body != ''
                content = content.replace(
                    config_match.group(0),
                    f'const SERVER_CONFIG = {{{config_body}{"," if needs_comma else ""}\n    usbIp: \'{usb_ip}\'\n}}'
                )
            else:
                return jsonify({
                    'success': False,
                    'error': 'Could not find SERVER_CONFIG in file'
                }), 400
        
        # Ensure the directory exists
        os.makedirs(os.path.dirname(CONFIG_PATH), exist_ok=True)
        
        # Write the updated content back to file
        with open(CONFIG_PATH, 'w', encoding='utf-8') as f:
            f.write(content)
        
        return jsonify({
            'success': True,
            'message': f'USB IP updated to {usb_ip} successfully',
            'path': CONFIG_PATH,
            'usbIp': usb_ip
        }), 200
        
    except PermissionError as e:
        return jsonify({
            'success': False,
            'error': f'Permission denied: {str(e)}'
        }), 403
        
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
            
            # Extract server name
            server_name = 'SPR'  # Default
            usb_ip = '10.208.50.60'  # Default
            
            # Parse serverName
            match = re.search(r"serverName:\s*'([^']+)'", content)
            if match:
                server_name = match.group(1)
            
            # Parse usbIp
            match = re.search(r"usbIp:\s*'([^']+)'", content)
            if match:
                usb_ip = match.group(1)
            
            return jsonify({
                'success': True,
                'serverName': server_name,
                'usbIp': usb_ip,
                'content': content
            }), 200
        else:
            return jsonify({
                'success': False,
                'error': 'Config file not found',
                'serverName': 'SPR',
                'usbIp': '10.208.50.60'
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
            usb_ip = '10.208.50.60'
            
            match = re.search(r"serverName:\s*'([^']+)'", content)
            if match:
                server_name = match.group(1)
            
            match = re.search(r"usbIp:\s*'([^']+)'", content)
            if match:
                usb_ip = match.group(1)
            
            return jsonify({
                'success': True,
                'serverName': server_name,
                'usbIp': usb_ip,
                'status': 'active'
            }), 200
        else:
            return jsonify({
                'success': False,
                'serverName': 'SPR',
                'usbIp': '10.208.50.60',
                'status': 'default'
            }), 200
            
    except Exception as e:
        return jsonify({
            'success': False,
            'error': str(e)
        }), 500

if __name__ == '__main__':
    app.run(host='0.0.0.0', port=8080, debug=True)