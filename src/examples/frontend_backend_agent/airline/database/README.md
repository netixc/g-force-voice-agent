# Demonstration Booking Database

The booking sidecar uses SQLite data seeded from `seed_data/flights.jsonl` and `seed_data/pnrs.jsonl`. It supports the prototype's new flight searches, new bookings, and PNR status checks.

Useful sample PNRs include:

| PNR | Passenger | Flight | Status |
| --- | --- | --- | --- |
| `ABC123` | Jane Doe | AA123 | Scheduled |
| `DEF456` | John Smith | AA456 | Delayed |
| `GHI789` | Maria Garcia | AA789 | Cancelled due to weather |
| `JKL234` | Ahmed Khan | AA106 | Delayed |

The database is demonstration data, not a production reservation system. Runtime state is stored in the Docker volume configured by `BOOKING_DATA_VOLUME`.

Reset project-owned booking data with care:

```bash
docker compose down
docker volume rm g-force-voice-agent_booking_data
docker compose up -d
```

Do not remove the volume if it points to a shared or existing deployment database.
