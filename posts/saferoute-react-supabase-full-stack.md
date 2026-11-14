---
title: SafeRoute — A Full-Stack App on React and Supabase
date: 2026-08-30
updated: 2026-11-14
excerpt: How SafeRoute runs trip planning, live rides, chat and calls on React and Supabase, and the RLS tradeoff behind claiming a ride.
cover: posts/images/saferoute-react-supabase-full-stack.png
tags: react, supabase, full-stack, pwa, maps
---

# SafeRoute — A Full-Stack App on React and Supabase

[SafeRoute](https://github.com/abdulmanan69/saferoutes) is a road-trip planner and ride-booking app I built with React 19, Vite 7 and Supabase. You compare up to three real driving routes between two cities, each with a risk score, then run the trip with live GPS. A Rides section lets a customer request a ride and a driver accept it, with live tracking, chat and voice calls. Screenshots are on the [project page](/projects/saferoutes/).

## The problem

Nearly everything here is data that belongs to someone. Trips are per user, admins see all of it, and a ride is shared by two people who each need to see it change the moment the other acts.

I also didn't want my own server or paid map APIs. The README lists "Free APIs (no keys, already wired)" and the push guide says "Everything runs on Supabase's free tier — no other service." So the question was how much of a two-sided app Supabase and browser APIs can carry alone.

## How it is built

The browser talks to Supabase directly with the anon key: Auth for accounts, Postgres with row-level security for data, and Realtime for live ride updates, chat and call signaling. Leaflet draws OpenStreetMap tiles, OSRM provides routes, Open-Meteo handles city search and weather, BigDataCloud turns GPS into place names and Wikipedia supplies photos, all without keys. The only server-side code is one Edge Function, `supabase/functions/push/index.ts`, which three Database Webhooks call to send Web Push.

## Letting Postgres do the bookkeeping

`supabase/schema.sql` defines seven tables, all with RLS enabled.

**The admin check is a function.** A rule like *own rows, or any row for an admin* needs the caller's role from `profiles`, and a policy on `profiles` that queries `profiles` refers back to itself. So the lookup lives in `is_admin()`, a `SECURITY DEFINER` function, under the comment "Admin check function (avoids circular RLS reference)".

**Signup side effects live in a trigger.** `handle_new_user()` runs after each insert into `auth.users` and creates the profile and settings rows, taking the name from sign-up metadata or the email. No React code path has to remember them.

**The file can be run again.** It uses `CREATE TABLE IF NOT EXISTS` and `ADD COLUMN IF NOT EXISTS`, drops each policy before recreating it, and wraps the Realtime publication changes so a duplicate is ignored. The README calls it "idempotent — safe to re-run anytime".

The outfit closet, tourism itinerary and pre-trip checklist are not in the database. They sit in `localStorage` under per-user keys, so they stay in one browser.

## Routing without an API key

`getRoutes` tries two public OSRM hosts in order and, if both fail, returns an estimate instead of an error ([src/utils/geo.js](https://github.com/abdulmanan69/saferoutes/blob/cacec45a9a035fa3bea0cdcd6b3c15316544b988/src/utils/geo.js)):

```js
// ...
    for (const host of OSRM_HOSTS) {
        try {
            const res = await fetch(host + path);
            if (!res.ok) continue;
            const data = await res.json();
            if (data.code !== 'Ok' || !data.routes?.length) continue;
            return data.routes.map(r => {
// ...
        } catch {
            // try next host
        }
    }

    // Offline / all hosts down: estimate from the real geocoded coordinates.
    const dist = haversineKm(start, end) * 1.3; // road-distance factor
    return [{
        distanceKm: dist,
        durationHours: dist / 60,
        avgSpeed: 60,
        coordinates: [[start.lat, start.lng], [end.lat, end.lng]],
        estimated: true
    }];
// ...
```

That is straight-line distance times 1.3 at 60 km/h. The planner checks the flag and warns "Routing service unavailable — showing a straight-line estimate." The ride fare quote (Rs. 200 base plus Rs. 45 per km) uses the same function, so it gets marked "(estimated)" too.

## What the risk score actually is

`computeRisk` in `src/pages/NewTrip.jsx` starts at 12 and adds points for the weather, season, difficulty and driver profile chosen in the form: Snowy adds 28, Expert 22, Winter 15, an aggressive driver 8. Then the route: 10 if OSRM's average speed is under 45 km/h (4 under 60), 6 over 500 km (3 over 300), and 4 per position after the first route. The result is clamped to 5 to 92; under 20 is Low, under 45 Medium.

So it is a heuristic, shown as a percentage and a badge with no breakdown. The weather is what you select, not the live forecast, and road type and travel preference don't affect it.

## Rides on Realtime

A customer inserts a `rides` row with status `requested`. Every signed-in client subscribes to `rides` through Realtime, so drivers see it without refreshing. Accepting is one filtered update ([src/pages/Rides.jsx](https://github.com/abdulmanan69/saferoutes/blob/cacec45a9a035fa3bea0cdcd6b3c15316544b988/src/pages/Rides.jsx)):

```js
    const acceptRide = async (ride) => {
        ensureNotifyPermission();
        const { error } = await supabase.from('rides')
            .update({ driver_id: user.id, status: 'accepted', updated_at: new Date().toISOString() })
            .eq('id', ride.id).eq('status', 'requested');
        if (error) return toast.error(error.message);
        setRides(prev => prev.map(r => r.id === ride.id ? { ...r, driver_id: user.id, status: 'accepted' } : r));
// ...
```

In the [first version](https://github.com/abdulmanan69/saferoutes/blob/de0459fbbc6795a128c61dec1718a1cd479739d5/src/pages/Rides.jsx) the `.eq('status', 'requested')` line carried the comment `// race-safe`: if two drivers tap Accept together, only one update finds the ride still open. But the client checks only for an error, not whether a row changed, so the losing driver still gets the success toast and the ride marked as theirs locally.

Once accepted, the driver's browser writes `driver_lat` and `driver_lng` to the ride at most every 5 seconds, and the customer's map follows through the same subscription. Chat is a `ride_messages` table only the ride's customer and driver can write to. Calls are WebRTC audio, signaled over a Realtime broadcast channel per ride. With two public STUN servers and no TURN server configured, calls need a direct path between devices.

## The tradeoff: open requests are open

The comment in [supabase/schema.sql](https://github.com/abdulmanan69/saferoutes/blob/cacec45a9a035fa3bea0cdcd6b3c15316544b988/supabase/schema.sql) states the choice:

> Rides policies: open requests are visible to any signed-in user (drivers browse them); accepted/completed rides only to their customer, driver, or an admin.

```sql
CREATE POLICY "rides_select" ON public.rides FOR SELECT
    USING (status = 'requested' OR customer_id = auth.uid() OR driver_id = auth.uid() OR public.is_admin());
CREATE POLICY "rides_insert" ON public.rides FOR INSERT
    WITH CHECK (customer_id = auth.uid());
CREATE POLICY "rides_update" ON public.rides FOR UPDATE
    USING (status = 'requested' OR customer_id = auth.uid() OR driver_id = auth.uid() OR public.is_admin());
```

`status = 'requested'` doesn't ask who is reading. Being a driver is `profiles.user_type`, which these policies never check, so customers can read every open request's pickup, destination, coordinates and fare just as drivers can. The same clause on UPDATE is what lets a driver write their id onto a row they don't own yet, and while a ride is open it is equally permissive for everyone.

What it buys: no accept endpoint and no server code. Drivers browse with a plain select, claim with one update, and an accepted ride drops out of everyone else's view. The stricter version would be a database function that checks `user_type` and only sets `driver_id` and `status`.

## What the commit history shows

There are 13 commits from 20 June to 5 July 2026. The Supabase backend came second (a8b858e), before any pages, and its schema already had the `rides` and `ride_messages` tables that nothing used until de0459f on 3 July.

The clearest reversal is in the last commit, cacec45. In de0459f the call engine was a `useVoiceCall` hook inside `Rides.jsx` that tore down its channels on unmount, so calls rang only on the Rides page. cacec45 moved it and the ride subscription into a `RideLiveProvider` wrapping every route, with the header comment "ring EVERYWHERE in the app — not just on the Rides page."

That commit also added a browser `Notification` when the tab is hidden and Web Push when the app is closed, and dropped the hint "Pay the shown fare on arrival. Cash, simple." The app takes no payments; the README calls subscription billing "a demo".

## Smaller things worth stating plainly

- **Voice guidance** is `speechSynthesis` announcing the start, each quarter of the route and arrival within about 1.5 km. It is not turn-by-turn.
- **Smart Outfit** runs no model. `src/utils/outfitModel.js` notes the original scikit-learn tree learned rule-generated labels, "so the fitted tree reproduces those exact rules", and codes the rules directly.
- **The PWA** caches the app shell only. The service worker skips cross-origin requests ("Never cache API traffic"), so offline means UI without routes or weather.

## Running your own copy

- Create a Supabase project, run `supabase/schema.sql`, and set `VITE_SUPABASE_URL` and `VITE_SUPABASE_ANON_KEY` in `.env`.
- Background push also needs VAPID keys, the Edge Function and three webhooks; `docs/PUSH-SETUP.md` has the steps.

If you want something like this built, [start a conversation](/#contact).
