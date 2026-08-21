# Dormant Demonstration Booking Database

This directory is retained as upstream demonstration source and is not loaded by the active Ava runtime. Docker Compose exposes only the Pi backend; it does not start a booking sidecar, publish a booking port, or create a booking-data volume.

The SQLite implementation can seed local demonstration data from `seed_data/flights.jsonl` and `seed_data/pnrs.jsonl`. The fixtures are synthetic and must not be treated as production reservations or connected to real customer data.

Useful dormant sample PNRs include:

| PNR | Passenger | Flight | Status |
| --- | --- | --- | --- |
| `ABC123` | Jane Doe | AA123 | Scheduled |
| `DEF456` | John Smith | AA456 | Delayed |
| `GHI789` | Maria Garcia | AA789 | Cancelled due to weather |
| `JKL234` | Ahmed Khan | AA106 | Delayed |

Any manual use of this package is outside the supported Pi-only deployment and must use an explicitly chosen local database path.
