"""Publish one signed monitor heartbeat; Rekor proves publication, not execution."""
from datetime import datetime, timezone
from pathlib import Path
import argparse
import base64
import hashlib
import json
import urllib.error
import urllib.request

from cryptography.hazmat.primitives import hashes, serialization
from cryptography.hazmat.primitives.asymmetric import ec
from .external_anchor import LOG_KEY_ID, canonical, require, strict_json, verify_anchor


def digest(raw):
    return hashlib.sha256(raw).hexdigest()


def key_id(key):
    return digest(key.public_bytes(serialization.Encoding.DER,
                                  serialization.PublicFormat.SubjectPublicKeyInfo))


def validate(raw, expected_cadence, expected_key):
    payload = strict_json(raw)
    require(payload['schema'] == 'replay-monitor-heartbeat/1', 'wrong schema')
    require(digest(canonical(payload['cadence'])) == expected_cadence
            == payload['cadence_sha256'], 'unapproved cadence change')
    require(payload['cadence']['publisher_public_key_sha256'] == expected_key, 'unapproved publisher')
    times = []
    for field in ('intended_fire_time', 'actual_arrival_time'):
        value = datetime.fromisoformat(payload[field].replace('Z', '+00:00'))
        require(value.utcoffset().total_seconds() == 0, 'timestamps must be explicit UTC')
        times.append(value)
    require((times[1] - times[0]).total_seconds() == payload['lateness_seconds'],
            'lateness inconsistent with raw timestamps')
    require(payload['same_owner_principal'] is True and payload['independent_witnessing'] is False,
            'independence misrepresented')
    return payload


def publish(args):
    out = Path(args.output)
    out.mkdir(parents=True, exist_ok=False)
    observations = []
    def now():
        return datetime.now(timezone.utc).isoformat()
    def request(url, data=None):
        headers = {'User-Agent': 'replay-monitor-heartbeat/1', 'Accept': 'application/json'}
        if data is not None:
            headers['Content-Type'] = 'application/json'
        req = urllib.request.Request(url, data=data, headers=headers,
                                     method='GET' if data is None else 'POST')
        with urllib.request.urlopen(req, timeout=30) as response:
            raw = response.read()
            observations.append({'url': url, 'status': response.status, 'observed_at': now()})
            return raw
    try:
        raw = Path(args.heartbeat).read_bytes()
        validate(raw, args.cadence_sha256, args.publisher_key_sha256)
        private = serialization.load_pem_private_key(Path(args.key).read_bytes(), password=None)
        require(isinstance(private, ec.EllipticCurvePrivateKey), 'wrong signing key type')
        require(key_id(private.public_key()) == args.publisher_key_sha256, 'publisher key mismatch')
        public = private.public_key().public_bytes(serialization.Encoding.PEM,
                                                   serialization.PublicFormat.SubjectPublicKeyInfo)
        key_raw = request('https://rekor.sigstore.dev/api/v1/log/publicKey')
        if key_raw.startswith(b'"'):
            key_raw = strict_json(key_raw).encode()
        require(key_id(serialization.load_pem_public_key(key_raw)) == LOG_KEY_ID, 'unpinned service key')
        signature = private.sign(raw, ec.ECDSA(hashes.SHA256()))
        submission = {'kind': 'hashedrekord', 'apiVersion': '0.0.1', 'spec': {
            'data': {'hash': {'algorithm': 'sha256', 'value': digest(raw)}},
            'signature': {'content': base64.b64encode(signature).decode(),
                          'publicKey': {'content': base64.b64encode(public).decode()}}}}
        (out/'heartbeat.json').write_bytes(raw)
        (out/'author.pub').write_bytes(public)
        (out/'rekor-public-key.pem').write_bytes(key_raw)
        (out/'submission.json').write_bytes(canonical(submission))
        response = request('https://rekor.sigstore.dev/api/v1/log/entries', canonical(submission))
        (out/'rekor-entry.json').write_bytes(response)
        report = verify_anchor(raw, strict_json(response), key_raw)
        entry = next(iter(strict_json(response).values()))
        body = strict_json(base64.b64decode(entry['body'], validate=True))
        require(key_id(serialization.load_pem_public_key(base64.b64decode(
            body['spec']['signature']['publicKey']['content'], validate=True)))
            == args.publisher_key_sha256, 'returned publisher mismatch')
        readback = request(report['entry_url'])
        (out/'rekor-readback.json').write_bytes(readback)
        checked = verify_anchor(raw, strict_json(readback), key_raw)
        require(checked['uuid'] == report['uuid'], 'readback mismatch')
        result = {'schema': 'replay-monitor-heartbeat-publication/1',
                  'status': 'VERIFIED_PUBLICATION', 'heartbeat_sha256': digest(raw),
                  'rekor_index': report['log_index'], 'rekor_entry_url': report['entry_url'],
                  'rekor_integrated_time': report['integrated_time'],
                  'rekor_integrated_at': datetime.fromtimestamp(report['integrated_time'],
                                                               timezone.utc).isoformat(),
                  'readback_verified': True, 'publisher_public_key_sha256': args.publisher_key_sha256}
    except Exception as error:
        result = {'schema': 'replay-monitor-heartbeat-publication/1', 'status': 'INCONCLUSIVE',
                  'reason_code': 'HEARTBEAT_PUBLICATION_FAILED',
                  'detail': type(error).__name__ + ': ' + str(error)}
    result.update({'observations': observations, 'recorded_at_utc': now(),
                   'publication_proves_reported_arrival_time': False,
                   'same_owner_principal': True, 'independent_witnessing': False})
    (out/'publication.json').write_text(json.dumps(result, indent=2) + '\n')
    return result


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    for name in ('heartbeat','key','cadence-sha256','publisher-key-sha256','output'):
        parser.add_argument('--' + name, required=True)
    args = parser.parse_args()
    result = publish(args)
    print(json.dumps(result, indent=2))
    return 0 if result['status'] == 'VERIFIED_PUBLICATION' else 2


if __name__ == '__main__':
    raise SystemExit(main())
