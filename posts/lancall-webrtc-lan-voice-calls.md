---
title: LanCall — WebRTC Voice Calls Over Your LAN
date: 2026-08-20
excerpt: Voice calls between devices on the same network with no cloud service in the middle. A small Python server does the introductions.
cover: posts/images/lancall-webrtc-lan-voice-calls.png
tags: webrtc, javascript, python, networking, privacy
---

# LanCall — WebRTC Voice Calls Over Your LAN

Two people sitting in the same building, on the same Wi-Fi, talk to each other by
sending their voices to a data centre in another country and back. That's normal
now, and it's absurd — it needs internet, it needs an account, and a third party
hears everything.

**[LanCall](https://github.com/abdulmanan69/lancall)** is voice calling that stays
on your LAN. Devices on the same network call each other directly using WebRTC,
with no external servers involved.

## How a "serverless" call still needs a server

The audio is peer-to-peer. Getting the two peers to find each other is not.

Two pieces run on one machine on the network:

1. **An HTTPS server** that serves the web app — HTML, CSS, JavaScript
2. **A WebSocket signalling server** that carries the introduction between peers

```
[Device A] ----\
                \
                 [Signaling Server] <---> [HTTPS Server]
                /
[Device B] ----/
```

The sequence:

1. Both devices connect to the signalling server and exchange connection details —
   session descriptions and network candidates
2. Once they know how to reach each other, they open a direct P2P connection
3. **Voice data flows straight between the devices**, not through the server

The signalling server handles a few kilobytes of setup, then does nothing for the
rest of the call. If it crashed mid-conversation, the conversation would continue.

That's the thing WebRTC tutorials bury: signalling and media are separate problems.
The server you need is small, dumb and only involved at the start.

## HTTPS isn't optional, and that's the fiddly bit

Browsers won't give a page microphone access over plain HTTP, and WebRTC needs a
secure context. On the public internet you get a certificate from Let's Encrypt.
On a LAN, with devices addressed as `192.168.1.x`, there's no domain to certify.

So LanCall serves over **HTTPS and WSS using self-signed certificates**, generated
at setup. The cost is the browser warning on first connect — you click through it
once per device. The alternative is no microphone access at all.

If you're deploying something like this for a team, the tidier route is installing
your own certificate authority on the devices. For a small network, clicking
through once is fine.

## Cross-platform for free

Windows, macOS, Linux, Android and iOS — anything with a modern browser. There's
no app to install on the phones, no store approval, no build per platform. One web
app, every device on the network.

This is the part people forget when reaching for Electron or a native app: a web
page served from a laptop on the LAN already runs everywhere, and the browser
provides the microphone, the codecs, the echo cancellation and the encryption.

## Getting it running

Prerequisites: Python 3.6 or newer, and pip.

**Windows**

```cmd
start_server.bat
```

**Linux / macOS**

```bash
python start_server.py
```

Then open the printed HTTPS address on any device on the same network, accept the
certificate warning once, and call.

## Where it's genuinely useful

An office where the internet is down but the network is up. A warehouse floor. A
workshop. Any situation where two people need voice contact and a cloud dependency
is either unavailable or unwelcome — the audio never leaves the building, so
there's no recording in someone else's account and no bill.

It also makes a good way to actually learn WebRTC. On the open internet you also
need STUN and TURN servers to punch through NATs, and that complexity hides the
core idea. On a LAN, peers can reach each other directly, so the protocol shows
through clearly.

## Related reading

If the privacy-first, no-cloud thread is what interests you, the same idea shows up
in [ToolForge](/blog/toolforge-browser-pdf-tools/) — 93 document tools with no
uploads — and in
[LeadSlicer](/blog/leadslicer-split-csv-excel-files/) for spreadsheet work.

Source: [github.com/abdulmanan69/lancall](https://github.com/abdulmanan69/lancall).
Questions, or want something like it for your office? [Message me](/#contact).
