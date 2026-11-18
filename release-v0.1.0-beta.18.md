# Menu Companion 0.1.0-beta.18

Expose three narrowly scoped program actions:

- `acknowledge_hop_addition`: 3080/qH/010.
- `confirm_whirlpool`: 3510/ph/000.
- `finish_brewing`: 3610/ph/000.

Requires Bridge 0.5.1-beta.10 and Display Card 0.7.0-beta.28. Wrong states,
actuator flags, indicators, stale telemetry and non-administrator requests are
rejected. These are Select/key-4 acknowledgments, not generic Resume or Cancel.
Install while idle and restart Home Assistant as requested by HACS.
