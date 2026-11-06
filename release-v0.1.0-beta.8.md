# Nine-recipe display beta

The user supplied MySpeidel screenshots showing nine synchronized recipes (9 of 9 possible). The Companion now returns slots 0–8 according to the live recipe count in status field 8, rather than limiting the picker to the original four test recipes. Invalid counts/slots are rejected and stale entries beyond the live count are omitted.

Display Card 0.7.0-beta.10 presents the returned recipes in two columns, five on the left and up to four on the right, preserving numeric slot order, selected-recipe highlighting and HTML escaping. Companion 0.1.0-beta.8 supplies the expanded list.

Update both HACS components, restart HA for the Companion, then reload the browser for the Card. Keep existing configuration. The old Bridge 0.3.2-control.4-beta.1 still limits recipe navigation/selection to four recipes; use a Bridge containing the current upstream nine-slot implementation (included in the locally reviewed upstream 0.5.0 source). This HACS update does not update or restart the Bridge.

Validation: 32 Companion tests and Ruff passed; Card menu, program and bundle tests passed. No device commands were issued. Nine-recipe hardware validation of these new builds is pending. Rollback: redownload Card beta.9 / Companion beta.7 in HACS and restart/reload as above.