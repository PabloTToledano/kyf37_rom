# Visible keypad focus — 2026-10-09

Framework/native Android View focus now uses an 8dp dark outer edge, a 4dp yellow
outline and a solid corner marker. Selected native ListView rows get the same
outline. SystemUI logical notification/tile selections use a dark/yellow layered
border with a blue tinted interior. Theme selection and wallpaper do not alter it.
Custom renderers that expose no native View focus (for example a canvas app) do
not automatically acquire semantic selection; this patch cannot invent controls.

Quick Settings navigation follows actual tile geometry; F2/Menu uses the actual
QS expansion state, and the first visible tile is highlighted automatically after
opening QS. Native click listeners continue to perform toggle actions.

Reproduction: fix-android10-keypad-panel.py, then
fix-android10-visible-focus.py. Build framework SystemUI through build-locked.sh.
The framework/SystemUI build passed in 9:14; final panel build passed in 2:53.

These files are build artifacts, not a flash ZIP. The framework change belongs
in the next validated ROM image with matching ART boot-classpath artifacts. Do
not replace framework.jar alone on the running phone. SystemUI.apk can use the
existing SystemUI installer in a future exclusive phone session.

**Not installed.** The owner requested continuing offline while another session
was operating the phone despite the cooperative lock. Own lock was released.
Global focus rendering and the latest QS navigation have not been hardware-tested.
