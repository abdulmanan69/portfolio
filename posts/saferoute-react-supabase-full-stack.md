---
title: SafeRoute — A Full-Stack App on React and Supabase
date: 2026-08-30
excerpt: Real driving routes, safety scoring, live GPS and a ride marketplace, built on React 19, Supabase RLS and free APIs that need no keys.
cover: posts/images/saferoute-react-supabase-full-stack.png
tags: react, supabase, full-stack, pwa, maps
---

# SafeRoute — A Full-Stack App on React and Supabase

Most of my tools deliberately have no backend. **SafeRoute** is the opposite: a
full-stack travel platform where accounts, roles, bookings and admin broadcasts
all have to be real.

It plans road trips on **real driving routes** with automatic **safety-risk
scoring**, runs **live GPS journeys** with voice guidance, books rides in a
customer/driver marketplace, explores any city in the world with real photos, gives
AI outfit advice from live weather, and is managed from an admin panel — installable
as a **PWA** on your phone.

Here's what I'd tell anyone building something similar.

## Supabase did the part I didn't want to build

**Backend:** Supabase — PostgreSQL, Auth and Row-Level Security.

Auth alone is weeks of work done properly: sign-up, email confirmation, password
reset that actually sends mail, sessions that survive a refresh. Supabase gives you
all of it, and — this is the part people underrate — it gives you Postgres
underneath rather than a proprietary document store you'll fight later.

Two decisions that paid off:

**RLS is the authorisation layer, not the client.** A driver must not read another
driver's bookings. If that rule lives in React, it holds until someone opens the
network tab. In a row-level security policy it holds everywhere, including from a
raw API call. The client stops being a trust boundary.

**Signup side effects belong in the database.** A new user needs a profile row and
a settings row. Doing that in the app means every signup path has to remember, and
a failed second insert leaves a half-created user. A database trigger creates both
rows atomically — one place, no drift.

The schema lives in `supabase/schema.sql` and is **idempotent**, so it's safe to
re-run against a fresh project any time. A migration you're afraid to run twice is
a migration you'll avoid running at all.

## The frontend

**React 19 · Vite 7 · React Router 7 · Leaflet / React-Leaflet · ESLint 9.**

Vite is the reason the project stayed pleasant. A dev server that starts instantly
and hot-reloads a map-heavy page in under a second changes how much you're willing
to experiment.

Leaflet over a commercial map SDK was a cost decision that turned into a design
one: OpenStreetMap tiles are free and unlimited, and Leaflet's plainness meant the
map inherited the app's dark-violet UI instead of fighting it.

## Every API is free, and none of them need a key

This was a hard constraint: anyone should be able to clone the repo and have a
working app without signing up for anything.

| Purpose | Service |
|---|---|
| City search & geocoding | Open-Meteo Geocoding |
| Live weather + forecast | Open-Meteo Forecast |
| Real driving routes | OSRM (two public hosts + offline estimate fallback) |
| Map tiles | OpenStreetMap |
| Place photos & nearby landmarks | Wikipedia REST + geosearch |
| GPS to place name | BigDataCloud reverse geocoding |
| Voice guidance | Browser SpeechSynthesis |
| Live position | Browser Geolocation |

Note the routing row: **two public OSRM hosts plus an offline estimate fallback.**
Free public endpoints go down, rate-limit and occasionally return nonsense. A
trip planner that shows an error instead of a route is useless, so it tries the
second host, and if both are gone it falls back to a distance-and-speed estimate
and says so. Degrade, don't die.

The last two rows are worth noticing too — voice guidance and live position are
*browser* APIs. The turn-by-turn voice costs nothing and needs no service at all.

## What "safety-risk scoring" means

The route comes back as real road geometry. Scoring combines what's knowable for
free — conditions along the way, time of day, weather at the destination, the
character of the road segments — into a number a person can act on.

The interesting problem isn't the maths, it's the honesty: a score that looks
authoritative but is guessing is worse than no score. So the app shows what fed
the number rather than presenting a bare 7/10.

## PWA, because this runs in a car

Installable on Android, iOS and desktop. On a phone mount, a browser tab with an
address bar is the wrong shape — and a PWA also keeps the shell cached, which
matters on a patchy signal between towns.

## What I'd keep from this build

- **Push authorisation into the database.** RLS policies are the cheapest real
  security you will ever write.
- **Make the schema idempotent** from day one.
- **Give every external call a fallback** before you ship, not after the first
  outage.
- **Free APIs are a real stack**, not a prototype stack — as long as you plan for
  them being down.

Source: [github.com/abdulmanan69/saferoutes](https://github.com/abdulmanan69/saferoutes).
If you want something like this built — React front, Supabase back, deployed and
live — [start a conversation](/#contact).
