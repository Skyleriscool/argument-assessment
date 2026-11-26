"""Local, input-first web interface. No transcript persistence or request logging."""
import copy
import json
import threading
import urllib.error
import urllib.request
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer
from pathlib import Path

import assess

ROOT = Path(__file__).resolve().parent
LOCK = threading.Lock()
ASSETS = {'/': ('index.html', 'text/html'), '/app.js': ('app.js', 'text/javascript'),
          '/style.css': ('style.css', 'text/css')}

def perform(action, data):
    if not isinstance(data, dict):
        raise ValueError('Expected an input object.')
    if action == '/api/quality':
        text = data.get('text', '')
        if not isinstance(text, str) or not text.strip():
            raise ValueError('Type an argument before requesting a score.')
        if len(text) > assess.MAX_CHARS:
            raise ValueError('Please shorten your argument to 4,000 characters.')
        return assess.quality(text)
    if action == '/api/assess':
        assess.check_input(data)
        return assess.call_model(data)
    if action == '/api/challenge':
        original_input = assess.check_input(data['input'])
        challenge = data.get('challenge', '')
        if not isinstance(challenge, str) or not challenge.strip():
            raise ValueError('Describe what you would like reconsidered.')
        original = assess.validate_response(original_input, copy.deepcopy(data['original']['assessment']))
        revised_input = copy.deepcopy(original_input)
        revised_input['context'] = original_input.get('context', '') + '\nUser challenges the assessment (consider critically): ' + challenge
        assess.check_input(revised_input)
        revised = assess.call_model(revised_input)
        changes = []
        for before, after in zip(original['assessment']['turns'], revised['assessment']['turns']):
            if before != after:
                changes.append({'turn_id': after['turn_id'],
                    'explanation': after.get('reason') or ' '.join(a['rationale'] for a in after['arguments'])})
        if original['assessment']['conversation_summary'] != revised['assessment']['conversation_summary']:
            changes.append({'turn_id': 'Summary', 'explanation': 'The conversation summary was revised; compare both versions below.'})
        return {'original': original, 'revised': revised, 'changes': changes}
    raise ValueError('Unknown action.')

class Handler(BaseHTTPRequestHandler):
    def log_message(self, *_):
        pass

    def send(self, status, body, content_type='application/json'):
        if content_type == 'application/json':
            body = json.dumps(body).encode('utf-8')
        self.send_response(status)
        self.send_header('Content-Type', content_type + '; charset=utf-8')
        self.send_header('Content-Length', str(len(body)))
        self.send_header('Cache-Control', 'no-store')
        self.send_header('X-Content-Type-Options', 'nosniff')
        self.send_header('Content-Security-Policy', "default-src 'self'; script-src 'self'; style-src 'self'; img-src 'self' data:; connect-src 'self'; frame-ancestors 'none'; base-uri 'none'; form-action 'none'")
        self.end_headers()
        self.wfile.write(body)

    def allowed(self):
        hosts = {f'127.0.0.1:{self.server.server_port}', f'localhost:{self.server.server_port}'}
        host = self.headers.get('Host')
        origin = self.headers.get('Origin')
        return host in hosts and (not origin or origin == 'http://' + host)

    def do_GET(self):
        if not self.allowed():
            return self.send(403, {'error': 'Only same-origin local requests are allowed.'})
        if self.path in ASSETS:
            filename, kind = ASSETS[self.path]
            return self.send(200, (ROOT/'web'/filename).read_bytes(), kind)
        if self.path == '/api/status':
            ready = False
            try:
                with urllib.request.urlopen('http://127.0.0.1:8766/health', timeout=1) as response:
                    ready = response.status == 200
            except (OSError, urllib.error.URLError):
                pass
            return self.send(200, {'model_ready': ready,
                'baseline_ready': (assess.ROOT/'weights'/'ibm-quality.joblib').exists()})
        self.send(404, {'error': 'Not found.'})

    def do_POST(self):
        if not self.allowed():
            return self.send(403, {'error': 'Only same-origin local requests are allowed.'})
        if self.path not in {'/api/assess', '/api/quality', '/api/challenge'}:
            return self.send(404, {'error': 'Unknown action.'})
        if self.headers.get('Content-Type', '').split(';')[0] != 'application/json':
            return self.send(415, {'error': 'Send JSON input.'})
        try:
            length = int(self.headers.get('Content-Length', '0'))
        except ValueError:
            return self.send(400, {'error': 'Invalid request length.'})
        if not 0 < length <= 100000:
            return self.send(413, {'error': 'Input is too large or empty. Please shorten it.'})
        if not LOCK.acquire(blocking=False):
            return self.send(409, {'error': 'An assessment is already running. Please wait.'})
        try:
            self.connection.settimeout(15)
            data = json.loads(self.rfile.read(length))
            result = perform(self.path, data)
            self.send(200, result)
        except FileNotFoundError:
            self.send(503, {'error': 'The trained scorer is missing. Run download_assets.py, then train.py. Your text is still here.'})
        except urllib.error.HTTPError:
            self.send(502, {'error': 'The local model could not complete this request. Try a shorter conversation; no partial result was accepted.'})
        except (urllib.error.URLError, TimeoutError):
            self.send(503, {'error': 'The local model is unavailable or timed out. Start run.ps1 server in another terminal, then try again. Your text is still here.'})
        except (ValueError, KeyError, TypeError):
            self.send(422, {'error': 'Check that every turn has a speaker and text, groups are exact excerpts, and text plus context fits 4,000 characters. If those are correct, the model returned an invalid assessment; no partial result was accepted.'})
        except Exception:
            self.send(502, {'error': 'The assessment could not be validated. No partial result was accepted. Your input has been kept in this page.'})
        finally:
            LOCK.release()

def main():
    import argparse
    parser = argparse.ArgumentParser(description='Local input-first argument assessment UI')
    parser.add_argument('--port', type=int, default=8765)
    args = parser.parse_args()
    server = ThreadingHTTPServer(('127.0.0.1', args.port), Handler)
    print(f'Open http://127.0.0.1:{server.server_port} — Ctrl+C to stop.', flush=True)
    try:
        server.serve_forever()
    except KeyboardInterrupt:
        pass
    finally:
        server.server_close()

if __name__ == '__main__':
    main()
