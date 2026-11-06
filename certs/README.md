# Aiven CA certificate folder

Put the CA certificate downloaded from the Aiven console here:

```text
certs/ca.pem
```

Then set this in `.env`:

```text
DB_SSL_CA=certs/ca.pem
```

The certificate is used with `ssl_verify_cert=True` and
`ssl_verify_identity=True`. Do not disable TLS verification to work around a
connection problem; download the correct `ca.pem` instead.

Certificate and key files in this folder are ignored by Git. The `.pem` file is
not a private key, but keeping it out of the repository makes it clear that each
environment downloads its own copy from Aiven.
