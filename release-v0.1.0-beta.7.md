# Braumeister Local Menu 0.1.0-beta.7

Companion test release paired with Display Card 0.7.0-beta.9. Control implementation and service metadata are unchanged from beta.6: request_program_pause accepts state 2300, flags Ph, indicator 000. This release provides an explicit matching HACS version for the HA test.

Use Bridge 0.3.2-control.4-beta.1. Preserve configuration and restart HA after updating. Then update the Card and reload the browser. No device commands or hardware validation were performed. Python adapter tests were not rerun: pytest is missing in the local environment. Card validation: seven Node scripts passed. Rollback by redownloading beta.6 and restarting HA.