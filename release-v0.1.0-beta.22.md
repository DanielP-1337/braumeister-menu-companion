# Companion 0.1.0-beta.22

Check the current program screen and pause indicator before checking pump/heater flags. A screen that changed no longer produces a misleading actuator rejection from a fallback rule.

Program-context and actuator rejection messages now include the requested action and the observed screen, actuator flags, and pause indicator. No credentials or recipe contents are included.

Investigation: the recorded hop acknowledgment (3080/qH/010 to 3070/qH/000) and brewing-complete acknowledgment (3450/ph/010 to 3510/ph/000) already match supported rules. The historical refusal before Whirlpool remains unconfirmed because rejected Companion requests do not reach the Bridge control log. These diagnostics help identify the next occurrence; no additional device permissions are enabled.

Use with Display Card 0.7.0-beta.35, which clears obsolete action feedback on context changes. Restart Home Assistant after updating the Companion. No Bridge or integration update is introduced by this release.

Validation: Companion regression tests cover rejection priority, observed-context diagnostics, and rejection without sending a control command.
