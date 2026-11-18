# Companion 0.1.0-beta.24

Allow the observed normal heating-to-boil pause `3010/qH/000` in addition to PH/000. This corrects the actuator rejection reported during the November 18 test. The separate lid-warning and final-abort rules remain unchanged.

Use Bridge 0.5.1-beta.15, which also accepts the confirmed pH target after rest-end acknowledgment from Pi. Source `2910/qi/010` remains rejected. Card 0.7.0-beta.37 includes this Companion version.

Restart Home Assistant after updating. Automated control tests cover the added context and rejection of editor/unverified variants; live HA validation remains pending.
