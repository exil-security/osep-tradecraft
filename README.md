# OSEP Tools

## Install

### Dependencies

```bash
sudo apt install mingw-w64 mono-devel
```

- mono csharp
- jinja

- [x] dll proxy

### OpenSSL

```bash
openssl req -new -x509 -nodes -days 365 -subj "/CN=OSEP" -out cert.pem -keyout key.pem
```