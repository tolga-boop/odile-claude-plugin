#!/usr/bin/env python3
"""Small stdlib Odile Direct client. Keys come only from a named environment variable."""
import argparse
import json
import os
import re
import sys
import urllib.error
import urllib.parse
import urllib.request
from pathlib import Path

API = 'https://api.odilelabs.com/a2a/v1'


def endpoint(biz, claim=False):
    if not re.fullmatch(r'[a-zA-Z0-9_-]{1,100}', biz):
        raise ValueError('Invalid business id')
    return API + ('/c/' if claim else '/b/') + biz


def validate(data, allowed):
    skill = data.get('skill')
    if skill not in allowed:
        raise ValueError('Skill is not advertised on this card')
    if skill not in ('take_message', 'check_availability', 'book', 'book_first_available'):
        raise ValueError('Helper supports structured tasks only')
    if skill != 'check_availability':
        for field in ('caller_name', 'callback_number', 'need'):
            if not isinstance(data.get(field), str) or not data[field].strip():
                raise ValueError('Missing ' + field)
        if not re.fullmatch(r'\+[1-9]\d{6,14}', data['callback_number']):
            raise ValueError('Callback must be E.164')
    for key, limit in [('caller_name', 100), ('on_behalf_of', 100), ('need', 500), ('service', 120)]:
        if key in data and (not isinstance(data[key], str) or len(data[key]) > limit):
            raise ValueError('Invalid ' + key)
    if skill == 'book' and (not isinstance(data.get('slot'), str) or not data['slot']):
        raise ValueError('Use an unchanged signed slot returned by availability')
    if skill == 'book_first_available':
        options = data.get('options')
        if not isinstance(options, list) or not 1 <= len(options) <= 5:
            raise ValueError('Use one to five date windows')


def request(url, payload=None, key_env=None):
    headers = {'Content-Type': 'application/json', 'User-Agent': 'odile-m2m-skill/1.0'}
    if key_env:
        key = os.environ.get(key_env)
        if not key:
            raise ValueError('Named key environment variable is unset')
        if any(ord(char) < 33 or ord(char) > 126 for char in key):
            raise ValueError('Named key variable contains invalid header characters')
        headers['Authorization'] = 'Bearer ' + key
    body = None if payload is None else json.dumps(payload).encode()
    if body is not None and len(body) > 8192:
        raise ValueError('Request exceeds 8 KB')
    req = urllib.request.Request(url, data=body, headers=headers)
    # No redirects: never forward an authorized request or key to another origin.
    class NoRedirect(urllib.request.HTTPRedirectHandler):
        def redirect_request(self, req, fp, code, msg, headers, newurl):
            return None
    try:
        with urllib.request.build_opener(NoRedirect).open(req, timeout=30) as response:
            return json.load(response)
    except urllib.error.HTTPError as error:
        raise ValueError('HTTP ' + str(error.code) + '; stop and inspect limits/configuration') from None
    except (urllib.error.URLError, TimeoutError):
        raise ValueError('Transport failed; outcome may be unknown. Do not repeat a write with a new ID') from None
    except ValueError:
        raise ValueError('Invalid transport response or request; no headers logged') from None


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('action', choices=['resolve', 'card', 'send'])
    parser.add_argument('target')
    parser.add_argument('--claim', action='store_true')
    parser.add_argument('--data-file', type=Path)
    parser.add_argument('--message-id')
    parser.add_argument('--allow-send', action='store_true')
    parser.add_argument('--key-env')
    args = parser.parse_args()
    if args.action == 'resolve':
        if not re.fullmatch(r'\+[1-9]\d{6,14}', args.target):
            parser.error('Use an E.164 number')
        result = request(API + '/resolve?' + urllib.parse.urlencode({'number': args.target}), key_env=args.key_env)
    else:
        base = endpoint(args.target, args.claim)
        card = request(base + '/agent-card.json', key_env=args.key_env)
        if args.action == 'card':
            result = card
        else:
            if not args.data_file or not args.message_id or len(args.message_id) > 160:
                parser.error('send needs --data-file and --message-id (1–160 chars)')
            data = json.loads(args.data_file.read_text())
            if not isinstance(data, dict):
                parser.error('data file must be a JSON object')
            validate(data, {s['id'] for s in card.get('skills', [])})
            if data['skill'] != 'check_availability' and not args.allow_send:
                parser.error('Message/booking needs authorized --allow-send')
            result = request(base, {'jsonrpc': '2.0', 'id': 1, 'method': 'SendMessage', 'params': {
                'message': {'messageId': args.message_id, 'role': 'ROLE_USER', 'parts': [
                    {'data': data, 'mediaType': 'application/json'}]}}}, args.key_env)
    print(json.dumps(result, indent=2))
    if args.action == 'send':
        state = result.get('result', {}).get('task', {}).get('status', {}).get('state')
        return 0 if state == 'TASK_STATE_COMPLETED' else 1
    return 0


if __name__ == '__main__':
    try:
        sys.exit(main())
    except ValueError as error:
        print(str(error), file=sys.stderr)
        sys.exit(1)
    except (KeyError, OSError):
        print('Request failed; inspect inputs, limits and outcome before retrying. No keys logged.', file=sys.stderr)
        sys.exit(1)
