package org.kyf37.tama;

import android.content.SharedPreferences;
import java.util.Calendar;
import java.util.Random;

/** Pet simulation. Time is measured in game minutes; speed scales real time (1x, 10x, 60x). */
final class Pet {
    static final int EGG = 0, BABY = 1, CHILD = 2, TEEN = 3, ADULT = 4;
    static final double[] STAGE_START = { 0, 2, 60, 360, 1440 };
    static final String[] STAGE_NAME = { "Egg", "Baby", "Child", "Teen", "Adult" };
    static final String[] FORM_NAME = { "Starlet", "Bearlet", "Impling" };
    static final int WANT_NONE = -1, WANT_FOOD = 0, WANT_PLAY = 1, WANT_CLEAN = 2, WANT_SLEEP = 3;
    static final String[] ITEM_NAME = { "Bow", "Hat", "Glasses", "Crown" };
    static final int[] ITEM_COST = { 10, 15, 20, 40 };

    final Random rnd = new Random();
    String name = "Kiki";
    double ageMin;
    float fullness = 80, happy = 80, hygiene = 90, energy = 90;
    int poops;
    boolean sick;
    boolean lightsOn = true;
    int coins = 10, bond, mistakes;
    double careSum, careMin;
    int form = -1;
    int owned, worn;
    int want = WANT_NONE;
    double wantLeft, wantCd = 15;
    double poopTimer = 30, sickMin;
    final double[] zeroMin = new double[4];
    int speed = 1;
    boolean sound = true;
    boolean needName;
    long lastMs;
    int eggTaps;

    // transient (not saved)
    String event = "";

    int stage() {
        int s = EGG;
        for (int i = 0; i < STAGE_START.length; i++) if (ageMin >= STAGE_START[i]) s = i;
        return s;
    }

    boolean night() {
        int h = Calendar.getInstance().get(Calendar.HOUR_OF_DAY);
        return h >= 22 || h < 7;
    }

    boolean sleeping() { return !lightsOn && stage() != EGG; }

    /** Needs attention right now (used for the status line and the outer screen). */
    String need() {
        if (stage() == EGG) return "";
        if (sleeping()) return "";
        if (sick) return name + " is sick!";
        if (fullness < 25) return name + " is hungry!";
        if (poops > 0 && hygiene < 60) return "Clean up!";
        if (happy < 25) return name + " is sad.";
        if (energy < 20) return name + " is sleepy.";
        if (night() && lightsOn) return "Lights off, please.";
        return "";
    }

    private static float clamp(float v) { return v < 0 ? 0 : (v > 100 ? 100 : v); }

    /** Advance by dt game minutes (call with dt <= 1). */
    void step(double dt) {
        int before = stage();
        if (before == EGG) {
            ageMin += dt;
            if (stage() != EGG) { needName = true; event = "It hatched!"; }
            return;
        }
        boolean asleep = sleeping();
        boolean night = night();
        fullness -= (asleep ? 0.2 : 0.5) * dt;
        happy -= (asleep ? 0.1 : 0.35) * dt;
        hygiene -= (0.2 + poops * 0.15) * dt;
        if (asleep) energy += 1.2 * dt;
        else energy -= 0.25 * dt;
        if (!asleep && night && lightsOn) happy -= 0.2 * dt;
        if (energy <= 0) happy -= 0.3 * dt;
        if (sick) happy -= 0.3 * dt;
        if (!asleep && fullness > 20) {
            poopTimer -= dt;
            if (poopTimer <= 0) { if (poops < 4) poops++; poopTimer = 25 + rnd.nextInt(30); event = name + " made a mess."; }
        }
        fullness = clamp(fullness); happy = clamp(happy); hygiene = clamp(hygiene); energy = clamp(energy);
        float[] v = { fullness, happy, hygiene, energy };
        for (int i = 0; i < 4; i++) {
            if (v[i] <= 0) { zeroMin[i] += dt; if (zeroMin[i] >= 20) { mistakes++; zeroMin[i] = 0; } }
            else zeroMin[i] = 0;
        }
        if (hygiene < 10 || poops >= 3) sickMin += dt; else sickMin = Math.max(0, sickMin - dt);
        if (!sick && sickMin >= 15) { sick = true; event = name + " got sick!"; }
        careMin += dt;
        careSum += (fullness + happy + hygiene + energy) / 400.0 * dt;
        ageMin += dt;
        // wants
        if (want != WANT_NONE) { wantLeft -= dt; if (wantLeft <= 0) want = WANT_NONE; }
        else if (!asleep) {
            wantCd -= dt;
            if (wantCd <= 0) { pickWant(); wantCd = 20 + rnd.nextInt(25); }
        }
        int after = stage();
        if (after != before) {
            if (after == ADULT) {
                double avg = careMin > 0 ? careSum / careMin : 0.5;
                form = (avg >= 0.65 && mistakes <= 3) ? 0 : (avg >= 0.4 && mistakes <= 8 ? 1 : 2);
                event = name + " grew into a " + FORM_NAME[form] + "!";
            } else event = name + " is now a " + STAGE_NAME[after].toLowerCase() + "!";
            happy = clamp(happy + 15);
        }
    }

    private void pickWant() {
        int[] pool = new int[4];
        int n = 0;
        if (fullness < 75) pool[n++] = WANT_FOOD;
        if (happy < 85) pool[n++] = WANT_PLAY;
        if (hygiene < 85 || poops > 0) pool[n++] = WANT_CLEAN;
        if (energy < 50) pool[n++] = WANT_SLEEP;
        if (n == 0) return;
        want = pool[rnd.nextInt(n)];
        wantLeft = 12;
    }

    /** Fulfilling a want gives bond and coins. */
    boolean grantWant(int kind) {
        if (want != kind) return false;
        want = WANT_NONE;
        bond++;
        coins += 2;
        happy = clamp(happy + 8);
        event = name + " is delighted! +2";
        return true;
    }

    void catchUp(long nowMs) {
        if (lastMs == 0) { lastMs = nowMs; return; }
        double minutes = Math.max(0, (nowMs - lastMs) / 60000.0) * speed;
        minutes = Math.min(minutes, 24 * 60);
        lastMs = nowMs;
        while (minutes > 0) { double d = Math.min(1.0, minutes); step(d); minutes -= d; }
    }

    // ------------------------------------------------------------------ actions
    String feed(int kind) {
        if (stage() == EGG) return "";
        if (sleeping()) return name + " is asleep.";
        if (kind == 0) {
            if (fullness > 92) return name + " is full.";
            fullness = clamp(fullness + 30); happy = clamp(happy + 3); poopTimer = Math.min(poopTimer, 20 + rnd.nextInt(15));
            grantWant(WANT_FOOD);
            return "Yum! A tasty meal.";
        }
        if (kind == 1) {
            fullness = clamp(fullness + 10); happy = clamp(happy + 15);
            grantWant(WANT_FOOD);
            return "Snack time!";
        }
        if (happy > 95) return name + " does not want a treat.";
        happy = clamp(happy + 25); fullness = clamp(fullness + 5); hygiene = clamp(hygiene - 5);
        return "A sweet treat!";
    }

    String clean() {
        if (stage() == EGG) return "";
        if (sleeping()) return name + " is asleep.";
        if (poops == 0 && hygiene > 90) return "Already spotless.";
        poops = 0; hygiene = clamp(hygiene + 45); poopTimer = 30 + rnd.nextInt(20);
        grantWant(WANT_CLEAN);
        return "Squeaky clean!";
    }

    String toggleLights() {
        if (stage() == EGG) return "";
        lightsOn = !lightsOn;
        if (!lightsOn) { grantWant(WANT_SLEEP); return "Goodnight, " + name + "."; }
        return "Good morning!";
    }

    String heal() {
        if (!sick) return name + " is not sick.";
        sick = false; sickMin = 0; happy = clamp(happy + 10); hygiene = clamp(hygiene + 20);
        return "Feeling better!";
    }

    String wear(int item) {
        if ((owned & (1 << item)) == 0) {
            if (coins < ITEM_COST[item]) return "Not enough coins.";
            coins -= ITEM_COST[item]; owned |= 1 << item; worn |= 1 << item;
            return "Bought the " + ITEM_NAME[item].toLowerCase() + "!";
        }
        worn ^= 1 << item;
        return (worn & (1 << item)) != 0 ? "Wearing the " + ITEM_NAME[item].toLowerCase() + "." : "Took it off.";
    }

    void playReward(int win, int coinGain) {
        happy = clamp(happy + (win > 0 ? 25 : 10));
        energy = clamp(energy - 8);
        hygiene = clamp(hygiene - 3);
        fullness = clamp(fullness - 4);
        coins += coinGain;
        grantWant(WANT_PLAY);
    }

    // ------------------------------------------------------------------ persistence
    void save(SharedPreferences sp) {
        sp.edit().putString("name", name).putFloat("age", (float) ageMin).putFloat("full", fullness).putFloat("happy", happy)
            .putFloat("hyg", hygiene).putFloat("en", energy).putInt("poops", poops).putBoolean("sick", sick)
            .putBoolean("lights", lightsOn).putInt("coins", coins).putInt("bond", bond).putInt("mist", mistakes)
            .putFloat("careSum", (float) careSum).putFloat("careMin", (float) careMin).putInt("form", form)
            .putInt("owned", owned).putInt("worn", worn).putInt("want", want).putFloat("wantLeft", (float) wantLeft)
            .putFloat("wantCd", (float) wantCd).putFloat("poopT", (float) poopTimer).putFloat("sickMin", (float) sickMin)
            .putInt("speed", speed).putBoolean("sound", sound).putBoolean("needName", needName).putLong("last", lastMs)
            .putBoolean("exists", true).apply();
    }

    void load(SharedPreferences sp) {
        if (!sp.getBoolean("exists", false)) { lastMs = System.currentTimeMillis(); needName = false; return; }
        name = sp.getString("name", "Kiki"); ageMin = sp.getFloat("age", 0); fullness = sp.getFloat("full", 80);
        happy = sp.getFloat("happy", 80); hygiene = sp.getFloat("hyg", 90); energy = sp.getFloat("en", 90);
        poops = sp.getInt("poops", 0); sick = sp.getBoolean("sick", false); lightsOn = sp.getBoolean("lights", true);
        coins = sp.getInt("coins", 10); bond = sp.getInt("bond", 0); mistakes = sp.getInt("mist", 0);
        careSum = sp.getFloat("careSum", 0); careMin = sp.getFloat("careMin", 0); form = sp.getInt("form", -1);
        owned = sp.getInt("owned", 0); worn = sp.getInt("worn", 0); want = sp.getInt("want", WANT_NONE);
        wantLeft = sp.getFloat("wantLeft", 0); wantCd = sp.getFloat("wantCd", 15); poopTimer = sp.getFloat("poopT", 30);
        sickMin = sp.getFloat("sickMin", 0); speed = sp.getInt("speed", 1); sound = sp.getBoolean("sound", true);
        needName = sp.getBoolean("needName", false); lastMs = sp.getLong("last", System.currentTimeMillis());
    }

    void reset(SharedPreferences sp) {
        boolean snd = sound; int spd = speed;
        sp.edit().clear().apply();
        Pet fresh = new Pet();
        name = fresh.name; ageMin = 0; fullness = 80; happy = 80; hygiene = 90; energy = 90; poops = 0; sick = false;
        lightsOn = true; coins = 10; bond = 0; mistakes = 0; careSum = 0; careMin = 0; form = -1; owned = 0; worn = 0;
        want = WANT_NONE; wantCd = 15; poopTimer = 30; sickMin = 0; needName = false; eggTaps = 0;
        java.util.Arrays.fill(zeroMin, 0);
        sound = snd; speed = spd; lastMs = System.currentTimeMillis();
    }
}
