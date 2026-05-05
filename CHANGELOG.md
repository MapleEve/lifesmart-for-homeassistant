# Changelog

## Unreleased - v2026.05.1 (main/current patch release candidate)

Release branch context:
- Prepared on `fix/main-doc-backed-issue-patch` after `664c07f7605547cb434a0abbee6b938653f2832a`.
- This is a main/current patch release candidate. Gen2 / `v25.08.1` architecture work is not part of this release line.
- `custom_components/lifesmart/manifest.json` now reports `v2026.05.1` for the main/current patch release candidate.
- Local tag `v2026.05.0` points at `4fd1d1c`, before the later main feedback fixes in `664c07f`; publish these notes as the next patch (`v2026.05.1`).

### Highlights

- Cloud password login: use the authentication region returned by `/auth.login` during `/auth.do_auth`, and persist returned `usertoken`, `userid`, and region data when available.
- Local protocol decoding: normalize non-hashable parsed keys before building dictionaries, avoiding `TypeError: unhashable type: 'dict'` from unusual nested local packets.
- Device discovery aliases: recognize runtime-reported `SL_SC_BG_V1` and `SL_P_V1` as their documented base device families.
- RGBW / SPOT lighting: restore single-IO RGBW entity creation when devices do not expose a DYN endpoint, and improve SPOT brightness / color-temperature state handling where P1/P2 data exists.
- DOOYA curtains: correct movement direction interpretation and merge partial websocket updates without dropping existing cover state.
- Climate / thermostat state: improve `SL_NATURE` thermostat detection, temperature parsing fallback, fan mode fallback, hub-aware refresh, and partial websocket state merging.

### Issue handling notes

Do not auto-close every issue below purely from this changelog. The table distinguishes direct fix candidates from partial refs or items that still need reporter validation/hardware confirmation.

| Issue | Status for this release candidate | Suggested PR keyword | Notes |
| --- | --- | --- | --- |
| #92 | Direct fix candidate | `Fixes #92` | Local protocol dict/list decoding now normalizes non-hashable keys before building dictionaries. This matches the reported `TypeError: unhashable type: 'dict'`, but should still be validated against the reporter's smoke sensor/local packet if possible. |
| #95 | Direct fix candidate | `Fixes #95` | Cloud password login now carries the region returned by step 1 into step 2 and stores returned token/user/region data. Live credential-specific validation is required before claiming universal cloud-login coverage. |
| #93 | Direct fix candidate | `Fixes #93` | Adds runtime aliases for `SL_SC_BG_V1` and `SL_P_V1`, including generic controller non-positional cover mapping for `SL_P_V1`. |
| #98 | Direct/partial fix candidate | `Fixes #98` if validated; otherwise `Refs #98` | Restores single-IO RGBW entity creation and improves SPOT brightness/color-temperature handling. This addresses the RGBW/SPOT control path, but local device-list failure mentioned in the same issue belongs with #96/#99 and is not fully resolved here. |
| #91 | Direct/partial fix candidate | `Fixes #91` if validated; otherwise `Refs #91` | Climate temperature and fan-mode parsing were improved, including raw `val / 10` fallback and additional `SL_NATURE` thermostat mode handling. Needs reporter-device validation for the exact AC/Nature variant. |
| #90 | Partial reference | `Refs #90` | Broad smart-panel / downstream-device issue. This release improves climate/control state handling but does not prove every smart-panel-attached switch, VRF, floor-heating, or fresh-air case is fixed. |
| #94 | Direct fix candidate | `Fixes #94` | DOOYA direction bit handling and partial websocket merge were corrected for curtain position/state feedback. Hardware validation is still recommended. |
| #87 | Direct/partial fix candidate | `Fixes #87` if validated; otherwise `Refs #87` | Climate websocket partial-update merging and hub-aware refresh reduce stale frontend state after cloud commands. Reporter validation is recommended before closure. |
| #99 | Partial reference | `Refs #99` | Cloud token/login handling and local websocket/state merge paths improved. The broader local polling-delay and token-expiry report is not fully proven resolved. |
| #101 | Partial reference | `Refs #101` | Cloud password login and some model support overlap with this aggregate request. Door-lock support, dynamic sensor extra entities, and automatic cloud remote import remain outside this main/current patch scope. |
| #96 | Reference / not fixed | `Refs #96` | Local mode remains best-effort; this patch does not claim a full fix for local device-list retrieval failures on affected hub firmware. |

### Validation notes

- Focused code/test fixes were already present before this documentation commit.
- A full main/current regression was running separately in `tmp/2026-05-06-main-664c07f-full-regression.log` at documentation-preparation time; this docs commit did not start or interrupt that regression.
- This documentation-only release-preparation commit only ran lightweight markdown/content checks.
