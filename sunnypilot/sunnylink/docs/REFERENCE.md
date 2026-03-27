# sunnylink Settings UI Definition Guide

> How to add, change, or update params/settings that appear on the sunnylink frontend -- without modifying any frontend code.

## Overview

The sunnylink frontend renders its settings UI entirely from a **device-generated schema**. One file in the sunnypilot repo controls what the frontend displays:

| File | What you control |
|------|-----------------|
| `sunnypilot/sunnylink/settings_ui.json` | Structure, layout, widget types, display text, options, ranges, visibility/enablement rules |

**The frontend renders whatever the device sends.** No frontend PR needed.

---

## Quick Start

### Adding a new toggle (minimum viable change)

**1. Register the param** in `common/params_keys.h`:
```cpp
{"MyNewToggle", {PERSISTENT | BACKUP, BOOL}},
```

**2. Place it in the UI** in `sunnypilot/sunnylink/settings_ui.json`:

Find the panel and section where it belongs, then add to the `items` array:
```json
{
  "key": "MyNewToggle",
  "widget": "toggle",
  "title": "My New Feature",
  "description": "Enable the new feature for enhanced driving.",
  "enablement": [{"type": "offroad_only"}]
}
```

**3. Validate:**
```bash
python sunnypilot/sunnylink/tools/validate_settings_ui.py
```

**4. Commit.** The frontend will render it on the next device boot.

---

## File Structure

```
sunnypilot/sunnylink/
  settings_ui.json            <-- UI definition (the only file you edit)
  settings_ui.schema.json     <-- JSON Schema for IDE autocomplete
  capabilities.py             <-- Car capability fields (reference)
  tools/
    validate_settings_ui.py   <-- Run this after every edit
    generate_settings_schema.py  <-- Reads settings_ui.json, compresses for device param
```

---

## How It Works

```
settings_ui.json
  (structure, rules, titles, options, ranges -- everything)
        |
        v
  gzip + base64 encode
        |
        v
  SettingsSchema param (stored on device)
        |
        v (fetched via getParams RPC)
  sunnylink frontend
  (decodes, decompresses, renders)
```

At device boot, the generator:
1. Reads `settings_ui.json`
2. Compresses (gzip) and base64-encodes
3. Writes to the `SettingsSchema` param

The frontend fetches this param, decompresses it, and renders the UI.

---

## settings_ui.json Structure

### Hierarchy

```
Root
  panels[]                    <-- Top-level navigation categories
    sections[]                <-- Grouped cards within a panel
      items[]                 <-- Individual settings
        sub_items[]           <-- Nested settings revealed by parent
      sub_panels[]            <-- Drill-down pages (chevron rows)
    items[]                   <-- Flat items (panels without sections)
  vehicle_settings{}          <-- Brand-specific settings (by brand key)
```

### Panel (top-level category)

```json
{
  "id": "steering",
  "label": "Steering",
  "icon": "steering_wheel",
  "order": 1,
  "description": "Lateral control, lane changes, and steering behavior",
  "remote_configurable": true,
  "sections": [...]
}
```

| Field | Required | Description |
|-------|----------|-------------|
| `id` | Yes | Unique identifier, matches the URL path (`/dashboard/settings/{id}`) |
| `label` | Yes | Display name in the sidebar navigation |
| `icon` | Yes | Icon identifier |
| `order` | Yes | Sort order in navigation (must be unique across panels) |
| `description` | No | Subtitle shown below the panel heading |
| `remote_configurable` | No | Whether the frontend can push changes (default: `true`) |
| `sections` | No | Array of grouped sections (use this OR `items`, not both) |
| `items` | No | Array of flat items (for simple panels without grouping) |

### Section (grouped card within a panel)

```json
{
  "id": "mads",
  "title": "MADS",
  "description": "Modified Assistive Driving Safety",
  "order": 1,
  "items": [...],
  "sub_panels": [...],
  "visibility": [{"type": "capability", "field": "has_longitudinal_control", "equals": true}],
  "enablement": [{"type": "offroad_only"}]
}
```

| Field | Required | Description |
|-------|----------|-------------|
| `id` | Yes | Unique within the panel |
| `title` | Yes | Section header displayed above the card |
| `description` | No | Subtitle below the section header |
| `order` | No | Sort order within the panel (falls back to array position) |
| `visibility` | No | Rules controlling if the entire section is visible. When rules fail, section is dimmed. |
| `enablement` | No | Rules controlling if the entire section is enabled. When rules fail, all items within are disabled. |
| `items` | No | Settings within this section |
| `sub_panels` | No | Drill-down pages triggered by items in this section |

### Item (individual setting)

```json
{
  "key": "Mads",
  "widget": "toggle",
  "title": "Modular Assistive Driving System (MADS)",
  "description": "Enable the beloved MADS feature.",
  "enablement": [{"type": "offroad_only"}]
}
```

| Field | Required | Description |
|-------|----------|-------------|
| `key` | Yes | Param key name (must exist in `params_keys.h`) |
| `widget` | Yes | One of: `toggle`, `option`, `multiple_button`, `button`, `info` |
| `title` | Yes | Display name shown to the user |
| `description` | No | Explanatory text below the title. Supports `<br>` for line breaks. |
| `options` | For selectors | Array of `{"value": 0, "label": "Off"}` for `option` or `multiple_button` widgets. Each option can have `enablement` rules. |
| `min` | For sliders | Minimum value (renders `option` widget as a slider) |
| `max` | For sliders | Maximum value |
| `step` | For sliders | Step increment |
| `unit` | No | Unit label. Static: `"seconds"`. Dynamic: `{"metric": "km/h", "imperial": "mph"}` (frontend resolves based on `IsMetric` param). See [Dynamic Units](#dynamic-units). |
| `value_map` | No | Maps stored values to display labels |
| `visibility` | No | Rules controlling visibility. Settings are **never hidden**, always dimmed with UNAVAILABLE badge when rules fail. See [Visibility vs Enablement](#visibility-vs-enablement). |
| `enablement` | No | Rules controlling enabled/disabled state. Grayed out with contextual badge when rules fail. |
| `blocked` | No | When `true`, this param cannot be modified remotely (device-only). Frontend shows as read-only. |
| `title_param_suffix` | No | Dynamic title suffix. Object with `param` (param key) and `values` (mapping of param values to suffix strings). |
| `sub_items` | No | Child items that appear indented below this item |
| `needs_onroad_cycle` | No | When `true`, this param requires an onroad cycle to take effect. See [Remote Onroad Cycle](#remote-onroad-cycle) |

### Sub-Panel (drill-down page)

```json
{
  "id": "mads_settings",
  "label": "MADS Settings",
  "trigger_key": "Mads",
  "trigger_condition": {
    "type": "param",
    "key": "Mads",
    "equals": true
  },
  "items": [...]
}
```

| Field | Required | Description |
|-------|----------|-------------|
| `id` | Yes | Unique identifier |
| `label` | Yes | Text shown on the chevron row |
| `trigger_key` | Yes | Param key that this sub-panel relates to (must exist in same panel) |
| `trigger_condition` | No | Rule that controls when the sub-panel row is visible |
| `items` | No | Settings shown when the sub-panel is opened |

---

## Widget Types

| Widget | Renders as | Use when |
|--------|-----------|----------|
| `toggle` | On/off switch | Boolean param (`BOOL` type) |
| `multiple_button` | Segmented button group | Param with 2-4 discrete options |
| `option` | Dropdown or slider | Param with many options, or numeric range with `min`/`max` |
| `info` | Read-only text display | Display-only values (e.g., language) |
| `button` | Action button | Triggering an action (rarely used) |

**How the frontend decides dropdown vs slider for `option` widget:**
- If item has `min`/`max`/`step` -> renders as a **slider**
- If item has `options` array -> renders as a **dropdown**

**How the frontend handles `multiple_button` overflow:**
- Fits on screen -> **segmented buttons** (pill-shaped)
- Too many options -> **compact mode** (smaller text)
- Still overflows -> **dropdown fallback**

---

## Visibility vs Enablement

**Critical design difference:**

- **`visibility` rules** (NEW): Settings are **never hidden**. When rules fail, the setting is **dimmed with an UNAVAILABLE badge** so users know it exists but isn't applicable. This prevents confusion and preserves UI stability.

- **`enablement` rules**: When rules fail, the setting is **grayed out** with a contextual badge explaining why (e.g., "Requires longitudinal control"). User can still see it exists.

The "dim instead of hide" approach (visibility-based dimming instead of hiding) provides better UX: settings remain discoverable, and users understand why a setting is unavailable.

## Rules Reference

Rules control **visibility** (dimmed) and **enablement** (grayed out).

- All rules in an array use **AND** logic (all must pass for the rule to pass)
- If ANY rule fails, the condition is unsatisfied
- Empty array or no rules = always visible/enabled

### offroad_only

Only passes when the device is not actively driving.

```json
{"type": "offroad_only"}
```

Use in `enablement` (not `visibility`) so users can see the setting exists but know they need to stop to change it. The frontend shows an "Offroad" badge.

### capability

Checks a vehicle capability derived from CarParams at runtime.

```json
{"type": "capability", "field": "has_longitudinal_control", "equals": true}
```

```json
{"type": "capability", "field": "brand", "equals": "toyota"}
```

**Permissive evaluation**: When brand is empty (no car fingerprinted yet), capability rules are **permissive** (return `true`). This prevents hiding settings before capabilities load. Once capabilities arrive, rules are evaluated normally.

**Available capability fields:**

| Field | Type | Description | Label (from schema) |
|-------|------|-------------|-------------------|
| `has_longitudinal_control` | bool | Car supports openpilot longitudinal | "sunnypilot longitudinal control" |
| `has_icbm` | bool | Intelligent Cruise Button Management active | "ICBM enabled" |
| `icbm_available` | bool | ICBM is available for this car | "ICBM available" |
| `torque_allowed` | bool | Torque lateral control supported | "torque steering (not available for angle steering vehicles)" |
| `brand` | string | Vehicle brand (e.g., "toyota", "hyundai") | "Vehicle brand" |
| `pcm_cruise` | bool | PCM cruise control | "PCM cruise" |
| `alpha_long_available` | bool | Alpha longitudinal available | "Alpha Longitudinal available" |
| `steer_control_type` | string | Steering control type (e.g., "angle", "torque") | "Steer control type" |
| `enable_bsm` | bool | Blind spot monitoring available | "BSM available" |
| `is_release` | bool | Running release branch | "Release branch" |
| `is_sp_release` | bool | Running sunnypilot release branch | "SP release branch" |
| `is_development` | bool | Running development branch | "Development branch" |
| `tesla_has_vehicle_bus` | bool | Tesla with vehicle bus access | "Tesla vehicle bus" |
| `has_stop_and_go` | bool | Stop and go capability | "Stop and Go" |
| `stock_longitudinal` | bool | Using stock longitudinal control | "stock longitudinal" |

The `capability_labels` field in the schema response maps these field names to human-readable strings for UI tooltips. Fallback labels are provided by the evaluator if the schema doesn't include `capability_labels`.

### param

Checks the current value of another param.

```json
{"type": "param", "key": "Mads", "equals": true}
```

### param_compare

Numeric comparison against another param's value.

```json
{"type": "param_compare", "key": "AutoLaneChangeTimer", "op": ">", "value": 0}
```

| Operator | Meaning |
|----------|---------|
| `>` | Greater than |
| `<` | Less than |
| `>=` | Greater than or equal |
| `<=` | Less than or equal |

### not

Negates a single rule. The setting is enabled/visible when the inner condition is **false**.

```json
{
  "type": "not",
  "condition": {
    "type": "capability",
    "field": "steer_control_type",
    "equals": "angle"
  }
}
```

This example: show the setting only for non-angle steering cars (i.e., when steer_control_type is NOT "angle").

**Description generation**: When a negated rule fails (inner condition is true), the frontend generates an inverted message. For example:
- Inner rule "Requires longitudinal control" → inverted to "Not available with longitudinal control disabled"
- Inner rule "Disable X first" → inverted to "Enable X first"

### any (OR logic)

Passes if **at least one** child condition passes. The setting is enabled/visible if any condition is satisfied.

```json
{
  "type": "any",
  "conditions": [
    {"type": "capability", "field": "has_longitudinal_control", "equals": true},
    {"type": "capability", "field": "has_icbm", "equals": true}
  ]
}
```

This example: show the setting if the car has either longitudinal control OR ICBM.

**Description generation**: When an `any` rule fails (all conditions are false), failure reasons are joined with "or":
- "Requires longitudinal control or ICBM available"
- Multiple reasons with common prefix are consolidated: "Requires X or Y or Z"

### all (AND logic)

Passes if **all** child conditions pass. (Note: a plain array of rules already uses AND logic. Use `all` inside `any` or `not` for nested logic.)

```json
{
  "type": "all",
  "conditions": [
    {"type": "param_compare", "key": "SpeedLimitMode", "op": ">", "value": 0},
    {"type": "param_compare", "key": "SpeedLimitOffsetType", "op": ">", "value": 0}
  ]
}
```

---

## Common Scenarios

### 1. Add a new toggle to an existing section

Find the panel and section, add to `items`:

```json
{
  "key": "FirehoseMode",
  "widget": "toggle",
  "title": "Firehose Mode",
  "description": "Upload all driving data continuously.",
  "enablement": [{"type": "offroad_only"}]
}
```

### 2. Add a multi-button selector with options

```json
{
  "key": "RecordingQuality",
  "widget": "multiple_button",
  "title": "Recording Quality",
  "options": [
    {"value": 0, "label": "Low (720p)"},
    {"value": 1, "label": "Medium (1080p)"},
    {"value": 2, "label": "High (4K)"}
  ]
}
```

### 3. Add a slider/range control

```json
{
  "key": "FollowDistance",
  "widget": "option",
  "title": "Follow Distance",
  "description": "Time gap to lead vehicle.",
  "min": 0.5,
  "max": 3.0,
  "step": 0.1,
  "unit": "seconds"
}
```

### 4. Show a setting only when another setting is enabled

```json
{
  "key": "BlinkerMinLateralControlSpeed",
  "widget": "option",
  "title": "Minimum Speed for Lateral Control",
  "visibility": [
    {"type": "param", "key": "BlinkerPauseLateralControl", "equals": true}
  ]
}
```

### 5. Show a setting only for specific cars

```json
{
  "key": "SmartCruiseControlVision",
  "widget": "toggle",
  "title": "Smart Cruise Control (Vision)",
  "visibility": [
    {
      "type": "any",
      "conditions": [
        {"type": "capability", "field": "has_longitudinal_control", "equals": true},
        {"type": "capability", "field": "has_icbm", "equals": true}
      ]
    }
  ]
}
```

### 6. Mutual exclusion (two toggles that can't both be on)

Each toggle's `enablement` requires the other to be `false`:

```json
{
  "key": "EnforceTorqueControl",
  "widget": "toggle",
  "title": "Enforce Torque Lateral Control",
  "enablement": [
    {"type": "offroad_only"},
    {"type": "param", "key": "NeuralNetworkLateralControl", "equals": false}
  ]
},
{
  "key": "NeuralNetworkLateralControl",
  "widget": "toggle",
  "title": "Neural Network Lateral Control",
  "enablement": [
    {"type": "offroad_only"},
    {"type": "param", "key": "EnforceTorqueControl", "equals": false}
  ]
}
```

### 7. Add a new section to a panel

```json
{
  "id": "comfort",
  "title": "Comfort",
  "description": "Steering feel and responsiveness tuning",
  "order": 5,
  "items": [
    {"key": "SteeringResponsiveness", "widget": "option", "title": "Steering Responsiveness"}
  ]
}
```

### 8. Add a sub-panel (drill-down page)

```json
{
  "id": "comfort",
  "title": "Comfort",
  "items": [
    {"key": "SteeringResponsiveness", "widget": "option", "title": "Steering Responsiveness"}
  ],
  "sub_panels": [
    {
      "id": "advanced_steering",
      "label": "Advanced Steering",
      "trigger_key": "SteeringResponsiveness",
      "items": [
        {"key": "SteeringDeadzone", "widget": "option", "title": "Deadzone"},
        {"key": "SteeringRampRate", "widget": "option", "title": "Ramp Rate"}
      ]
    }
  ]
}
```

### 9. Add vehicle-specific settings

Add to `vehicle_settings` in `settings_ui.json`:

```json
"rivian": {
  "title": "Rivian Settings",
  "items": [
    {
      "key": "RivianOnePedalMode",
      "widget": "toggle",
      "title": "Rivian One Pedal",
      "enablement": [{"type": "offroad_only"}]
    }
  ]
}
```

Only users with a Rivian (where `capabilities.brand === "rivian"`) see this on the Vehicle page.

### 10. Change display text

Edit the `title` or `description` directly on the item in `settings_ui.json`.

### 11. Move a setting from one panel to another

1. Remove the item from its current panel/section
2. Add it to the target panel/section
3. Run the validator (catches duplicate keys if you forget to remove)

### 12. Grey out a setting while driving

Use `enablement` with `offroad_only`:

```json
{
  "key": "MyParam",
  "widget": "toggle",
  "title": "My Param",
  "enablement": [{"type": "offroad_only"}]
}
```

The toggle is visible but disabled while driving. The frontend shows an "Offroad" badge.

### 13. Description with line breaks

Use `<br>` tags (only `<br>` is allowed, all other HTML is stripped):

```json
{
  "key": "SomeParam",
  "widget": "toggle",
  "title": "Feature Name",
  "description": "First line of explanation.<br>Second line with more detail."
}
```

---

## Validation

**Always run after editing `settings_ui.json`:**

```bash
python sunnypilot/sunnylink/tools/validate_settings_ui.py
```

The validator performs 10 checks:

| Check | What it catches |
|-------|----------------|
| JSON parseable | Syntax errors, trailing commas, missing brackets |
| Structural | Missing required fields (id, key, widget, etc.) |
| Item completeness | Missing `title`, dropdown items missing `options` with `value` + `label` |
| No duplicate keys | Same param key in multiple panels |
| Rule well-formedness | Invalid rule types, missing fields, bad operators |
| Capability refs | Capability field names that don't exist |
| No self-reference | Item whose rule references its own key |
| Sub-panel triggers | trigger_key that doesn't exist in the same panel |
| Ordering | Duplicate panel order values |
| Vehicle brands | Non-lowercase brand keys |

---

## IDE Support

`settings_ui.json` references a JSON Schema file for editor autocomplete:

```json
{
  "$schema": "./settings_ui.schema.json",
  ...
}
```

In VS Code or JetBrains IDEs, this provides:
- Autocomplete for field names
- Enum validation for widget types and rule types
- Red squiggles for structural errors
- Hover documentation

---

## Checklist

Before committing changes to `settings_ui.json`:

- [ ] Param registered in `common/params_keys.h` with correct type
- [ ] Item in `settings_ui.json` with correct widget type and `title`
- [ ] Widget type matches the param type (toggle for BOOL, option/multiple_button for INT/FLOAT)
- [ ] Visibility rules use correct capability field names
- [ ] Enablement includes `offroad_only` for settings that should not change while driving
- [ ] `needs_onroad_cycle: true` for settings that trigger `OnroadCycleRequested` on the device UI
- [ ] `python sunnypilot/sunnylink/tools/validate_settings_ui.py` passes

---

## Per-Option Enablement

Individual options within `multiple_button` or `option` widgets can have their own `enablement` rules:

```json
{
  "key": "MadsSteeringMode",
  "widget": "multiple_button",
  "title": "Steering Mode on Brake Pedal",
  "options": [
    {
      "value": 0,
      "label": "Remain Active",
      "enablement": [
        {
          "type": "not",
          "condition": {"type": "capability", "field": "brand", "equals": "tesla"}
        }
      ]
    },
    {
      "value": 1,
      "label": "Pause",
      "enablement": [{"type": "offroad_only"}]
    }
  ]
}
```

When an option's enablement fails, that option is **grayed out** (disabled but still visible and selectable). This prevents users from changing to an unavailable option but keeps the UI stable.

---

## Dynamic Title Suffixes

Use `title_param_suffix` to append a dynamic value to the title based on another param:

```json
{
  "key": "FollowDistance",
  "widget": "option",
  "title": "Follow Distance",
  "title_param_suffix": {
    "param": "IsMetric",
    "values": {"0": "mph", "1": "km/h"}
  },
  "min": 0.5,
  "max": 3.0,
  "step": 0.1
}
```

**Result**:
- When `IsMetric = 0`: displays "Follow Distance: mph"
- When `IsMetric = 1`: displays "Follow Distance: km/h"

The `values` object maps param values (as strings) to suffix text. Unknown param values show no suffix.

---

## Device-Only (Blocked) Settings

Use `blocked: true` to mark a setting as device-only and not remotely configurable:

```json
{
  "key": "OnroadCyclePendingRemote",
  "widget": "info",
  "title": "Pending Remote Cycle",
  "blocked": true
}
```

**Frontend behavior**: Displays the setting as read-only. Users cannot change it via sunnylink.

**Use case**: Params that are written by the device itself (e.g., `OnroadCyclePendingRemote`, `AutoApplyRemoteOnroadCycle`) should be marked `blocked` to indicate they are not user-modifiable remotely.

---

## How Capabilities Work

Capabilities are **car-derived boolean/string fields** that rules can reference. They bridge CarParams (device-specific) to the schema (declarative).

### Generation pipeline (`capabilities.py`)

```
Device boot
  |
  v
CarParamsPersistent (serialized CarParams from car fingerprint)
  |
  v
capabilities.py: generate_capabilities()
  |
  +-- Phase 1: All fields default to False / ""
  +-- Phase 2: Boolean params (IsReleaseBranch, etc.) -- no CarParams needed
  +-- Phase 3: CarParams-derived (alphaLongitudinalAvailable, brand, etc.)
  +-- Phase 3b: CarParamsSP-derived (ICBM, Tesla flags)
  |
  v
SettingsCapabilities JSON param (written to device param store)
  |
  v (fetched by frontend via getParams RPC)
Frontend rule evaluator checks capabilities.field === equals
```

### When capabilities are unavailable

When `CarParamsPersistent` hasn't been written yet (no car detected), or when brand is empty, ALL CarParams-derived capabilities default to `False` or `""`.

**Permissive evaluation**: The frontend rule evaluator treats capability-referencing rules as **permissive** (returns `true`) when capabilities are unavailable. This prevents hiding/disabling settings before capabilities load.

**Result**:
- Items with `visibility: [capability: torque_allowed == true]` will be **temporarily visible** before caps load, then dimmed if the car doesn't support torque
- Items with `enablement: [capability: has_longitudinal_control == true]` will be **temporarily enabled**, then disabled
- Items without capability rules show normally regardless of capability status

**Rationale**: Prevents jarring flashes of empty panels on page load. Better UX to show settings as available initially, then dim them once the actual car capabilities are known.

### Capability field generation (`capabilities.py`)

Device generates capabilities at runtime via `generate_capabilities()`:

```
1. Initialize all fields to defaults (False for booleans, "" for strings)
2. Overwrite with boolean params (is_release, is_sp_release, is_development, stock_longitudinal)
   → No CarParams dependency, always available
3. Overwrite with CarParams-derived fields (brand, has_longitudinal_control, torque_allowed, etc.)
   → Only if CarParamsPersistent is available
4. Overwrite with CarParamsSP-derived fields (has_icbm, icbm_available, tesla_has_vehicle_bus)
   → Only if CarParamsSPPersistent is available
```

Each phase preserves previous values and only overwrites if new data is available. This ensures safe initialization even if some params are missing.

---

## Schema Generator Pipeline (`generate_settings_schema.py`)

The generator is a **pass-through** -- it reads `settings_ui.json` as-is, compresses, and writes to the device param store. There is no enrichment or transformation step.

```python
# Simplified flow
def generate_schema():
    definition = load("settings_ui.json")
    return definition  # No merge, no enrichment
```

### Compression

The schema is compressed before writing to the param store:
1. JSON serialize (compact, no whitespace) -- ~36KB
2. gzip compress -- ~5KB
3. base64 encode -- ~7KB string

The frontend detects compressed data (gzip magic bytes `H4sI`) and decompresses automatically.

### Introspection utilities

The generator also provides helper functions used by the validator and other tools:
- `collect_all_keys()` -- extracts all param keys referenced in items and rules
- `collect_capability_refs()` -- extracts all capability field names from rules

---

## Centralized Param Enforcement

The device UI enforces capability-driven constraints in `selfdrive/ui/sunnypilot/ui_state.py:_enforce_sp_constraints()`. This is the **single source of truth** for removing incompatible params from user control.

**Key constraints enforced**:

| Condition | Params Removed | Reason |
|-----------|----------------|--------|
| Angle steering car (`steerControlType == angle`) | `EnforceTorqueControl`, `NeuralNetworkLateralControl` | Angle steering doesn't support torque control |
| No CarParams available | `EnforceTorqueControl`, `NeuralNetworkLateralControl`, `AlphaLongitudinalEnabled` | Safety: avoid stale param values |
| Alpha longitudinal not available OR on release branch | `AlphaLongitudinalEnabled` | Feature gating |
| No blind spot monitoring | `AutoLaneChangeBsmDelay` | Car capability |
| No longitudinal control | `ExperimentalMode` | Feature dependency |
| No ICBM available OR full longitudinal active | `IntelligentCruiseButtonManagement` | Conflict: can't use ICBM if full long control active |
| No (longitudinal OR ICBM) | `CustomAccIncrementsEnabled`, `DynamicExperimentalControl`, `SmartCruiseControlVision`, `SmartCruiseControlMap` | All cruise features require at least one |

**Important**: Settings layouts should **NOT** duplicate these `params.remove()` calls. The centralized enforcement is automatically applied at device boot. Layouts should instead rely on schema visibility/enablement rules to match these constraints, so the frontend can properly gate the UI.

---

## Frontend Component Layout

The sunnylink frontend uses a consistent spacing system aligned with Linear's design language:

**Spacing hierarchy**:
- **36px** between page title and first section
- **12px** between section title and card/items
- **48px** between sections (card to next section title)
- **8px** vertical gap between items within a section

**SettingsPageShell component**: Provides consistent page layout with header, breadcrumb, and scrollable content area. All settings pages should wrap content in this component for visual consistency.

---

## Device-Side Dialogs vs. Frontend Widgets

The device UI uses several dialog types that have **no direct equivalent** in the schema. Instead, the schema maps them to the closest frontend widget type.

### TreeOptionDialog (device) -> `multiple_button` or `option` (schema)

On the device, `TreeOptionDialog` renders a hierarchical tree selector with search and favorites.

| Param | Device dialog | Schema widget | Frontend renders as |
|-------|--------------|---------------|-------------------|
| `TorqueControlTune` | TreeOptionDialog (torque version list from JSON) | `multiple_button` | Segmented buttons |

### MultiOptionDialog (device) -> `info` (schema)

On the device, `MultiOptionDialog` renders a scrollable flat list picker.

| Param | Device dialog | Schema widget | Frontend renders as |
|-------|--------------|---------------|-------------------|
| `LanguageSetting` | MultiOptionDialog (language list) | `info` | Read-only display |

Language selection is not remotely configurable -- it requires a device reboot and locale change.

### ConfirmDialog (device) -> handled by frontend

On the device, `ConfirmDialog` shows a two-button confirmation before toggling certain params. The frontend handles confirmation for destructive operations in its own push flow -- no schema representation needed.

Params that use ConfirmDialog on device:
- `AlphaLongitudinalEnabled` -- confirmation before enabling alpha longitudinal
- `ExperimentalMode` -- confirmation before enabling
- `OffroadMode` -- double confirmation before forcing offroad
- Calibration reset -- confirmation before deleting calibration data

### OptionControlSP (device) -> `option` (schema)

On the device, `OptionControlSP` renders a +/- stepper with numeric display. In the schema, this maps to `widget: "option"` with `min`/`max`/`step`. The frontend renders it as a **slider** when range fields are present.

---

## Parity Reference: Device UI vs. sunnylink Frontend

### Full param coverage

All **80 remotely-configurable params** from the device settings layouts are present in `settings_ui.json`. This was verified by auditing every non-mici layout file:

| Layout file | Params | All in schema? |
|-------------|--------|---------------|
| `steering.py` + sub-layouts | 17 | Yes |
| `cruise.py` + sub-layouts | 10 | Yes |
| `display.py` | 3 | Yes |
| `visuals.py` | 13 | Yes |
| `developer.py` (upstream + SP) | 10 | Yes |
| `sunnylink.py` | 3 | Yes |
| `device.py` (upstream + SP) | 10 | Yes |
| `models.py` | 5 | Yes |
| `toggles.py` | 9 | Yes |
| Vehicle settings | 6 | Yes |

### Known behavior differences

These are intentional differences between the device UI and the frontend rendering:

| Param | Device behavior | Frontend behavior | Why |
|-------|----------------|-------------------|-----|
| `EnforceTorqueControl` | Hidden when CP=None | Visible but dimmed (UNAVAILABLE badge) | Dim-instead-of-hide design: permissive before caps load, then dimmed if unavailable |
| `NeuralNetworkLateralControl` | Hidden when CP=None | Visible but dimmed (UNAVAILABLE badge) | Same as above |
| `AlphaLongitudinalEnabled` | Disabled when engaged | Disabled (no real-time engagement check) | Frontend can't detect real-time engagement state; rules use static capability checks |
| `SpeedLimitMode` | "Assist" option disabled for Tesla/Rivian SP release | All options enabled | Per-option enablement now supported in schema |
| `MadsMainCruiseAllowed` | Hidden for limited MADS platforms (Tesla w/o bus, Rivian) | Visible but dimmed (permissive caps) | Dim-instead-of-hide design ensures settings remain discoverable |
| `LanguageSetting` | MultiOptionDialog picker | Read-only info display | Language change requires device reboot |
| `TorqueControlTune` | TreeOptionDialog with version folders | Segmented buttons or dropdown | Options are flat on frontend; tree structure not representable in schema |

### Panels NOT in schema (device-only)

These panels exist on the device but are intentionally excluded from the schema because they involve device-local operations:

| Panel | Why excluded |
|-------|-------------|
| Network | WiFi scanning, connection management -- device-local hardware |
| Software | Update download/install -- device-local operation |
| Trips | Read-only drive statistics from API |
| OSM | Offline map download/management -- large file operations |
| Navigation | Not yet implemented on device |

### Device UI features not representable in schema

| Feature | Description | Workaround |
|---------|-------------|------------|
| OnroadCycleRequested | Some toggles trigger a restart | Frontend push triggers `OnroadCyclePendingRemote` -- device prompts driver to confirm before cycling. See [Remote Onroad Cycle](#remote-onroad-cycle) |
| Lock params | `{Param}Lock` disables user control | Not needed for remote config |
| Metric scaling | Speed values scale by IsMetric | Frontend reads IsMetric and formats accordingly |
| Mutual exclusion side effects | JoystickDebugMode resets LongitudinalManeuverMode | Frontend uses enablement rules only (no cross-param reset) |

---

## Dynamic Units

Speed and distance units depend on the user's `IsMetric` preference. The `unit` field supports two forms:

**Static** (constant regardless of IsMetric):
```json
"unit": "seconds"
"unit": "m/s²"
"unit": "meters"
```

**Dynamic** (resolved by the frontend based on `IsMetric` param):
```json
"unit": {"metric": "km/h", "imperial": "mph"}
```

The frontend reads `IsMetric` from the device's param values and displays the appropriate string. When `IsMetric` is `true` or `1`, the `metric` value is shown. Otherwise, the `imperial` value is shown.

### Items with dynamic units

| Param | Unit |
|-------|------|
| `BlinkerMinLateralControlSpeed` | `{"metric": "km/h", "imperial": "mph"}` |
| `SpeedLimitValueOffset` | `{"metric": "km/h", "imperial": "mph"}` |
| `LaneTurnValue` | `{"metric": "km/h", "imperial": "mph"}` |

### When to use dynamic units

Use `{"metric": ..., "imperial": ...}` whenever the param stores a value whose interpretation depends on `IsMetric`. This includes:
- Speed values (km/h vs mph)
- Distance values (km vs mi) if applicable

Use a plain string when the unit is always the same regardless of user preference (seconds, m/s², meters, percentages).

### Descriptions with speed references

For **fixed thresholds** in descriptions (not user-configurable), include both units inline:
```json
"description": "Alerts when driving over 31 mph (50 km/h)."
```

For **user-configurable values**, use the `unit` field instead of embedding units in the description.

---

## Remote Onroad Cycle

When the sunnylink frontend pushes a param change for a setting marked with `needs_onroad_cycle: true`, the device triggers a confirmation flow before cycling the system.

### How it works

```
sunnylink saveParams() writes param value
        |
        v
sunnylinkd checks: is this param in ONROAD_CYCLE_PARAMS?
        |
       Yes --> set OnroadCyclePendingRemote = True
        |
        v
selfdrived (0.1s poll): reads OnroadCyclePendingRemote
        |
       True + engaged --> emit remoteCyclePending event
        |                   (onroad alert: "Remote Settings Update Pending / Disengage to Apply")
        |
       True + not engaged --> UIStateSP.check_remote_cycle_pending()
        |
        v
AutoApplyRemoteOnroadCycle ON?
        |           |
       Yes         No (default)
        |           |
        v           v
  Set cycle     Show ConfirmDialog:
  immediately     tici: "Apply Now" / "Later" buttons
  (no prompt)     mici: "slide to apply" slider
```

### Params

| Param | Type | Flags | Description |
|-------|------|-------|-------------|
| `OnroadCyclePendingRemote` | BOOL | CLEAR_ON_MANAGER_START | Set by sunnylinkd when a cycle-requiring param is written remotely. Cleared after driver confirms or declines. |
| `AutoApplyRemoteOnroadCycle` | BOOL | PERSISTENT, BACKUP | Toggle: OFF (default) = always prompt driver. ON = skip prompt, auto-cycle when not engaged. |

Both params are in `BLOCKED_PARAMS` -- they cannot be modified via sunnylink.

### Settings that require onroad cycle

These items have `needs_onroad_cycle: true` in `settings_ui.json`:

| Param | Panel |
|-------|-------|
| `OpenpilotEnabledToggle` | Toggles |
| `RecordFront` | Toggles |
| `RecordAudio` | Toggles |
| `AlphaLongitudinalEnabled` | Developer |
| `ToyotaEnforceStockLongitudinal` | Vehicle (Toyota) |
| `ToyotaStopAndGoHack` | Vehicle (Toyota) |

The set of cycle-requiring params is loaded at sunnylinkd startup from `settings_ui.json` -- no code change needed when adding new items.

### Frontend behavior

The frontend reads `needs_onroad_cycle` from the schema and displays an orange **Restart** badge next to affected settings. This indicates to the user that changing the setting will require a brief system restart.

### Safety gates

| Gate | Description |
|------|-------------|
| Never cycle while engaged | Dialog/auto-cycle only triggers when `engaged == False` |
| Blocked from remote write | `OnroadCycleRequested`, `AutoApplyRemoteOnroadCycle`, `OnroadCyclePendingRemote` all in `BLOCKED_PARAMS` |
| Driver confirmation required (default) | `AutoApplyRemoteOnroadCycle` defaults to OFF -- driver must approve each cycle |
| Enable confirmation | Turning ON `AutoApplyRemoteOnroadCycle` requires a one-time ConfirmDialog (tici) or slide-to-confirm (mici) |
| Auto-clear on restart | `OnroadCyclePendingRemote` has `CLEAR_ON_MANAGER_START` flag |

### Adding a new cycle-requiring setting

1. Add `"needs_onroad_cycle": true` to the item in `settings_ui.json`
2. No other changes needed -- sunnylinkd loads the set at startup from the JSON

---

## FAQ

**Q: Do I need to modify any frontend code?**
No. The frontend renders whatever the schema contains. All UI changes are made through `settings_ui.json`.

**Q: When does the frontend pick up my changes?**
At device boot, the generator reads `settings_ui.json`, compresses it, and writes to the `SettingsSchema` param. The frontend fetches this when it connects to the device.

**Q: What's the difference between `visibility` and `enablement`?**
- `visibility`: hidden entirely when rules fail (user doesn't know it exists)
- `enablement`: visible but grayed out when rules fail (user sees it but can't change it)

**Q: How do I test my changes locally?**
Run the generator directly to see the full output:
```bash
python sunnypilot/sunnylink/tools/generate_settings_schema.py
```

**Q: What happens if I add a key that doesn't exist in params_keys.h?**
The validator warns about it. The frontend will render the item but won't be able to read/write the value.
