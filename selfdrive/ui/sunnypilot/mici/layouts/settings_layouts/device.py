from openpilot.selfdrive.ui.mici.layouts.settings.device import DeviceLayoutMici
from openpilot.selfdrive.ui.mici.widgets.button import BigCircleButton
from openpilot.selfdrive.ui.mici.widgets.dialog import BigDialog, BigConfirmationDialog
from openpilot.selfdrive.ui.ui_state import ui_state
from openpilot.system.ui.lib.application import gui_app
from openpilot.system.ui.lib.multilang import tr

ICON_SIZE = 110

class DeviceLayoutMiciSP(DeviceLayoutMici):
  def __init__(self):
    super().__init__()

    self.icon_enable = gui_app.texture("../../sunnypilot/selfdrive/assets/icons_mici/always_offroad.png", ICON_SIZE,
                                  ICON_SIZE)
    self.icon_disable = gui_app.texture("../../sunnypilot/selfdrive/assets/icons_mici/disable_offroad.png", ICON_SIZE,
                                   ICON_SIZE)
    self.icon_lkas = gui_app.texture("icons_mici/settings/device/lkas.png", ICON_SIZE, ICON_SIZE)

    self._enable_offroad = BigCircleButton(self.icon_enable, red=True)
    self._enable_offroad.set_click_callback(self._handle_always_offroad)

    self._disable_offroad = BigCircleButton(self.icon_disable, red=False)
    self._disable_offroad.set_click_callback(self._handle_always_offroad)

    items = self._scroller._items.copy()

    items.insert(len(self._scroller._items) - 2, self._enable_offroad)
    items.insert(len(self._scroller._items) - 2, self._disable_offroad)

    self._scroller._items.clear()
    for item in items:
      self._scroller.add_widget(item)

  def _handle_always_offroad(self):
    if ui_state.engaged:
      gui_app.push_widget(BigDialog(tr("disengage"),tr("\nto enable always offroad")))
      return

    def _enable_always_offroad():
      if not ui_state.engaged:
        ui_state.params.put_bool("OffroadMode", True)
        ui_state.always_offroad = True

    def _disable_always_offroad():
      ui_state.params.put_bool("OffroadMode", False)
      ui_state.always_offroad = False

    if ui_state.params.get_bool("OffroadMode"):
      dlg = BigConfirmationDialog(tr("slide to exit always offroad"), self.icon_lkas, red=True, confirm_callback=_disable_always_offroad)
    else:
      dlg = BigConfirmationDialog(tr("slide to enable always offroad"), self.icon_lkas, red=True, confirm_callback=_enable_always_offroad)
    gui_app.push_widget(dlg)

  def _update_state(self):
    super()._update_state()

    # Handle Always Offroad buttons
    always_offroad = ui_state.always_offroad
    self._enable_offroad.set_visible(not always_offroad)
    self._disable_offroad.set_visible(always_offroad)
