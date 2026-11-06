# Restore recipe list after dashboard reload

Display Card 0.7.0-beta.11 with Companion 0.1.0-beta.9 reads the existing Bridge recipe snapshot when HA reports the recipe-selection screen. Previously names were populated only by successful navigation replies, so a dashboard reload or opening recipe selection at the appliance could leave the list empty.

The new response-only get_recipe_picker service reads GET /api/status only, checks administrator access and status freshness, and never queues device commands. Reads are limited to at most once per five seconds on incoming HA updates. Leaving the screen or starting a menu action invalidates an older pending read. There is no faster integration polling in this release: ordinary HA updates still follow the configured scan interval (30 seconds by default).

The nine-recipe display has now been reported working on hardware. The separate HTTP 409 navigation report remains unresolved pending confirmation of the installed Bridge version. The older 0.3.2-control.4-beta.1 rejects nine-recipe navigation; upstream 0.5.0 supports it. No Bridge guards are bypassed.

Update both HACS components, restart HA for Companion, then reload the browser. Local validation: 34 Companion tests and Ruff; Card regression tests include cold-load read-only fetching, throttling and late-response rejection. No device commands were sent. Hardware validation of this fix is pending.