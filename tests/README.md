# CycleTLS Python Tests

## Quick start

```bash
uv sync --all-extras --dev
uv run pytest -m "not live" tests/        # offline, no external deps
uv run pytest -m live tests/               # hits https://tls.peet.ws by default
```

## Live tests against a local tlsfingerprint.com Docker instance

Live tests target `https://tls.peet.ws` by default. To run them against a
local instance of [Danny-Dasilva/tlsfingerprint.com](https://github.com/Danny-Dasilva/tlsfingerprint.com)
(the open-source server behind `tls.peet.ws`), bring up a local container and
point the suite at it via the `TLSFP_URL` env var. CI does this automatically;
locally:

```bash
# 1. Clone the server into a sibling directory
git clone https://github.com/Danny-Dasilva/tlsfingerprint.com.git
cd tlsfingerprint.com

# 2. Generate self-signed certs
mkdir -p certs
openssl req -x509 -newkey rsa:4096 \
    -keyout certs/key.pem -out certs/chain.pem \
    -sha256 -days 365 -nodes \
    -subj "/CN=localhost" \
    -addext "subjectAltName=IP:127.0.0.1,DNS:localhost"

# 3. Create config.json with DB logging disabled
jq '.log_to_db = false | .mongo_url = "" | .device = ""' \
    config.example.json > config.json

# 4. Boot it (binds 80/443; needs sudo on most distros)
docker compose up -d --build

# 5. Trust the cert and run the live tests against the local server
cd ../cycletls_python
cat /etc/ssl/certs/ca-certificates.crt \
    ../tlsfingerprint.com/certs/chain.pem > /tmp/combined-test-cas.crt
TLSFP_URL=https://localhost SSL_CERT_FILE=/tmp/combined-test-cas.crt \
    uv run pytest -v -m live tests/
```

If `TLSFP_URL` is unset, the suite falls back to `https://tls.peet.ws`.

## Markers

- `live` — exercises a real fingerprint server (`tls.peet.ws` or local).
- `blocking` — CI-critical fingerprint validation; subset of `live`.

## Connection reuse note

`tls.peet.ws` and the local tlsfingerprint.com container both close the TLS
connection after each response. The CycleTLS Go transport caches connections
globally, so a closed connection can leak into the next test as
`use of closed network connection`. Most fixtures default
`enable_connection_reuse=False` to avoid this.
