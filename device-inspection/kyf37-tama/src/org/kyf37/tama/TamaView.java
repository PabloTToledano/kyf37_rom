package org.kyf37.tama;

import android.app.AlertDialog;
import android.content.Context;
import android.graphics.Bitmap;
import android.graphics.Canvas;
import android.graphics.Color;
import android.graphics.LinearGradient;
import android.graphics.Paint;
import android.graphics.Path;
import android.graphics.Rect;
import android.graphics.RectF;
import android.graphics.Shader;
import android.graphics.Typeface;
import android.media.AudioManager;
import android.media.ToneGenerator;
import android.os.Handler;
import android.os.SystemClock;
import android.view.KeyEvent;
import android.view.View;
import android.widget.EditText;
import java.util.ArrayList;
import java.util.Calendar;
import java.util.Random;

/** The whole game: scene, menus and the two mini games. Designed for a D-pad + keypad (no touch). */
final class TamaView extends View {
    private static final int S_MAIN = 0, S_GUESS = 1, S_CATCH = 2;
    private static final int M_NONE = 0, M_FEED = 1, M_PLAY = 2, M_WEAR = 3, M_INFO = 4, M_SET = 5, M_CONFIRM = 6;
    private static final String[] LABEL = { "Feed", "Play", "Clean", "Lights", "Heal", "Wear", "Status", "Setup" };
    private static final int INK = 0xFF2A2F55, PANEL = 0xF2F4F7FF, ACCENT = 0xFF1E6FD9, SOFT = 0xFFD8E2FF;

    private final Tama activity;
    private final Pet pet = new Pet();
    private final Handler handler = new Handler();
    private final Paint P = new Paint(Paint.ANTI_ALIAS_FLAG);
    private final Paint PX = new Paint(); // pixel art, no AA
    private final Bitmap art = Bitmap.createBitmap(48, 48, Bitmap.Config.ARGB_8888);
    private final Canvas artCanvas = new Canvas(art);
    private final Random rnd = new Random();
    private ToneGenerator tone;

    private int state = S_MAIN;
    private int sel;              // main menu selection 0..7
    private int menuKind = M_NONE, menuSel;
    private String menuTitle = "";
    private final ArrayList<String> menuItems = new ArrayList<String>();
    private String msg = "";
    private long msgUntil;
    private long lastTick, lastFrame;
    private int frame;
    private boolean running;
    private boolean dialogOpen;
    private long actionAnimUntil;
    private int actionAnim;       // 0 none, 1 eat, 2 happy, 3 clean sparkle
    private final ArrayList<float[]> hearts = new ArrayList<float[]>();

    // guess game
    private int gRound, gWins, gShown, gHidden, gPhase; // phase 0 ask, 1 reveal
    private boolean gLast;
    private long gRevealUntil;
    // catch game
    private float cX = 0.5f;
    private int cScore, cMiss;
    private long cEnd, cNextSpawn;
    private final ArrayList<float[]> cItems = new ArrayList<float[]>(); // x, y, type (0 food,1 bad), speed
    private boolean cLeft, cRight;

    TamaView(Tama a) {
        super(a);
        activity = a;
        setFocusable(true);
        setFocusableInTouchMode(false);
        PX.setAntiAlias(false);
        PX.setFilterBitmap(false);
        pet.load(a.store());
        pet.catchUp(System.currentTimeMillis());
        try { tone = new ToneGenerator(AudioManager.STREAM_MUSIC, 40); } catch (RuntimeException e) { tone = null; }
        if (pet.stage() == Pet.EGG) say("Press OK to warm the egg.", 4000);
        else say("Welcome back, " + pet.name + "!", 3000);
    }

    // ------------------------------------------------------------------ lifecycle / loop
    void resumeGame() {
        pet.catchUp(System.currentTimeMillis());
        running = true;
        lastTick = SystemClock.elapsedRealtime();
        handler.removeCallbacks(loop);
        handler.post(loop);
        flushEvent();
    }

    void pauseGame() {
        running = false;
        handler.removeCallbacks(loop);
        pet.lastMs = System.currentTimeMillis();
        pet.save(activity.store());
        if (tone != null) { tone.release(); tone = null; }
    }

    private final Runnable loop = new Runnable() { public void run() {
        if (!running) return;
        long now = SystemClock.elapsedRealtime();
        if (state == S_MAIN && now - lastTick >= 1000) {
            double dtMin = (now - lastTick) / 60000.0 * pet.speed;
            lastTick = now;
            while (dtMin > 0) { double d = Math.min(1.0, dtMin); pet.step(d); dtMin -= d; }
            pet.lastMs = System.currentTimeMillis();
            flushEvent();
            if (pet.needName && !dialogOpen) askName();
            if (frame % 40 == 0) pet.save(activity.store());
        } else if (state != S_MAIN) lastTick = now;
        if (now - lastFrame >= 50) { lastFrame = now; frame++; tickGames(now); }
        invalidate();
        handler.postDelayed(this, 50);
    } };

    private void flushEvent() {
        if (!pet.event.isEmpty()) { say(pet.event, 4000); beep(1); pet.event = ""; }
    }

    private void say(String s, long ms) { msg = s; msgUntil = SystemClock.elapsedRealtime() + ms; }

    private void beep(int kind) {
        if (!pet.sound || tone == null) return;
        try {
            tone.startTone(kind == 0 ? ToneGenerator.TONE_PROP_BEEP : (kind == 1 ? ToneGenerator.TONE_PROP_ACK : ToneGenerator.TONE_PROP_NACK), 90);
        } catch (RuntimeException ignored) { }
    }

    private void askName() {
        dialogOpen = true;
        final EditText edit = new EditText(getContext());
        edit.setSingleLine(true);
        edit.setText(pet.name);
        edit.setSelectAllOnFocus(true);
        edit.setFilters(new android.text.InputFilter[] { new android.text.InputFilter.LengthFilter(12) });
        new AlertDialog.Builder(getContext()).setTitle("Name your pet").setView(edit).setCancelable(false)
            .setPositiveButton("OK", (d, w) -> {
                String n = edit.getText().toString().trim();
                if (!n.isEmpty()) pet.name = n;
                pet.needName = false; dialogOpen = false; pet.save(activity.store());
                say("Hello, " + pet.name + "!", 3000);
            }).show();
    }

    // ------------------------------------------------------------------ input
    boolean onBack() {
        if (menuKind != M_NONE) { closeMenu(); return true; }
        if (state != S_MAIN) { state = S_MAIN; return true; }
        return false;
    }

    boolean onGameKeyUp(int code, KeyEvent e) {
        if (code == KeyEvent.KEYCODE_DPAD_LEFT || code == KeyEvent.KEYCODE_4) cLeft = false;
        if (code == KeyEvent.KEYCODE_DPAD_RIGHT || code == KeyEvent.KEYCODE_6) cRight = false;
        return false;
    }

    boolean onGameKey(int code, KeyEvent e) {
        if (dialogOpen) return false;
        boolean first = e.getRepeatCount() == 0;
        if (state == S_CATCH) {
            if (code == KeyEvent.KEYCODE_DPAD_LEFT || code == KeyEvent.KEYCODE_4) { cLeft = true; return true; }
            if (code == KeyEvent.KEYCODE_DPAD_RIGHT || code == KeyEvent.KEYCODE_6) { cRight = true; return true; }
            return false;
        }
        if (state == S_GUESS) {
            if (!first) return true;
            if (gPhase == 0 && (code == KeyEvent.KEYCODE_DPAD_LEFT || code == KeyEvent.KEYCODE_4)) { guess(false); return true; }
            if (gPhase == 0 && (code == KeyEvent.KEYCODE_DPAD_RIGHT || code == KeyEvent.KEYCODE_6)) { guess(true); return true; }
            return false;
        }
        if (menuKind != M_NONE) return menuKey(code, first);
        if (!first && code != KeyEvent.KEYCODE_DPAD_LEFT && code != KeyEvent.KEYCODE_DPAD_RIGHT
            && code != KeyEvent.KEYCODE_DPAD_UP && code != KeyEvent.KEYCODE_DPAD_DOWN) return true;
        switch (code) {
            case KeyEvent.KEYCODE_DPAD_LEFT: sel = (sel + 7) % 8 == 3 && sel % 4 == 0 ? sel + 3 : (sel % 4 == 0 ? sel + 3 : sel - 1); return true;
            case KeyEvent.KEYCODE_DPAD_RIGHT: sel = sel % 4 == 3 ? sel - 3 : sel + 1; return true;
            case KeyEvent.KEYCODE_DPAD_UP:
            case KeyEvent.KEYCODE_DPAD_DOWN: sel = (sel + 4) % 8; return true;
            case KeyEvent.KEYCODE_DPAD_CENTER:
            case KeyEvent.KEYCODE_ENTER:
                if (pet.stage() == Pet.EGG) { warmEgg(); return true; }
                act(sel); return true;
            case KeyEvent.KEYCODE_MENU:
            case KeyEvent.KEYCODE_F1: act(6); return true;
            case KeyEvent.KEYCODE_POUND: act(3); return true;
            default:
                if (code >= KeyEvent.KEYCODE_1 && code <= KeyEvent.KEYCODE_8) {
                    sel = code - KeyEvent.KEYCODE_1;
                    if (pet.stage() == Pet.EGG) { warmEgg(); return true; }
                    act(sel); return true;
                }
        }
        return false;
    }

    private void warmEgg() {
        pet.eggTaps++;
        pet.ageMin += 0.2;
        actionAnim = 2; actionAnimUntil = SystemClock.elapsedRealtime() + 400;
        beep(0);
        if (pet.stage() != Pet.EGG) { pet.needName = true; say("It hatched!", 3000); beep(1); }
        else say("Warm... " + (int) Math.min(99, pet.ageMin / 2 * 100) + "%", 1500);
    }

    private void act(int a) {
        if (pet.stage() == Pet.EGG) { warmEgg(); return; }
        String r = "";
        switch (a) {
            case 0: openMenu(M_FEED, "Feed", "Meal", "Snack", "Treat"); return;
            case 1:
                if (pet.sleeping()) { say(pet.name + " is asleep.", 2000); return; }
                openMenu(M_PLAY, "Play", "Guess (higher/lower)", "Catch the food"); return;
            case 2: r = pet.clean(); if (r.startsWith("Squeaky")) { actionAnim = 3; actionAnimUntil = SystemClock.elapsedRealtime() + 1500; } break;
            case 3: r = pet.toggleLights(); break;
            case 4: r = pet.heal(); break;
            case 5: openWear(); return;
            case 6: openInfo(); return;
            case 7: openSettings(); return;
        }
        if (!r.isEmpty()) { say(r, 2500); beep(r.contains("not") || r.contains("asleep") || r.contains("Already") ? 2 : 1); }
    }

    private void openMenu(int kind, String title, String... items) {
        menuKind = kind; menuTitle = title; menuSel = 0;
        menuItems.clear();
        for (String s : items) menuItems.add(s);
    }

    private void closeMenu() { menuKind = M_NONE; }

    private void openWear() {
        String[] it = new String[Pet.ITEM_NAME.length];
        for (int i = 0; i < it.length; i++) it[i] = wearLine(i);
        openMenu(M_WEAR, "Wardrobe  ·  " + pet.coins + " coins", it);
    }

    private String wearLine(int i) {
        boolean own = (pet.owned & (1 << i)) != 0;
        return Pet.ITEM_NAME[i] + (own ? ((pet.worn & (1 << i)) != 0 ? "   (wearing)" : "   (owned)") : "   " + Pet.ITEM_COST[i] + " coins");
    }

    private void openInfo() {
        int st = pet.stage();
        long mins = (long) pet.ageMin;
        String age = mins >= 1440 ? (mins / 1440) + "d " + (mins % 1440) / 60 + "h" : (mins >= 60 ? (mins / 60) + "h " + (mins % 60) + "m" : mins + "m");
        openMenu(M_INFO, pet.name,
            "Stage: " + Pet.STAGE_NAME[st] + (pet.form >= 0 && st == Pet.ADULT ? " (" + Pet.FORM_NAME[pet.form] + ")" : ""),
            "Age: " + age,
            "Hunger: " + (int) pet.fullness + "%   Joy: " + (int) pet.happy + "%",
            "Clean: " + (int) pet.hygiene + "%   Energy: " + (int) pet.energy + "%",
            "Bond: " + pet.bond + "   Coins: " + pet.coins,
            "Care mistakes: " + pet.mistakes,
            pet.sick ? "Status: sick" : "Status: healthy");
    }

    private void openSettings() {
        openMenu(M_SET, "Setup", "Speed: x" + pet.speed + " (OK to change)", "Sound: " + (pet.sound ? "on" : "off"), "Start a new pet");
    }

    private boolean menuKey(int code, boolean first) {
        int n = menuItems.size();
        switch (code) {
            case KeyEvent.KEYCODE_DPAD_UP: menuSel = (menuSel + n - 1) % n; return true;
            case KeyEvent.KEYCODE_DPAD_DOWN: menuSel = (menuSel + 1) % n; return true;
            case KeyEvent.KEYCODE_DPAD_CENTER:
            case KeyEvent.KEYCODE_ENTER: if (first) menuPick(menuSel); return true;
            default:
                if (code >= KeyEvent.KEYCODE_1 && code <= KeyEvent.KEYCODE_9 && first && code - KeyEvent.KEYCODE_1 < n && menuKind != M_INFO) {
                    menuSel = code - KeyEvent.KEYCODE_1; menuPick(menuSel); return true;
                }
        }
        return false;
    }

    private void menuPick(int i) {
        int kind = menuKind;
        switch (kind) {
            case M_FEED: {
                closeMenu();
                String r = pet.feed(i);
                if (!r.isEmpty()) { say(r, 2500); }
                boolean ok = r.startsWith("Yum") || r.startsWith("Snack") || r.startsWith("A sweet");
                if (ok) { actionAnim = 1; actionAnimUntil = SystemClock.elapsedRealtime() + 1600; }
                beep(ok ? 1 : 2);
                break;
            }
            case M_PLAY:
                closeMenu();
                if (pet.energy < 12) { say(pet.name + " is too tired.", 2500); beep(2); return; }
                if (i == 0) startGuess(); else startCatch();
                break;
            case M_WEAR: {
                String r = pet.wear(i);
                say(r, 2500); beep(r.startsWith("Not") ? 2 : 1);
                openWear(); menuSel = i;
                break;
            }
            case M_SET:
                if (i == 0) { pet.speed = pet.speed == 1 ? 10 : (pet.speed == 10 ? 60 : 1); openSettings(); menuSel = 0; }
                else if (i == 1) { pet.sound = !pet.sound; openSettings(); menuSel = 1; }
                else openMenu(M_CONFIRM, "Really start over?", "No, keep " + pet.name, "Yes, new egg");
                break;
            case M_CONFIRM:
                closeMenu();
                if (i == 1) { pet.reset(activity.store()); say("A new egg appeared.", 3000); }
                break;
            default: closeMenu();
        }
    }

    // ------------------------------------------------------------------ guess game
    private void startGuess() {
        state = S_GUESS; gRound = 0; gWins = 0; gPhase = 0; nextCard();
    }
    private void nextCard() { gShown = 2 + rnd.nextInt(7); do { gHidden = 1 + rnd.nextInt(9); } while (gHidden == gShown); gPhase = 0; }
    private void guess(boolean higher) {
        gLast = (gHidden > gShown) == higher;
        if (gLast) gWins++;
        gPhase = 1; gRevealUntil = SystemClock.elapsedRealtime() + 1100;
        beep(gLast ? 1 : 2);
    }
    private void finishGuess() {
        boolean win = gWins >= 3;
        pet.playReward(win ? 1 : 0, win ? 5 : 1);
        say(win ? "You won! " + pet.name + " is thrilled. +5" : "Good try! +1", 3500);
        actionAnim = 2; actionAnimUntil = SystemClock.elapsedRealtime() + 1800;
        state = S_MAIN;
    }

    // ------------------------------------------------------------------ catch game
    private void startCatch() {
        state = S_CATCH; cX = 0.5f; cScore = 0; cMiss = 0; cItems.clear();
        cEnd = SystemClock.elapsedRealtime() + 30000; cNextSpawn = SystemClock.elapsedRealtime() + 600; cLeft = cRight = false;
    }
    private void finishCatch() {
        int coins = Math.max(0, cScore / 3);
        pet.playReward(cScore >= 10 ? 1 : 0, coins);
        say("Caught " + cScore + "!  +" + coins + " coins", 3500);
        actionAnim = 2; actionAnimUntil = SystemClock.elapsedRealtime() + 1800;
        state = S_MAIN;
    }

    private void tickGames(long now) {
        if (state == S_GUESS && gPhase == 1 && now >= gRevealUntil) {
            gRound++;
            if (gRound >= 5) finishGuess(); else nextCard();
        }
        if (state == S_CATCH) {
            if (cLeft) cX -= 0.035f;
            if (cRight) cX += 0.035f;
            cX = Math.max(0.08f, Math.min(0.92f, cX));
            if (now >= cNextSpawn) {
                cNextSpawn = now + 450 + rnd.nextInt(500);
                cItems.add(new float[] { 0.08f + rnd.nextFloat() * 0.84f, 0f, rnd.nextInt(4) == 0 ? 1 : 0, 0.011f + rnd.nextFloat() * 0.008f });
            }
            for (int i = cItems.size() - 1; i >= 0; i--) {
                float[] it = cItems.get(i);
                it[1] += it[3];
                if (it[1] >= 0.86f) {
                    if (Math.abs(it[0] - cX) < 0.12f) {
                        if (it[2] == 0) { cScore++; beep(0); } else { cScore = Math.max(0, cScore - 1); beep(2); }
                    }
                    cItems.remove(i);
                } else if (it[1] > 1f) cItems.remove(i);
            }
            if (now >= cEnd) finishCatch();
        }
        for (int i = hearts.size() - 1; i >= 0; i--) { float[] h = hearts.get(i); h[1] -= 0.004f; h[2] -= 0.02f; if (h[2] <= 0) hearts.remove(i); }
        if (actionAnim == 2 && now < actionAnimUntil && frame % 4 == 0 && hearts.size() < 6)
            hearts.add(new float[] { 0.35f + rnd.nextFloat() * 0.3f, 0.45f, 1f });
        if (now >= actionAnimUntil) actionAnim = 0;
    }

    // ------------------------------------------------------------------ drawing
    @Override protected void onDraw(Canvas c) {
        float W = getWidth(), H = getHeight();
        float s = W / 480f;
        drawBackground(c, W, H, s);
        if (state == S_GUESS) { drawGuess(c, W, H, s); return; }
        if (state == S_CATCH) { drawCatch(c, W, H, s); return; }
        drawHeader(c, W, s);
        drawScene(c, W, H, s);
        drawMessage(c, W, s, H);
        drawMenuGrid(c, W, H, s);
        if (menuKind != M_NONE) drawMenuOverlay(c, W, H, s);
    }

    private boolean dark() { return pet.night() || !pet.lightsOn; }

    private void drawBackground(Canvas c, float W, float H, float s) {
        boolean night = pet.night();
        int top = night ? 0xFF1B2550 : 0xFFB9DCFF, bottom = night ? 0xFF3B3F7A : 0xFFEAF6FF;
        P.setShader(new LinearGradient(0, 0, 0, H, top, bottom, Shader.TileMode.CLAMP));
        c.drawRect(0, 0, W, H, P);
        P.setShader(null);
        if (night) {
            P.setColor(0xFFFFF6C8);
            for (int i = 0; i < 14; i++) c.drawCircle((i * 97 % 460 + 10) * s, (i * 53 % 380 + 40) * s, (i % 3 == 0 ? 2.5f : 1.5f) * s, P);
        } else {
            P.setColor(0xCCFFFFFF);
            float o = (SystemClock.elapsedRealtime() / 90 % 640) * s;
            cloud(c, (80 * s + o) % (W + 160 * s) - 80 * s, 190 * s, s);
            cloud(c, (330 * s + o * 0.6f) % (W + 160 * s) - 80 * s, 270 * s, s * 0.8f);
        }
        // ground
        P.setColor(night ? 0xFF3C5A66 : 0xFFBFE8B2);
        c.drawRect(0, 470 * s, W, 580 * s, P);
        P.setColor(night ? 0xFF2E4752 : 0xFFA6DB98);
        c.drawRect(0, 470 * s, W, 478 * s, P);
    }

    private void cloud(Canvas c, float x, float y, float s) {
        c.drawCircle(x, y, 22 * s, P); c.drawCircle(x + 26 * s, y - 8 * s, 28 * s, P); c.drawCircle(x + 56 * s, y, 22 * s, P);
        c.drawRect(x, y, x + 56 * s, y + 22 * s, P);
    }

    private void drawHeader(Canvas c, float W, float s) {
        int st = pet.stage();
        P.setTypeface(Typeface.create("sans-serif-medium", Typeface.NORMAL));
        P.setTextAlign(Paint.Align.LEFT);
        P.setTextSize(26 * s);
        P.setColor(dark() ? Color.WHITE : INK);
        String title = pet.name + (st == Pet.ADULT && pet.form >= 0 ? " · " + Pet.FORM_NAME[pet.form] : " · " + Pet.STAGE_NAME[st]);
        c.drawText(title, 20 * s, 64 * s, P);
        // coins pill
        String coins = String.valueOf(pet.coins);
        P.setTextSize(22 * s);
        float cw = P.measureText(coins) + 52 * s;
        P.setColor(PANEL);
        c.drawRoundRect(new RectF(W - cw - 16 * s, 36 * s, W - 16 * s, 76 * s), 20 * s, 20 * s, P);
        P.setColor(0xFFF2B63C);
        c.drawCircle(W - cw - 16 * s + 22 * s, 56 * s, 9 * s, P);
        P.setColor(INK);
        c.drawText(coins, W - cw - 16 * s + 38 * s, 64 * s, P);
        // stat bars
        String[] names = { "Food", "Joy", "Clean", "Rest" };
        float[] v = { pet.fullness, pet.happy, pet.hygiene, pet.energy };
        int[] col = { 0xFFFF8A65, 0xFFFF6FAE, 0xFF4FC3F7, 0xFF9575CD };
        float bw = (W - 40 * s - 3 * 10 * s) / 4f;
        for (int i = 0; i < 4; i++) {
            float x = 20 * s + i * (bw + 10 * s), y = 96 * s;
            P.setColor(PANEL);
            c.drawRoundRect(new RectF(x, y, x + bw, y + 44 * s), 14 * s, 14 * s, P);
            P.setTextSize(15 * s);
            P.setColor(INK);
            c.drawText(names[i], x + 10 * s, y + 18 * s, P);
            P.setColor(0xFFDDE3F3);
            c.drawRoundRect(new RectF(x + 10 * s, y + 26 * s, x + bw - 10 * s, y + 36 * s), 5 * s, 5 * s, P);
            P.setColor(v[i] < 25 ? 0xFFE53935 : col[i]);
            c.drawRoundRect(new RectF(x + 10 * s, y + 26 * s, x + 10 * s + (bw - 20 * s) * v[i] / 100f, y + 36 * s), 5 * s, 5 * s, P);
        }
    }

    private void drawScene(Canvas c, float W, float H, float s) {
        int st = pet.stage();
        boolean asleep = pet.sleeping();
        // poops
        for (int i = 0; i < pet.poops; i++) {
            float px = i % 2 == 0 ? 70 * s + i * 14 * s : W - 120 * s - i * 14 * s;
            drawPoop(c, px, 452 * s, s);
        }
        // pet
        int mood = asleep ? 3 : (pet.sick ? 5 : (actionAnim == 1 ? 4 : (actionAnim == 2 || actionAnim == 3 ? 1 : (pet.need().isEmpty() ? (pet.happy > 70 ? 1 : 0) : 2))));
        if (st == Pet.EGG && actionAnim == 2) mood = 0;
        drawPetArt(st, pet.form, mood, (frame / 10) % 2, pet.worn);
        float size = 290 * s;
        float cx = W / 2f, bottom = 466 * s;
        float wob = (st == Pet.EGG && actionAnim == 2) ? (float) Math.sin(frame * 1.2) * 6 * s : 0;
        Rect src = new Rect(0, 0, 48, 48);
        RectF dst = new RectF(cx - size / 2 + wob, bottom - size, cx + size / 2 + wob, bottom);
        if (dark() && !asleep) PX.setColorFilter(null);
        c.drawBitmap(art, src, dst, PX);
        // sleeping zzz
        if (asleep) {
            P.setColor(Color.WHITE);
            P.setTextSize(34 * s);
            P.setTypeface(Typeface.DEFAULT_BOLD);
            float zy = 220 * s - (frame % 40) * 1.2f * s;
            c.drawText("z", cx + 70 * s, 250 * s + zy * 0.2f, P);
            P.setTextSize(24 * s);
            c.drawText("z", cx + 100 * s, 215 * s + zy * 0.2f, P);
        }
        // bubble: want / need
        if (!asleep && st != Pet.EGG && pet.want != Pet.WANT_NONE) drawWantBubble(c, cx + 100 * s, 190 * s, s);
        if (pet.sick && !asleep) { P.setColor(0xFF66BB6A); c.drawCircle(cx - 100 * s, 210 * s, 22 * s, P); P.setColor(Color.WHITE); c.drawRect(cx - 108 * s, 207 * s, cx - 92 * s, 213 * s, P); c.drawRect(cx - 103 * s, 202 * s, cx - 97 * s, 218 * s, P); }
        // hearts / sparkles
        if (actionAnim == 3) {
            P.setColor(0xFFFFFFFF);
            for (int i = 0; i < 8; i++) {
                float a = frame * 0.2f + i * 0.8f;
                c.drawCircle(cx + (float) Math.cos(a) * 110 * s, 340 * s + (float) Math.sin(a * 1.3) * 90 * s, (4 + (i % 3) * 2) * s, P);
            }
        }
        for (float[] h : hearts) { P.setColor(0xFFFF6FAE); P.setAlpha((int) (255 * Math.min(1f, h[2]))); heart(c, h[0] * W, h[1] * H, 11 * s); P.setAlpha(255); }
        if (dark() && !asleep) { /* night with lights on: no overlay */ }
        if (asleep) { P.setColor(0xAA101030); c.drawRect(0, 0, W, 580 * s, P); P.setColor(Color.WHITE); P.setTextSize(24 * s); P.setTextAlign(Paint.Align.CENTER); P.setTypeface(Typeface.DEFAULT); c.drawText("Lights off", W / 2f, 150 * s, P); P.setTextAlign(Paint.Align.LEFT); }
    }

    private void drawWantBubble(Canvas c, float x, float y, float s) {
        P.setColor(Color.WHITE);
        c.drawRoundRect(new RectF(x - 34 * s, y - 34 * s, x + 34 * s, y + 30 * s), 18 * s, 18 * s, P);
        Path tail = new Path(); tail.moveTo(x - 14 * s, y + 28 * s); tail.lineTo(x - 30 * s, y + 52 * s); tail.lineTo(x + 2 * s, y + 28 * s); tail.close();
        c.drawPath(tail, P);
        int icon = pet.want == Pet.WANT_FOOD ? 0 : (pet.want == Pet.WANT_PLAY ? 1 : (pet.want == Pet.WANT_CLEAN ? 2 : 3));
        icon(c, icon, x, y - 2 * s, 20 * s, INK);
    }

    private void drawPoop(Canvas c, float x, float y, float s) {
        P.setColor(0xFF7B4B2A);
        c.drawOval(new RectF(x, y + 10 * s, x + 40 * s, y + 34 * s), P);
        c.drawOval(new RectF(x + 6 * s, y, x + 34 * s, y + 20 * s), P);
        c.drawOval(new RectF(x + 12 * s, y - 10 * s, x + 28 * s, y + 8 * s), P);
        P.setColor(Color.WHITE);
        c.drawCircle(x + 14 * s, y + 18 * s, 3 * s, P); c.drawCircle(x + 26 * s, y + 18 * s, 3 * s, P);
        P.setColor(INK);
        c.drawCircle(x + 14 * s, y + 18 * s, 1.4f * s, P); c.drawCircle(x + 26 * s, y + 18 * s, 1.4f * s, P);
    }

    private void heart(Canvas c, float x, float y, float r) {
        c.drawCircle(x - r * 0.55f, y - r * 0.2f, r * 0.62f, P);
        c.drawCircle(x + r * 0.55f, y - r * 0.2f, r * 0.62f, P);
        Path t = new Path(); t.moveTo(x - r * 1.1f, y); t.lineTo(x + r * 1.1f, y); t.lineTo(x, y + r * 1.3f); t.close();
        c.drawPath(t, P);
    }

    private void drawMessage(Canvas c, float W, float s, float H) {
        String text = SystemClock.elapsedRealtime() < msgUntil ? msg : pet.need();
        if (text.isEmpty() && pet.stage() == Pet.EGG) text = "Press OK to warm the egg.";
        if (text.isEmpty()) return;
        P.setTypeface(Typeface.DEFAULT_BOLD);
        P.setTextSize(21 * s);
        P.setTextAlign(Paint.Align.CENTER);
        float tw = Math.min(W - 40 * s, P.measureText(text) + 40 * s);
        P.setColor(ACCENT);
        c.drawRoundRect(new RectF(W / 2f - tw / 2, 494 * s, W / 2f + tw / 2, 540 * s), 23 * s, 23 * s, P);
        P.setColor(Color.WHITE);
        c.drawText(text, W / 2f, 524 * s, P);
        P.setTextAlign(Paint.Align.LEFT);
    }

    private void drawMenuGrid(Canvas c, float W, float H, float s) {
        float tw = (W - 40 * s - 3 * 12 * s) / 4f, th = 104 * s;
        for (int i = 0; i < 8; i++) {
            int col = i % 4, row = i / 4;
            float x = 20 * s + col * (tw + 12 * s), y = 566 * s + row * (th + 12 * s);
            boolean on = i == sel && menuKind == M_NONE;
            P.setColor(on ? ACCENT : PANEL);
            c.drawRoundRect(new RectF(x, y, x + tw, y + th), 22 * s, 22 * s, P);
            if (on) { P.setColor(0xFFFFFFFF); P.setStyle(Paint.Style.STROKE); P.setStrokeWidth(3 * s); c.drawRoundRect(new RectF(x + 3 * s, y + 3 * s, x + tw - 3 * s, y + th - 3 * s), 20 * s, 20 * s, P); P.setStyle(Paint.Style.FILL); }
            icon(c, i, x + tw / 2, y + 40 * s, 24 * s, on ? Color.WHITE : INK);
            P.setTypeface(Typeface.DEFAULT_BOLD);
            P.setTextSize(15 * s);
            P.setTextAlign(Paint.Align.CENTER);
            P.setColor(on ? Color.WHITE : INK);
            c.drawText((i + 1) + " " + LABEL[i], x + tw / 2, y + th - 14 * s, P);
            if (i == 3 && !pet.lightsOn) { P.setColor(0xFFE53935); c.drawCircle(x + tw - 14 * s, y + 14 * s, 6 * s, P); }
            if (i == 4 && pet.sick) { P.setColor(0xFFE53935); c.drawCircle(x + tw - 14 * s, y + 14 * s, 6 * s, P); }
            if (i == 2 && pet.poops > 0) { P.setColor(0xFFE53935); c.drawCircle(x + tw - 14 * s, y + 14 * s, 6 * s, P); }
        }
        P.setTextAlign(Paint.Align.LEFT);
    }

    private void icon(Canvas c, int id, float cx, float cy, float r, int col) {
        P.setColor(col);
        P.setStyle(Paint.Style.FILL);
        switch (id) {
            case 0: // apple
                c.drawCircle(cx - r * 0.25f, cy + r * 0.1f, r * 0.7f, P); c.drawCircle(cx + r * 0.25f, cy + r * 0.1f, r * 0.7f, P);
                c.drawRect(cx - r * 0.06f, cy - r * 0.9f, cx + r * 0.06f, cy - r * 0.4f, P);
                break;
            case 1: // ball
                c.drawCircle(cx, cy, r * 0.85f, P);
                P.setColor(col == Color.WHITE ? ACCENT : Color.WHITE); P.setStyle(Paint.Style.STROKE); P.setStrokeWidth(r * 0.14f);
                c.drawArc(new RectF(cx - r * 0.85f, cy - r * 0.85f, cx + r * 0.85f, cy + r * 0.85f), 200, 140, false, P);
                c.drawLine(cx - r * 0.85f, cy, cx + r * 0.85f, cy, P);
                P.setStyle(Paint.Style.FILL);
                break;
            case 2: { // drop
                Path p = new Path(); p.moveTo(cx, cy - r); p.quadTo(cx + r * 0.9f, cy + r * 0.1f, cx, cy + r * 0.95f); p.quadTo(cx - r * 0.9f, cy + r * 0.1f, cx, cy - r); c.drawPath(p, P); break; }
            case 3: // bulb
                c.drawCircle(cx, cy - r * 0.15f, r * 0.62f, P); c.drawRect(cx - r * 0.3f, cy + r * 0.4f, cx + r * 0.3f, cy + r * 0.85f, P);
                break;
            case 4: // cross
                c.drawRect(cx - r * 0.25f, cy - r * 0.85f, cx + r * 0.25f, cy + r * 0.85f, P); c.drawRect(cx - r * 0.85f, cy - r * 0.25f, cx + r * 0.85f, cy + r * 0.25f, P);
                break;
            case 5: // hat
                c.drawRect(cx - r * 0.5f, cy - r * 0.8f, cx + r * 0.5f, cy + r * 0.3f, P); c.drawRoundRect(new RectF(cx - r * 0.95f, cy + r * 0.2f, cx + r * 0.95f, cy + r * 0.6f), r * 0.2f, r * 0.2f, P);
                break;
            case 6: // bars
                c.drawRect(cx - r * 0.8f, cy, cx - r * 0.4f, cy + r * 0.8f, P); c.drawRect(cx - r * 0.2f, cy - r * 0.5f, cx + r * 0.2f, cy + r * 0.8f, P); c.drawRect(cx + r * 0.4f, cy - r * 0.9f, cx + r * 0.8f, cy + r * 0.8f, P);
                break;
            default: // gear
                c.drawCircle(cx, cy, r * 0.62f, P);
                for (int i = 0; i < 8; i++) { c.save(); c.rotate(i * 45, cx, cy); c.drawRect(cx - r * 0.14f, cy - r * 0.9f, cx + r * 0.14f, cy - r * 0.55f, P); c.restore(); }
                P.setColor(col == Color.WHITE ? ACCENT : PANEL); c.drawCircle(cx, cy, r * 0.25f, P);
        }
    }

    private void drawMenuOverlay(Canvas c, float W, float H, float s) {
        P.setColor(0xAA101030);
        c.drawRect(0, 0, W, H, P);
        int n = menuItems.size();
        float rowH = 58 * s, w = W - 60 * s, h = 80 * s + n * rowH + 16 * s;
        float x = 30 * s, y = Math.max(90 * s, (H - h) / 2f);
        P.setColor(PANEL);
        c.drawRoundRect(new RectF(x, y, x + w, y + h), 28 * s, 28 * s, P);
        P.setTypeface(Typeface.DEFAULT_BOLD);
        P.setTextSize(26 * s);
        P.setColor(INK);
        P.setTextAlign(Paint.Align.LEFT);
        c.drawText(menuTitle, x + 24 * s, y + 52 * s, P);
        for (int i = 0; i < n; i++) {
            float ry = y + 72 * s + i * rowH;
            boolean on = i == menuSel && menuKind != M_INFO;
            if (on) { P.setColor(ACCENT); c.drawRoundRect(new RectF(x + 14 * s, ry, x + w - 14 * s, ry + rowH - 8 * s), 18 * s, 18 * s, P); }
            P.setColor(on ? Color.WHITE : INK);
            P.setTypeface(on ? Typeface.DEFAULT_BOLD : Typeface.DEFAULT);
            P.setTextSize(21 * s);
            String prefix = menuKind == M_INFO ? "" : (i + 1) + "  ";
            c.drawText(prefix + menuItems.get(i), x + 30 * s, ry + 34 * s, P);
        }
    }

    // ------------------------------------------------------------------ mini game drawing
    private void drawGuess(Canvas c, float W, float H, float s) {
        P.setTypeface(Typeface.DEFAULT_BOLD);
        P.setTextAlign(Paint.Align.CENTER);
        P.setColor(INK);
        P.setTextSize(30 * s);
        c.drawText("Guess!", W / 2f, 90 * s, P);
        P.setTextSize(20 * s);
        c.drawText("Round " + (gRound + 1) + "/5   Wins " + gWins, W / 2f, 130 * s, P);
        // cards
        card(c, W / 2f - 130 * s, 260 * s, s, String.valueOf(gShown), true);
        card(c, W / 2f + 130 * s, 260 * s, s, gPhase == 1 ? String.valueOf(gHidden) : "?", gPhase == 1);
        P.setTextSize(22 * s);
        P.setColor(INK);
        if (gPhase == 0) {
            c.drawText("Is the hidden card", W / 2f, 470 * s, P);
            c.drawText("lower or higher?", W / 2f, 500 * s, P);
            P.setColor(ACCENT);
            c.drawRoundRect(new RectF(40 * s, 560 * s, W / 2f - 10 * s, 640 * s), 26 * s, 26 * s, P);
            c.drawRoundRect(new RectF(W / 2f + 10 * s, 560 * s, W - 40 * s, 640 * s), 26 * s, 26 * s, P);
            P.setColor(Color.WHITE);
            c.drawText("◀ Lower (4)", W / 4f + 15 * s, 610 * s, P);
            c.drawText("Higher (6) ▶", W * 3 / 4f - 15 * s, 610 * s, P);
        } else {
            P.setColor(gLast ? 0xFF2E9E5B : 0xFFE53935);
            P.setTextSize(36 * s);
            c.drawText(gLast ? "Correct!" : "Nope!", W / 2f, 520 * s, P);
        }
        P.setTextAlign(Paint.Align.LEFT);
    }

    private void card(Canvas c, float cx, float cy, float s, String t, boolean face) {
        P.setColor(face ? Color.WHITE : 0xFF8E7BE0);
        c.drawRoundRect(new RectF(cx - 80 * s, cy - 110 * s, cx + 80 * s, cy + 110 * s), 22 * s, 22 * s, P);
        P.setColor(face ? INK : Color.WHITE);
        P.setTextSize(90 * s);
        c.drawText(t, cx, cy + 30 * s, P);
    }

    private void drawCatch(Canvas c, float W, float H, float s) {
        P.setTypeface(Typeface.DEFAULT_BOLD);
        P.setTextAlign(Paint.Align.LEFT);
        P.setColor(INK);
        P.setTextSize(26 * s);
        c.drawText("Score " + cScore, 24 * s, 70 * s, P);
        long left = Math.max(0, (cEnd - SystemClock.elapsedRealtime()) / 1000);
        P.setTextAlign(Paint.Align.RIGHT);
        c.drawText(left + "s", W - 24 * s, 70 * s, P);
        P.setTextAlign(Paint.Align.LEFT);
        float top = 100 * s, floor = 740 * s;
        for (float[] it : cItems) {
            float x = it[0] * W, y = top + it[1] * (floor - top);
            if (it[2] == 0) { icon(c, 0, x, y, 20 * s, 0xFFE53935); } else { P.setColor(0xFF455A64); c.drawCircle(x, y, 18 * s, P); P.setColor(Color.WHITE); c.drawCircle(x - 6 * s, y - 4 * s, 3 * s, P); c.drawCircle(x + 6 * s, y - 4 * s, 3 * s, P); }
        }
        drawPetArt(Math.max(Pet.BABY, pet.stage()), pet.form, 1, (frame / 6) % 2, pet.worn);
        float size = 170 * s;
        c.drawBitmap(art, new Rect(0, 0, 48, 48), new RectF(cX * W - size / 2, floor - size + 20 * s, cX * W + size / 2, floor + 20 * s), PX);
        P.setColor(INK);
        P.setTextAlign(Paint.Align.CENTER);
        P.setTextSize(18 * s);
        c.drawText("◀ 4   move   6 ▶    (catch fruit, dodge bombs)", W / 2f, 800 * s, P);
        P.setTextAlign(Paint.Align.LEFT);
    }

    // ------------------------------------------------------------------ pixel art
    private void px(int color, float l, float t, float r, float b) { PX.setColor(color); artCanvas.drawRect(l, t, r, b, PX); }
    private void disc(int color, float cx, float cy, float r) { PX.setColor(color); artCanvas.drawCircle(cx, cy, r, PX); }
    private void ball(int body, float cx, float cy, float r) { disc(0xFF3A3358, cx, cy, r + 1); disc(body, cx, cy, r); }
    private void oval(int body, float cx, float cy, float rx, float ry) {
        PX.setColor(0xFF3A3358); artCanvas.drawOval(new RectF(cx - rx - 1, cy - ry - 1, cx + rx + 1, cy + ry + 1), PX);
        PX.setColor(body); artCanvas.drawOval(new RectF(cx - rx, cy - ry, cx + rx, cy + ry), PX);
    }
    private void tri(int color, float x1, float y1, float x2, float y2, float x3, float y3) {
        Path p = new Path(); p.moveTo(x1, y1); p.lineTo(x2, y2); p.lineTo(x3, y3); p.close();
        PX.setColor(color); PX.setStyle(Paint.Style.FILL); artCanvas.drawPath(p, PX);
    }

    private void face(int mood, float cx, float eyeY, float spread, float mouthY) {
        int ink = 0xFF3A3358;
        float lx = cx - spread, rx = cx + spread;
        switch (mood) {
            case 3: // sleeping
                px(ink, lx - 2, eyeY, lx + 2, eyeY + 1); px(ink, rx - 2, eyeY, rx + 2, eyeY + 1);
                px(ink, cx - 1, mouthY, cx + 1, mouthY + 1);
                return;
            case 1: // happy ^ ^
                px(ink, lx - 2, eyeY + 1, lx - 1, eyeY + 2); px(ink, lx - 1, eyeY, lx + 1, eyeY + 1); px(ink, lx + 1, eyeY + 1, lx + 2, eyeY + 2);
                px(ink, rx - 2, eyeY + 1, rx - 1, eyeY + 2); px(ink, rx - 1, eyeY, rx + 1, eyeY + 1); px(ink, rx + 1, eyeY + 1, rx + 2, eyeY + 2);
                px(ink, cx - 2, mouthY, cx + 2, mouthY + 1); px(ink, cx - 3, mouthY - 1, cx - 2, mouthY); px(ink, cx + 2, mouthY - 1, cx + 3, mouthY);
                break;
            case 5: // sick x x
                for (int i = 0; i < 3; i++) { px(ink, lx - 1 + i, eyeY + i, lx + i, eyeY + i + 1); px(ink, lx + 1 - i, eyeY + i, lx + 2 - i, eyeY + i + 1); px(ink, rx - 1 + i, eyeY + i, rx + i, eyeY + i + 1); px(ink, rx + 1 - i, eyeY + i, rx + 2 - i, eyeY + i + 1); }
                px(ink, cx - 2, mouthY + 1, cx + 2, mouthY + 2);
                break;
            default:
                px(ink, lx - 1, eyeY, lx + 1, eyeY + 3); px(ink, rx - 1, eyeY, rx + 1, eyeY + 3);
                px(0xFFFFFFFF, lx - 1, eyeY, lx, eyeY + 1); px(0xFFFFFFFF, rx - 1, eyeY, rx, eyeY + 1);
                if (mood == 4) { px(ink, cx - 2, mouthY, cx + 2, mouthY + 3); px(0xFFFF8A80, cx - 1, mouthY + 1, cx + 1, mouthY + 3); }
                else if (mood == 2) { px(ink, cx - 2, mouthY + 1, cx + 2, mouthY + 2); px(ink, cx - 3, mouthY + 2, cx - 2, mouthY + 3); px(ink, cx + 2, mouthY + 2, cx + 3, mouthY + 3); px(0xFF7FC8FF, lx - 1, eyeY + 4, lx, eyeY + 6); }
                else { px(ink, cx - 1, mouthY, cx + 1, mouthY + 1); }
        }
        px(0x99FF8FB4, lx - 3, eyeY + 3, lx - 1, eyeY + 4); px(0x99FF8FB4, rx + 1, eyeY + 3, rx + 3, eyeY + 4);
    }

    private void accessories(int worn, float cx, float headTop, float eyeY, float spread) {
        if ((worn & 1) != 0) { tri(0xFFFF6FAE, cx + 5, headTop + 2, cx + 11, headTop - 2, cx + 11, headTop + 6); tri(0xFFFF6FAE, cx + 5, headTop + 2, cx - 1, headTop - 2, cx - 1, headTop + 6); px(0xFFD81B60, cx + 4, headTop + 1, cx + 6, headTop + 4); }
        if ((worn & 2) != 0) { px(0xFF3A3358, cx - 8, headTop - 7, cx + 8, headTop + 1); px(0xFF5A4FA0, cx - 6, headTop - 9, cx + 6, headTop - 6); px(0xFFFF6FAE, cx - 6, headTop - 7, cx + 6, headTop - 6); }
        if ((worn & 4) != 0) { PX.setColor(0xFF3A3358); PX.setStyle(Paint.Style.STROKE); PX.setStrokeWidth(1); artCanvas.drawCircle(cx - spread, eyeY + 1, 3, PX); artCanvas.drawCircle(cx + spread, eyeY + 1, 3, PX); px(0xFF3A3358, cx - spread + 3, eyeY, cx + spread - 3, eyeY + 1); PX.setStyle(Paint.Style.FILL); }
        if ((worn & 8) != 0) { tri(0xFFF2B63C, cx - 8, headTop + 1, cx - 8, headTop - 7, cx - 4, headTop - 2); tri(0xFFF2B63C, cx - 4, headTop + 1, cx, headTop - 9, cx + 4, headTop + 1); tri(0xFFF2B63C, cx + 4, headTop - 2, cx + 8, headTop - 7, cx + 8, headTop + 1); px(0xFFF2B63C, cx - 8, headTop, cx + 8, headTop + 2); px(0xFFE53935, cx - 1, headTop - 4, cx + 1, headTop - 2); }
    }

    /** 48x48 pixel art of the pet, bottom-aligned on y=44. */
    private void drawPetArt(int stage, int form, int mood, int bob, int worn) {
        art.eraseColor(Color.TRANSPARENT);
        PX.setStyle(Paint.Style.FILL);
        // soft shadow
        PX.setColor(0x33000000);
        artCanvas.drawOval(new RectF(10, 41, 38, 46), PX);
        float b = bob;
        switch (stage) {
            case Pet.EGG: {
                oval(0xFFFFF3E0, 24, 28, 11, 14);
                disc(0xFFFFCC80, 20, 22, 2.5f); disc(0xFFFFCC80, 28, 30, 3f); disc(0xFFFFCC80, 21, 34, 2f);
                float prog = (float) Math.min(1, pet.ageMin / 2.0);
                if (prog > 0.35f) { px(0xFF3A3358, 21, 18, 23, 19); px(0xFF3A3358, 23, 19, 25, 20); px(0xFF3A3358, 25, 18, 27, 19); }
                if (prog > 0.7f) { px(0xFF3A3358, 19, 21, 21, 22); px(0xFF3A3358, 27, 21, 30, 22); px(0xFF3A3358, 24, 22, 25, 25); }
                break;
            }
            case Pet.BABY: {
                int col = 0xFF9EE6C9;
                oval(col, 18, 42, 3, 2); oval(col, 30, 42, 3, 2);
                ball(col, 24, 32 + b, 10);
                px(0xFF9EE6C9, 22, 21 + b, 26, 23 + b);
                face(mood, 24, 29 + b, 4, 35 + b);
                accessories(worn, 24, 23 + b, 29 + b, 4);
                break;
            }
            case Pet.CHILD: {
                int col = 0xFF8CC8FF;
                tri(0xFF3A3358, 12, 22, 14, 11, 21, 18); tri(col, 13, 21, 14.5f, 13, 19, 18);
                tri(0xFF3A3358, 36, 22, 34, 11, 27, 18); tri(col, 35, 21, 33.5f, 13, 29, 18);
                oval(col, 17, 42, 4, 2.5f); oval(col, 31, 42, 4, 2.5f);
                ball(col, 24, 30 + b, 12);
                face(mood, 24, 27 + b, 5, 34 + b);
                accessories(worn, 24, 19 + b, 27 + b, 5);
                break;
            }
            case Pet.TEEN: {
                int col = 0xFFC8A8F0;
                tri(0xFF3A3358, 11, 20, 12, 7, 20, 14); tri(col, 12, 19, 13, 9, 19, 14);
                tri(0xFF3A3358, 37, 20, 36, 7, 28, 14); tri(col, 36, 19, 35, 9, 29, 14);
                oval(col, 8, 32 + b, 3, 5); oval(col, 40, 32 + b, 3, 5);
                oval(col, 18, 42, 4.5f, 2.5f); oval(col, 30, 42, 4.5f, 2.5f);
                oval(col, 24, 28 + b, 12, 14);
                px(0xFFE8D6FA, 18, 33 + b, 30, 39 + b);
                face(mood, 24, 24 + b, 5, 31 + b);
                accessories(worn, 24, 15 + b, 24 + b, 5);
                break;
            }
            default: {
                if (form == 1) { // bear
                    int col = 0xFFF5B77A;
                    ball(col, 13, 15 + b, 5); ball(col, 35, 15 + b, 5); disc(0xFFFFE0B8, 13, 15 + b, 2.5f); disc(0xFFFFE0B8, 35, 15 + b, 2.5f);
                    oval(col, 9, 32 + b, 4, 6); oval(col, 39, 32 + b, 4, 6);
                    oval(col, 17, 42, 5, 3); oval(col, 31, 42, 5, 3);
                    oval(col, 24, 28 + b, 14, 15);
                    oval(0xFFFFE0B8, 24, 33 + b, 8, 7);
                    face(mood, 24, 23 + b, 6, 30 + b);
                    px(0xFF3A3358, 22, 28 + b, 26, 30 + b);
                    accessories(worn, 24, 14 + b, 23 + b, 6);
                } else if (form == 2) { // imp
                    int col = 0xFF8E7BE0;
                    tri(0xFF3A3358, 12, 15, 10, 3, 19, 11); tri(0xFFFFE082, 12.5f, 14, 11.5f, 5, 18, 11);
                    tri(0xFF3A3358, 36, 15, 38, 3, 29, 11); tri(0xFFFFE082, 35.5f, 14, 36.5f, 5, 30, 11);
                    tri(0xFF3A3358, 38, 40, 46, 30, 42, 42); tri(col, 39, 40, 45, 32, 42, 41);
                    oval(col, 17, 42, 5, 3); oval(col, 31, 42, 5, 3);
                    oval(col, 24, 27 + b, 14, 15);
                    face(mood, 24, 23 + b, 6, 30 + b);
                    px(0xFFFFFFFF, 21, 31 + b, 22, 33 + b); px(0xFFFFFFFF, 26, 31 + b, 27, 33 + b);
                    accessories(worn, 24, 13 + b, 23 + b, 6);
                } else { // starlet
                    int col = 0xFFFF9EC8;
                    tri(0xFF3A3358, 10, 18, 11, 2, 21, 12); tri(col, 11.5f, 17, 12, 5, 20, 12);
                    tri(0xFF3A3358, 38, 18, 37, 2, 27, 12); tri(col, 36.5f, 17, 36, 5, 28, 12);
                    oval(col, 8, 33 + b, 3, 5); oval(col, 40, 33 + b, 3, 5);
                    oval(col, 17, 42, 5, 3); oval(col, 31, 42, 5, 3);
                    oval(col, 24, 27 + b, 14, 15);
                    oval(0xFFFFD6E8, 24, 33 + b, 8, 6);
                    tri(0xFFFFE082, 24, 12 + b, 22, 17 + b, 26, 17 + b); tri(0xFFFFE082, 24, 19 + b, 22, 15 + b, 26, 15 + b);
                    face(mood, 24, 25 + b, 6, 32 + b);
                    accessories(worn, 24, 15 + b, 25 + b, 6);
                }
            }
        }
    }
}
