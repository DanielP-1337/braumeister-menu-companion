# Braumeister Local Menu

Local/unreleased program-control work is described in
[the preparation notes](docs/program-control-preparation.md). It needs the
matching experimental Bridge and Card branches and is not part of a published
HACS version yet.

**Disclaimer:** This project is an independent open-source development and is not affiliated with, funded by, or endorsed by Speidel Tank- und Behälterbau GmbH or any of its affiliates. "Braumeister" and "MySpeidel" are trademarks of their respective owners.

This Home Assistant integration connects the [Braumeister Display Card](https://github.com/DanielP-1337/braumeister-display-card) to the [upstream Braumeister Bridge](https://github.com/omphteliba/ha-speidel-braumeister/tree/main/braumeister_bridge). It requires a bridge build that includes the local control API from [Bridge PR #20](https://github.com/omphteliba/ha-speidel-braumeister/pull/20) and Display Card v0.7.0-beta.1 or later.

1. In HACS, open **Custom repositories**, add this repository as **Integration**, and download the beta.
2. With the Bridge running and the Braumeister online, open the Home Assistant Terminal or connect to Home Assistant over SSH. Run the command in that shell, where `127.0.0.1` can reach the Bridge.

   ```sh
   curl -fsS --max-time 5 http://127.0.0.1:8642/api/status |\
     jq -r '.devices[].device_id'
   ```

   The command prints one ID per device known to the Bridge. If it prints nothing, wait for the Braumeister to send a status update and try again. If it lists multiple IDs, use the one for the Braumeister whose entities you mapped in the card.
3. In Home Assistant's `configuration.yaml`, add the following block at the top level. Replace the placeholder with the ID printed by the command and keep the quotes.

   ```yaml
   braumeister_menu:
     device_id: "YOUR_BRIDGE_DEVICE_ID"
   ```

4. Check the configuration and restart Home Assistant Core. Under **Developer tools → Actions**, search for `braumeister_menu.navigate` to verify that the integration loaded.
5. Set `menu_control: true` in the card YAML and enable `control_enabled` in the Bridge for testing.
6. As an HA administrator, open Settings on the dashboard and verify the screen on the device. Use Cancel to return to the main menu.

The integration calls the Bridge on `127.0.0.1:8642` from HA Core and waits for the result. It submits each action once and requires fresh device status with both actuators off. Recipe picker highlights refresh after confirmed card actions.

The dashboard control path was tested end to end on a Braumeister 20L Plus. Menu navigation also worked while the browser was signed out of MySpeidel.

Testing Home Assistant and the Bridge with internet access blocked is still pending. The tested Bridge control path delivers a local key only after a matching poll receives the expected MySpeidel acknowledgment. A fully offline LAN with Home Assistant, the Bridge, and the Braumeister is a potential target. See the upstream discussion in [Bridge PR #20](https://github.com/omphteliba/ha-speidel-braumeister/pull/20).

## Live test coverage for locales and units

Live testing with MySpeidel and a physical Braumeister has so far used a German MySpeidel account, Celsius (°C), Plato (°P), and German date and time formats.

- **MySpeidel account settings:** English, Fahrenheit (°F), and Specific Gravity (SG) have not been tested against the live API. Whether these settings change API values, units, field formats, or only the portal display is unknown. Test each setting separately against the German / °C / °P baseline, then test them together.
- **System and browser locale:** Live tests with non-German system or browser languages and date/time formats, such as en-US, are pending. Test language and formatting separately while keeping the time zone fixed. Include 12-hour and 24-hour display, date rollover, and RTC monitoring where applicable.

The Companion uses the Bridge API. Verify that it still identifies the device and reports the outcome of supported menu actions under these settings.

## Observed on the device: Water filled?

After choosing a recipe on the Braumeister 20L Plus (firmware 1.1.27), the device shows its water confirmation screen. The two middle arrow keys change a displayed time value in 30-minute steps. Its meaning, the effect of confirming at zero or at a positive value, and the timing of pump or heater activation still need verification. Delayed preheating is a hypothesis. The next protocol check is to compare display and recorder data before and after a single arrow press, leaving the confirmation button untouched.

The `braumeister_menu.set_actuator` action supports manual pump and heater
control with Bridge `0.3.2-control.3-beta.3`. It requires an administrator,
fresh matching device telemetry, and the corresponding Bridge opt-in.
Configure the dashboard opt-ins separately in the Display Card.
