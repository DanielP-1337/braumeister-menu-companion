# Braumeister Local Menu 0.1.0-beta.6

Adds response-only program-stage services for experimental Bridge
**0.3.2-control.4-beta.1** and Display Card **0.7.0-beta.8**:

- `navigate: select_recipe` confirms the highlighted recipe, stopping at the
  water prompt (2015 -> 2030).
- `program_control: request_program_pause` at 2300/2410.
- `program_control: abort_program` only from the matching pause dialog.
- `program_control: resume_program` only from the purge pause at 2300.

Administrator, fresh telemetry, screen, flags, indicator and source checks remain
mandatory. No raw-key passthrough, automatic retry or direct cloud request is
added. The Bridge independently validates permissions and later confirmation.
Purge resume requires Bridge `program_control_enabled` and `allow_remote_heating`,
plus Card `program_control: true` and a confirmation dialog. Pause/abort are
distinct from resuming. Water confirmation/delayed-start and heating-stage resume
are not in the service allowlist.

Update the existing Bridge first using its separate local-app package, then
install this prerelease through the existing HACS repository. Preserve the
existing `braumeister_menu.device_id` YAML. Restart HA once after the Companion
update; do not remove/re-add the device. No HA integration update is required.

Validation: 17 local schema/adapter tests, Ruff and diff checks passed. Bridge
220 tests plus 261 subtests and an emulated ARM64 container smoke test passed;
the matching Card's seven scripts passed. Actual local-API hardware validation
is pending. No device commands were sent by these tests.

Rollback: redownload the previously installed Companion version in HACS and
restart HA, preserving configuration. Revert the matching Card if needed. Do not
uninstall the Bridge or restore unrelated HA data. Rollback is not hardware tested.
