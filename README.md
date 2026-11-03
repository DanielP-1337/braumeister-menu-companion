# Braumeister Local Menu

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
