import json
import os
import secrets
from flask import Flask, request, jsonify, send_from_directory, send_file

BASE_DIR = os.path.dirname(os.path.abspath(__file__))
PUBLIC_DIR = os.path.join(BASE_DIR, 'public')
app = Flask(__name__, static_folder=PUBLIC_DIR, static_url_path='')

DATA_DIR = os.path.join(BASE_DIR, 'data')
os.makedirs(DATA_DIR, exist_ok=True)


def event_path(event_id):
    return os.path.join(DATA_DIR, f'{event_id}.json')


def read_event(event_id):
    path = event_path(event_id)
    if not os.path.exists(path):
        return None
    with open(path) as f:
        return json.load(f)


def write_event(event):
    with open(event_path(event['id']), 'w') as f:
        json.dump(event, f, indent=2)


@app.route('/api/events', methods=['POST'])
def create_event():
    body = request.get_json()
    title = body.get('title', '').strip()
    dates = body.get('dates', [])
    time_start = body.get('timeStart', '')
    time_end = body.get('timeEnd', '')

    if not title or not dates or not time_start or not time_end:
        return jsonify({'error': 'Missing required fields'}), 400

    event_id = secrets.token_hex(5)
    event = {
        'id': event_id,
        'title': title,
        'dates': sorted(dates),
        'timeStart': time_start,
        'timeEnd': time_end,
        'responses': []
    }
    write_event(event)
    return jsonify({'id': event_id})


@app.route('/api/events/<event_id>', methods=['GET'])
def get_event(event_id):
    event = read_event(event_id)
    if event is None:
        return jsonify({'error': 'Event not found'}), 404
    return jsonify(event)


@app.route('/api/events/<event_id>/availability', methods=['POST'])
def submit_availability(event_id):
    event = read_event(event_id)
    if event is None:
        return jsonify({'error': 'Event not found'}), 404

    body = request.get_json()
    name = body.get('name', '').strip()
    slots = body.get('slots', [])

    if not name or not isinstance(slots, list):
        return jsonify({'error': 'Missing name or slots'}), 400

    responses = event['responses']
    idx = next((i for i, r in enumerate(responses) if r['name'].lower() == name.lower()), -1)
    if idx >= 0:
        responses[idx]['slots'] = slots
    else:
        responses.append({'name': name, 'slots': slots})

    write_event(event)
    return jsonify({'success': True})


@app.route('/event/<event_id>')
def event_page(event_id):
    return send_from_directory(PUBLIC_DIR, 'event.html')


@app.route('/')
def index():
    return send_from_directory(PUBLIC_DIR, 'index.html')


if __name__ == '__main__':
    port = int(os.environ.get('PORT', 3000))
    debug = os.environ.get('FLASK_ENV') != 'production'
    print(f'Overlap running at http://localhost:{port}')
    app.run(host='0.0.0.0', port=port, debug=debug)
