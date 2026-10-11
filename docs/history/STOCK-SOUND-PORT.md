# Original flipphone feedback

Authoritative evidence: stock `android.policy.dex`, disassembled into
`/home/pablo/kyf37-rom/stock-policy-smali` from the extracted stock boot OAT.

PhoneWindowManager.loadFolderSound loads `/system/media/audio/ui/open.mp3`
and `close.mp3` into SoundPool. Playback methods use independent System
settings `open_sound_enabled` and `close_sound_enabled`; both suppress
playback during the minimal decryption framework and while Telecom is ringing.

Physical buttons use a separate `key_sounds_enabled` setting. Stock init
explicitly disables generic `sound_effects_enabled`, so merely enabling
generic UI clicks would change behavior and may create duplicate sounds.
playKeySound acts on key-down when interactive or a wake key. It respects
window suppression flags for all keys, number keys, and D-pad keys. It skips
music playback, recording, muted STREAM_SYSTEM, and zero system volume,
then posts mPlayKeySoundRunnable to the policy handler.

The preparation generator now preserves all OEM UI recordings by explicit
product-copy entries. This change has not yet been applied to the running
build tree. Playback integration and physical verification remain pending;
the presence of recordings alone does not implement feedback.

Stock mPlayKeySoundRunnable directly calls IAudioService.playSoundEffect(0),
the standard click index, bypassing the generic UI-click setting.

Kyf37Feedback.java implements a STREAM_SYSTEM SoundPool for lid recordings,
the original independent settings, ringing/decryption suppression, and
direct IAudioService click playback for physical key downs. Recording and
music suppression uses Android 7 APIs. Ringer mode and stream mute/volume
are checked. Missing OEM settings default enabled to satisfy the requested
feedback on fresh userdata; explicit saved zero values are honored.

Source compiled successfully with JDK8 against the actual rebuilt Android7
framework classes.jar. integrate-kyf37-feedback.py applies model-only policy
hooks and verifies copied recording bytes. It refuses to mutate the tree
while the ROM build is active; integration is queued. Runtime still pending.

Original per-window key suppression flags are not implemented in this port
yet. Generic view clicks are disabled on initialization and user switches
to prevent a second sound after the physical click. No feedback is requested
for injected or fallback events. This remains queued, not runtime verified.
