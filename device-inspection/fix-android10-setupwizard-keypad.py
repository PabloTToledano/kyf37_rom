"""KYF37 owner item 2: keypad-operable first-run wizard (LineageSetupWizard). Idempotent; WSL Python 3.

 * BaseSetupWizardActivity: every clickable-but-not-focusable view (date/time rows, privacy rows, SIM rows) becomes
   focusable (D-pad reachable, themed selection drawn by the framework); after resume focus goes to the Next button
   when nothing (or only Back) has focus, so OK = Next on pages without a list; lists (language, time zone, Wi-Fi)
   keep first focus on the list. Menu/F1 = Next. Back/Clear = previous page (existing).
 * Shorter flow (res/raw/lineage_wizard_script.xml): Welcome, Language, Date/time (+time zone), Wi-Fi, Finish.
   Dropped as meaningless on this keypad phone: Bluetooth intro, SIM / mobile data pages (no cellular yet),
   privacy/metrics page, biometric, screen-lock (set in Settings), restore-from-backup. A copy of the original script
   is kept as lineage_wizard_script.xml.orig-kyf37.
"""
from pathlib import Path
SW = Path('/home/pablo/kyf37-android10/packages/apps/SetupWizard')
b = SW / 'src/org/lineageos/setupwizard/BaseSetupWizardActivity.java'
s = b.read_text()
if 'kyf37MakeFocusable' not in s:
    anchor = "    protected void onNextPressed() {"
    code = '''    // --- Kyf37 keypad support -------------------------------------------------------------
    private void kyf37MakeFocusable(View v) {
        if (v.isClickable() && !v.isFocusable() && v.isEnabled()) v.setFocusable(true);
        if (v instanceof android.view.ViewGroup) {
            android.view.ViewGroup g = (android.view.ViewGroup) v;
            for (int i = 0; i < g.getChildCount(); i++) kyf37MakeFocusable(g.getChildAt(i));
        }
    }

    @Override
    public void onContentChanged() {
        super.onContentChanged();
        kyf37MakeFocusable(getWindow().getDecorView());
    }

    private void kyf37InitialFocus() {
        if (mNavigationBar == null) return;
        mNavigationBar.post(() -> {
            View f = getCurrentFocus();
            Button next = mNavigationBar.getNextButton();
            if ((f == null || f == mNavigationBar.getBackButton()) && next != null
                    && next.getVisibility() == View.VISIBLE && next.isEnabled()) {
                next.requestFocus();
            }
        });
    }

    @Override
    public boolean onKeyDown(int keyCode, android.view.KeyEvent event) {
        if (event.getRepeatCount() == 0 && (keyCode == android.view.KeyEvent.KEYCODE_MENU
                || keyCode == android.view.KeyEvent.KEYCODE_F1) && mNavigationBar != null
                && mNavigationBar.getNextButton().isEnabled()) {
            onNextPressed();
            return true;
        }
        return super.onKeyDown(keyCode, event);
    }

'''
    assert anchor in s
    s = s.replace(anchor, code + anchor, 1)
    old = "        super.onResume();\n        if (mIsGoingBack) {"
    assert old in s
    s = s.replace(old, "        super.onResume();\n        kyf37InitialFocus();\n        if (mIsGoingBack) {", 1)
    b.write_text(s)
    print('patched BaseSetupWizardActivity')

ws = SW / 'res/raw/lineage_wizard_script.xml'
orig = SW / 'res/raw/lineage_wizard_script.xml.orig-kyf37'
if not orig.exists():
    orig.write_text(ws.read_text())
head = orig.read_text().split('<WizardScript')[0]
new = head + '''<WizardScript xmlns:wizard="http://schemas.android.com/apk/res/com.google.android.setupwizard"
    wizard:firstAction="welcome">

    <WizardAction wizard:uri="intent:#Intent;action=org.lineageos.setupwizard.LINEAGE_WELCOME;end" id="welcome">
        <result wizard:action="locale" />
    </WizardAction>
    <WizardAction wizard:uri="intent:#Intent;action=org.lineageos.setupwizard.LINEAGE_LOCALE;end" id="locale">
        <result wizard:action="datetime" />
    </WizardAction>
    <WizardAction wizard:uri="intent:#Intent;action=org.lineageos.setupwizard.LINEAGE_DATETIME;end" id="datetime">
        <result wizard:action="wifi_setup" />
    </WizardAction>
    <WizardAction wizard:uri="intent:#Intent;action=org.lineageos.setupwizard.LINEAGE_WIFI_SETUP;end" id="wifi_setup">
        <result wizard:resultCode="1" wizard:action="finish" wizard:name="no_sim" />
        <result wizard:action="finish" />
    </WizardAction>
    <WizardAction wizard:uri="intent:#Intent;action=org.lineageos.setupwizard.LINEAGE_SETUP_COMPLETE;end" id="finish">
        <result wizard:action="exit" />
    </WizardAction>
    <WizardAction wizard:uri="intent:#Intent;action=org.lineageos.setupwizard.EXIT;end" id="exit" />

</WizardScript>
'''
if ws.read_text() != new:
    ws.write_text(new)
    print('wizard script shortened')
