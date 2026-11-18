# Menu Companion 0.1.0-beta.17

Expose rest-end acknowledgment, malt-pipe-removal confirmation, and boil start for
the recorded 2910 → 2930 → 2960 → 3010 transitions. Add pause/abort requests in
the three prompt states; hardware testing of those new stop contexts is pending.
Other Resume contexts and boil editor commands remain unsupported.

Requires Bridge 0.5.1-beta.9 and Display Card 0.7.0-beta.27. Existing administrator,
freshness, device-context and Bridge policy checks remain in place. Install and
restart Home Assistant after the running brew has finished.

The observed lid-removal acknowledgment (`3010/qH/0DT` → `3010/qH/00T`) is now a separate guarded confirmation, not generic Resume. Cancel and Up/Down at that warning remain unverified and unavailable.
