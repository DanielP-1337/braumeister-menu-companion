# Braumeister Local Menu

This Home Assistant integration connects the [Braumeister Display Card](https://github.com/DanielP-1337/braumeister-display-card) to the [upstream Braumeister Bridge](https://github.com/omphteliba/ha-speidel-braumeister/tree/main/braumeister_bridge). It requires a bridge build that includes the local control API from [Bridge PR #20](https://github.com/omphteliba/ha-speidel-braumeister/pull/20) and Display Card v0.7.0-beta.1 or later.

1. In HACS, open **Custom repositories** and add this repository as **Integration**.
2. Download the integration, then add the device ID from the Bridge status API to Home Assistant's `configuration.yaml`.

   ```yaml
   braumeister_menu:
     device_id: "YOUR_BRIDGE_DEVICE_ID"
   ```

3. Check the configuration and restart Home Assistant Core.
4. Set `menu_control: true` in the card YAML. Map the card's entities to the same device. Enable `control_enabled` in the Bridge for testing.
5. As an HA administrator, open Settings on the dashboard and verify the screen on the device. Use Cancel to return to the main menu.

The integration calls the Bridge on `127.0.0.1:8642` from HA Core and waits for the result. It submits each action once and requires fresh device status with both actuators off. Recipe picker highlights refresh after confirmed card actions.

This beta covers menu navigation. End-to-end validation of the dashboard control path on hardware is pending.
