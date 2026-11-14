---
title: LanCall — WebRTC Voice Calls Over Your LAN
date: 2026-08-20
updated: 2026-11-15
excerpt: How LanCall runs browser-to-browser voice calls on a LAN with WebRTC, a small Python signalling server and self-signed HTTPS.
cover: posts/images/lancall-webrtc-lan-voice-calls.png
tags: webrtc, javascript, python, networking, privacy
---

# LanCall — WebRTC Voice Calls Over Your LAN

[LanCall](https://github.com/abdulmanan69/lancall) lets devices on the same network call each other from a browser. One machine runs a 74-line HTTPS file server and a 259-line WebSocket signalling server, both in Python. Every other device just opens a URL, and the audio goes directly between the two browsers. There's also a [project page](/projects/lancall/). This post covers how it works, including the parts of the code I'd change.

## The problem

The README states the goal: the app "allows users on the same network to make voice calls directly between devices without any external servers."

WebRTC can carry audio peer to peer, but two things stand in the way. The browsers have to swap session descriptions and network candidates before they can connect, and something has to carry those messages. And browsers only hand the microphone to secure pages; the error text in `app.js` says "browsers only allow media device access on HTTPS or localhost." A phone loading the page from a laptop's LAN IP is not localhost, so it needs HTTPS.

## What actually runs

- `https_server.py` serves the web app (`index.html`, `app.js` and `style.css`) on port 8443 with the standard library's `http.server`, wrapped in TLS. It refuses to start without a certificate.
- `signaling_server.py` is an asyncio WebSocket server on port 8765, built on the `websockets` package, using the same certificate.
- `start_server.py` (or `start_server.bat` on Windows) installs pyOpenSSL and websockets, runs `generate_cert.py` if there is no certificate yet, and starts both servers.

The README's diagram draws a link between the two servers. The code has none. They are separate processes that share only the certificate files, and `start_server.py` just launches both and terminates one if the other exits. The browser ties them together: it loads the page from port 8443, then builds its WebSocket URL from the page's own hostname and port 8765, choosing `wss://` whenever the page is HTTPS.

## The signalling server

The server keeps one dictionary, `connected_clients`, mapping each open socket to an `id` and a display `name`. Each browser invents its id on page load and a default name from its user agent, such as "Windows PC" plus a random number, and sends both in a `register` message. Whenever someone registers, renames or disconnects, the server broadcasts the full list to everyone as `client_list`. That broadcast is the whole presence system.

Everything else is relaying. `offer`, `answer`, `ice_candidate` and `hangup` messages carry a `target_id`, and the server forwards them to the matching socket:

```python
        elif msg_type == "offer":
            target_id = data.get("target_id")
            sender_info = connected_clients.get(websocket, {"id": "unknown", "name": "unknown"})
            # ...
            if target_id:
                # Find the target websocket
                target_socket = None
                for ws, client_info in connected_clients.items():
                    if client_info["id"] == target_id:
                        target_socket = ws
                        break
                        
                if target_socket:
                    # Add sender info to the message
                    data["sender_id"] = sender_info["id"]
                    data["sender_name"] = sender_info["name"]
                    try:
                        await target_socket.send(json.dumps(data))
                    # ...
```

From [signaling_server.py](https://github.com/abdulmanan69/lancall/blob/bea8e73e710c06f5b92ca993b836d76c65000784/signaling_server.py#L115-L136). The server writes `sender_id` and `sender_name` from its own registry, so the callee sees who is calling according to the server, not according to the caller's message. The other three branches are near-copies of this one and could be a single forwarding function.

## A call, end to end

1. The caller clicks Call next to a peer. `startCall()` runs a microphone test, then requests audio with `echoCancellation`, `noiseSuppression` and `autoGainControl` on.
2. It creates an `RTCPeerConnection`, adds the track, and sends an offer through the signalling server. ICE candidates follow the same route.
3. The callee gets an incoming-call screen and a ringtone made with the Web Audio API: an 800 Hz sine wave switched on and off every two seconds.
4. On Accept, the callee opens its microphone, applies the offer and sends back an answer.
5. Once ICE connects, audio flows browser to browser. No TURN server is configured, so nothing relays the media.

Hanging up is also a signalling message, and each side also ends the call if its connection state turns `disconnected` or `failed`. The page hangs up by itself when it becomes hidden ("Send hangup if in a call when leaving the page"), so switching tabs, or apps on a phone, ends the call.

Nothing in `app.js` ends a call when the WebSocket closes; `onclose` only schedules a reconnect. If the signalling server dies mid-call, the audio keeps going, but a hangup can't be delivered, and the other side only notices through its connection state.

## The tradeoff: self-signed certificates

A LAN address like `192.168.1.x` has no domain name to get a public certificate for, but the microphone needs HTTPS. LanCall makes its own certificate on first run:

```python
    # Create a key pair
    key = crypto.PKey()
    key.generate_key(crypto.TYPE_RSA, 2048)

    # Create a self-signed cert
    cert = crypto.X509()
    # ...
    cert.get_subject().CN = get_local_ip()
    cert.set_serial_number(1000)
    cert.gmtime_adj_notBefore(0)
    cert.gmtime_adj_notAfter(365*24*60*60)  # 1 year
    cert.set_issuer(cert.get_subject())
    cert.set_pubkey(key)
    cert.sign(key, 'sha256')
```

From [generate_cert.py](https://github.com/abdulmanan69/lancall/blob/bea8e73e710c06f5b92ca993b836d76c65000784/generate_cert.py#L24-L41). The certificate is its own issuer, so no browser trusts it. The README is upfront about the cost:

> Browsers will show security warnings - this is expected for self-signed certificates

`start_server.py` repeats it at launch: "Click 'Advanced' and 'Proceed to ...' to continue". Every device has to click through that warning before it can call. In return there is no domain or DNS to set up, and no key is shared between installs: `.gitignore` excludes `*.crt` and `*.key`, so each one generates its own.

The code also shows the limits:

- The common name is whatever LAN IP the machine had at generation time. `get_local_ip()` finds it by pointing a UDP socket at 8.8.8.8 ("doesn't actually send data", a copy of the helper notes) and falls back to `127.0.0.1` if that fails.
- The start scripts only check that the files exist, never the IP or the one-year expiry. The README's fix for certificate trouble is to "delete `server.crt` and `server.key` files and restart the server".

For a team, I'd install a local certificate authority on each device instead. LanCall doesn't do that.

## Not quite "without any external servers"

That README line overstates it. In [app.js](https://github.com/abdulmanan69/lancall/blob/bea8e73e710c06f5b92ca993b836d76c65000784/app.js#L357-L364) the peer connection is configured with five public STUN servers (two of Google's, plus stunprotocol.org, voiparound.com and voipbuster.com), which the browser contacts while gathering candidates when the network has internet access. `index.html` also loads `adapter-latest.js` from webrtc.github.io and Tailwind from cdn.tailwindcss.com. The audio still goes device to device, but for a strictly offline LAN the STUN list should go and those scripts should be served locally.

## Rough edges

- ICE candidates that arrive while the callee is still ringing are dropped: `handleIceCandidate()` only adds one `if (peerConnection)`, and the callee creates its peer connection after Accept. They should be queued.
- Every call start or accept shows an alert, "Microphone access test successful!", and opens the microphone twice.
- The reconnect comment says "Exponential backoff", but `2000 * reconnectAttempts` is linear, and after five tries it gives up without telling the user.

## What the history shows

Four commits. All of the code, nine files and 2,249 lines, arrived on 1 October 2025 in ce49093, "Initial commit: LAN Voice Call application with HTTPS and WebSocket signaling servers". The README (deeb9e7) and MIT license (d93c526) followed the next day, and no code has changed since. Earlier iteration survives only in comments: the WebSocket block is labelled "Solution 3", the error handlers mention "we removed the status elements", and a server comment mentions "websockets v15".

## Running it

The README says Python 3.6, but `signaling_server.py` calls `asyncio.run()`, which arrived in 3.7, so use a current Python 3. Run `start_server.bat` on Windows or `python start_server.py` elsewhere, open `https://<server-ip>:8443` on each device, accept the certificate warning, allow the microphone and click Call. Ports 8443 and 8765 must not be blocked by the server's firewall.

The same no-cloud idea runs through [ToolForge](/blog/toolforge-browser-pdf-tools/), browser tools with no uploads, and [LeadSlicer](/blog/leadslicer-split-csv-excel-files/) for spreadsheet work. Questions, or want something like it for your office? [Message me](/#contact).
