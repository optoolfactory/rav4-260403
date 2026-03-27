"""
Copyright (c) 2021-, Haibin Wen, sunnypilot, and a number of other contributors.

This file is part of sunnypilot and is licensed under the MIT License.
See the LICENSE.md file in the root directory for more details.
"""
import json

from cereal import car, custom, messaging
from opendbc.sunnypilot.car.tesla.values import TeslaFlagsSP
from openpilot.common.params import Params
from openpilot.common.swaglog import cloudlog
from openpilot.system.hardware import HARDWARE


# All capability fields that rules may reference.
# String-typed fields must have defaults in CAPABILITY_DEFAULTS.
CAPABILITY_FIELDS = (
  "has_longitudinal_control",
  "has_icbm",
  "icbm_available",
  "torque_allowed",
  "brand",
  "pcm_cruise",
  "alpha_long_available",
  "steer_control_type",
  "enable_bsm",
  "is_release",
  "is_sp_release",
  "is_development",
  "tesla_has_vehicle_bus",
  "has_stop_and_go",
  "stock_longitudinal",
  "device_type",
)

CAPABILITY_LABELS: dict[str, str] = {
  "has_longitudinal_control": "sunnypilot longitudinal control",
  "has_icbm": "ICBM enabled",
  "icbm_available": "ICBM available",
  "torque_allowed": "torque steering (not available for angle steering vehicles)",
  "brand": "Vehicle brand",
  "pcm_cruise": "PCM cruise",
  "alpha_long_available": "Alpha Longitudinal available",
  "steer_control_type": "Steer control type",
  "enable_bsm": "BSM available",
  "is_release": "Release branch",
  "is_sp_release": "SP release branch",
  "is_development": "Development branch",
  "tesla_has_vehicle_bus": "Tesla vehicle bus",
  "has_stop_and_go": "Stop and Go",
  "stock_longitudinal": "stock longitudinal",
  "device_type": "Device type",
}

# Explicit defaults for non-boolean capability fields
CAPABILITY_DEFAULTS: dict[str, bool | str] = {
  "brand": "",
  "steer_control_type": "",
  "device_type": "",
}


def generate_capabilities(params: Params | None = None) -> dict:
  """Generate a SettingsCapabilities dict from CarParams + boolean params.

  This mirrors the logic in UIState.update_params() and UIStateSP.update_params()
  to derive the same boolean capabilities that the device-side Python UI uses for
  visibility/enablement gating.

  Two-phase initialization:
  1. All fields initialized to defaults (False for booleans, "" for strings)
  2. Boolean-param fields overwritten unconditionally (no CarParams dependency)
  3. CarParams-derived fields overwritten if CarParams available
  """
  params = params or Params()

  caps: dict = {field: CAPABILITY_DEFAULTS.get(field, False) for field in CAPABILITY_FIELDS}

  # Phase 2: Hardware + boolean params (no CarParams dependency)
  caps["device_type"] = HARDWARE.get_device_type()
  caps["is_release"] = params.get_bool("IsReleaseBranch")
  caps["is_sp_release"] = params.get_bool("IsReleaseSpBranch")
  caps["is_development"] = params.get_bool("IsDevelopmentBranch")
  caps["stock_longitudinal"] = params.get_bool("ToyotaEnforceStockLongitudinal")

  # Phase 3: CarParams-derived capabilities
  CP_bytes = params.get("CarParamsPersistent")
  if CP_bytes is not None:
    try:
      CP = messaging.log_from_bytes(CP_bytes, car.CarParams)
      caps["alpha_long_available"] = bool(CP.alphaLongitudinalAvailable)
      if CP.alphaLongitudinalAvailable:
        caps["has_longitudinal_control"] = params.get_bool("AlphaLongitudinalEnabled")
      else:
        caps["has_longitudinal_control"] = bool(CP.openpilotLongitudinalControl)
      caps["torque_allowed"] = CP.lateralTuning.which() == "torque"
      caps["brand"] = str(CP.brand) if CP.brand else ""
      caps["pcm_cruise"] = bool(CP.pcmCruise)
      caps["steer_control_type"] = str(CP.lateralTuning.which())
      caps["enable_bsm"] = bool(CP.enableBsm)
      # Simplified check; the device UI does a platform-level lookup for Subaru
      caps["has_stop_and_go"] = bool(CP.openpilotLongitudinalControl)
    except Exception:
      cloudlog.exception("capabilities: failed to deserialize CarParamsPersistent")

  # CarParamsSP-derived capabilities
  CP_SP_bytes = params.get("CarParamsSPPersistent")
  if CP_SP_bytes is not None:
    try:
      CP_SP = messaging.log_from_bytes(CP_SP_bytes, custom.CarParamsSP)
      caps["icbm_available"] = bool(CP_SP.intelligentCruiseButtonManagementAvailable)
      caps["has_icbm"] = bool(CP_SP.intelligentCruiseButtonManagementAvailable) and params.get_bool("IntelligentCruiseButtonManagement")
      caps["tesla_has_vehicle_bus"] = bool(CP_SP.flags & TeslaFlagsSP.HAS_VEHICLE_BUS)
    except Exception:
      cloudlog.exception("capabilities: failed to deserialize CarParamsSPPersistent")

  return caps


def generate_capabilities_json(params: Params | None = None) -> str:
  """Generate SettingsCapabilities as a JSON string."""
  return json.dumps(generate_capabilities(params), separators=(",", ":"))
