# Program-control adapter — 0.1.0-beta.6

This branch adds recipe confirmation (`navigate: select_recipe`) and a separate
response-only `braumeister_menu.program_control` service. Advertised actions:

- `request_program_pause`: unpaused 2300 or 2410, recognized flags, indicator 000.
- `abort_program`: paused 2300 or 2410, flags ph, indicator 120.
- `resume_program`: paused **2300 only**, flags ph, indicator 120.

The adapter checks administrator identity, source screen, actuator flags,
indicator, status age below five seconds and, for program actions, a recent
cloud/local-control source before posting one bounded action. It uses only the
existing loopback Bridge API, keeps the existing per-device configuration and
service lock, and awaits Bridge confirmation. It never creates a cloud request,
raw-key endpoint or automatic retry.

The matching Bridge prototype independently rechecks the source context and
confirms the later indicator/flags. `control_enabled` remains required. Resume
additionally requires both new Bridge `program_control_enabled` and existing
`allow_remote_heating`; defaults remain false. Cancellation does not depend on
opting into resume. The Card adds its own `program_control: true` opt-in and
confirmation for resume, and a separate confirmation for final abort.

Water confirmation, water-prompt cancellation, delayed-start keys, resume during
heating and state 2310 are not advertised or accepted by this service schema.
They remain disabled in the Card. Selecting a recipe ends at the water prompt.

Evidence from user-operated MySpeidel tests on 2026-11-06:

```text
Pause during purge:   2300 / ph / 120
Pause during heating: 2410 / ph / 120
Final abort:           101 / ph / 000
Resume purge:         2300 / Ph / 000
```

These are cloud/device observations. The new local service has only been tested
with synthetic HA/HTTP objects and real voluptuous schemas. No hardware test of
this adapter, deployment, HA restart or recipe/program start was performed.

Run tests with the development dependencies in `requirements_test.txt` and
`pytest`. The Bridge uses a separate loopback-cloud suite. See [beta installation notes](../release-v0.1.0-beta.6.md). Controlled local-API hardware tests remain pending.

## User-reported hardware test — 2026-11-06

The user reports a successful test on the real Braumeister after the HACS test releases Display Card 0.7.0-beta.9 and Companion 0.1.0-beta.7 were provided. The reported problem was the disabled Cancel button during pump purging; the confirmed input status was state 2300, flags Ph, indicator 000. Installed baseline: Bridge 0.3.2-control.4-beta.1 and HA integration 3.1.1-beta.2.

This validates the reported pump-purge Cancel use case. The user had previously confirmed heating Cancel, the final-abort confirmation dialog and return to the main menu. This report does not establish validation of resume, water confirmation, delayed start, or every program stage. It also does not prove that the original installed UI failure was caused by a string-valued screen code.

Card beta.9 accepts numeric and numeric-string screen codes at the menu lookup/dispatch boundary; all seven local Node test scripts passed. Companion beta.7 retains beta.6 control rules. Python tests were not rerun in this follow-up because the available interpreter lacks pytest; earlier suite results remain historical. The assistant issued no appliance commands.