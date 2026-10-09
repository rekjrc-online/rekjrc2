"""Outgoing webhook helpers: payload body, HMAC signing, SSRF-guarded POST."""
import hashlib
import hmac
import ipaddress
import json
import socket
import time
from urllib.parse import urlparse

import requests

TIMEOUT = (5, 10)          # connect, read (seconds)
MAX_RESPONSE_BYTES = 64 * 1024


class WebhookError(Exception):
    """Delivery failed; message is safe to store/show."""


def build_body(payload):
    device = payload.device
    return json.dumps({
        "event_id": payload.id,
        "device": {
            "uuid": str(device.uuid),
            "mac": device.mac,
            "name": device.name,
        },
        "name": payload.name,
        "value": payload.value,
        "racedriver_id": payload.racedriver_id,
        "created_at": payload.created_at.isoformat(),
    }, separators=(",", ":")).encode()


def sign(secret, timestamp, body):
    msg = f"{timestamp}.".encode() + body
    return hmac.new(secret.encode(), msg, hashlib.sha256).hexdigest()


def _assert_public_https(url):
    parts = urlparse(url)
    if parts.scheme != "https" or not parts.hostname:
        raise WebhookError("URL must be https")
    try:
        infos = socket.getaddrinfo(parts.hostname, parts.port or 443,
                                   proto=socket.IPPROTO_TCP)
    except socket.gaierror:
        raise WebhookError("DNS lookup failed")
    for info in infos:
        ip = ipaddress.ip_address(info[4][0])
        if not ip.is_global:
            raise WebhookError("URL resolves to a non-public address")


def post(endpoint, payload):
    """POST one payload. Returns HTTP status code on 2xx; raises WebhookError."""
    body = build_body(payload)
    ts = int(time.time())
    headers = {
        "Content-Type": "application/json",
        "User-Agent": "RekjRC-Webhooks/1",
        "X-Rekj-Event-Id": str(payload.id),
        "X-Rekj-Signature": f"t={ts},v1={sign(endpoint.secret, ts, body)}",
    }
    _assert_public_https(endpoint.url)
    try:
        resp = requests.post(
            endpoint.url, data=body, headers=headers,
            timeout=TIMEOUT, allow_redirects=False, stream=True)
    except requests.RequestException as e:
        raise WebhookError(f"{type(e).__name__}"[:200])
    try:
        resp.raw.read(MAX_RESPONSE_BYTES, decode_content=True)
    finally:
        resp.close()
    if not 200 <= resp.status_code < 300:
        err = WebhookError(f"HTTP {resp.status_code}")
        err.status_code = resp.status_code
        raise err
    return resp.status_code
