package com.nemesis.coldstart;

import android.app.Activity;
import android.graphics.Color;
import android.os.Bundle;
import android.view.Gravity;
import android.view.View;
import android.widget.Button;
import android.widget.LinearLayout;
import android.widget.FrameLayout;
import android.widget.ImageView;
import android.view.Window;
import android.widget.ScrollView;
import android.widget.SeekBar;
import android.widget.TextView;
import android.widget.Toast;
import java.io.BufferedReader;
import java.io.InputStreamReader;
import java.util.ArrayList;
import java.util.concurrent.atomic.AtomicBoolean;

/**
 * Cold-start Heat settings. Writes one-value config files (read by the
 * coldstart.heat NEMESIS service) through the privileged `nemesis root`
 * channel, so this ordinary-uid app can persist to /data/nemesis/state.
 */
public class MainActivity extends Activity {

    static final String STATE = "/data/nemesis/state/coldstart.heat";
    static final String NEM = "/system/xbin/nemesis";
    static final String[] SEAT = { "Off", "Low", "Med", "High" };

    String loadError = "";
    boolean enabled = true;
    int thresholdF = 50;      // trigger when outside temp is below this
    boolean wheel = true;
    int seatDrv = 0;          // 0..3
    int seatPass = 0;         // 0..3
    boolean uiTempIsC = false; // dashboard shows Celsius (affects fallback temp source)
    boolean coolEnabled = false;
    int coolAboveF = 75;
    int ventDrv = 0;
    int ventPass = 0;
    boolean diag = false;      // optional persistent diagnostic logging (default off)

    TextView thrLabel, coolLabel, statusLabel;
    Button enBtn, wheelBtn, drvBtn, passBtn, unitBtn, diagBtn, ventDrvBtn, ventPassBtn, coolBtn;
    Button heatTestBtn, ventTestBtn, applyDrvVent, applyPassVent, applyDrvHeat, applyPassHeat;
    final ArrayList<Button> commandButtons = new ArrayList<Button>();
    static final AtomicBoolean commandBusy = new AtomicBoolean(false);

    @Override
    protected void onCreate(Bundle b) {
        super.onCreate(b);
        requestWindowFeature(Window.FEATURE_NO_TITLE);
        getWindow().setBackgroundDrawable(new android.graphics.drawable.ColorDrawable(Color.rgb(9, 11, 15)));
        TextView loading = new TextView(this);
        loading.setText("Loading Auto Seat settings...");
        loading.setTextColor(Color.WHITE);
        loading.setPadding(dp(20), dp(20), dp(20), dp(20));
        setContentView(loading);
        new Thread(new Runnable() {
            public void run() {
                loadConfig();
                runOnUiThread(new Runnable() {
                    public void run() { buildScreen(); }
                });
            }
        }).start();
    }

    static final int HEAT = Color.rgb(198, 40, 40);
    static final int BLUE = Color.rgb(6, 73, 219);
    static final int GRAPHITE = Color.rgb(41, 44, 52);
    LinearLayout heatPage, ventPage, settingsPage;
    ScrollView bodyScroll;

    void buildScreen() {
        commandButtons.clear();
        LinearLayout frame = page();
        frame.setPadding(dp(18), dp(16), dp(18), dp(12));
        android.graphics.drawable.GradientDrawable card = new android.graphics.drawable.GradientDrawable(
                android.graphics.drawable.GradientDrawable.Orientation.TL_BR,
                new int[] {Color.rgb(45, 48, 56), Color.rgb(31, 34, 40)});
        card.setCornerRadius(dp(22));
        card.setStroke(dp(1), Color.rgb(88, 93, 104));
        frame.setBackground(card);

        LinearLayout heading = new LinearLayout(this);
        heading.setGravity(Gravity.CENTER_VERTICAL);
        ImageView icon = new ImageView(this);
        icon.setImageResource(getResources().getIdentifier("auto_seat", "drawable", getPackageName()));
        icon.setContentDescription("Auto Seat");
        LinearLayout.LayoutParams ip = new LinearLayout.LayoutParams(dp(54), dp(54));
        ip.setMargins(0, 0, dp(14), 0);
        heading.addView(icon, ip);
        LinearLayout brand = page();
        brand.setPadding(0, 0, 0, 0);
        brand.addView(title("Auto Seat"));
        TextView subtitle = hint("Automatic comfort");
        subtitle.setPadding(0, 0, 0, 0);
        brand.addView(subtitle);
        heading.addView(brand, new LinearLayout.LayoutParams(0, -2, 1));
        Button close = control("Close", new Runnable() { public void run() { finish(); }});
        heading.addView(close, new LinearLayout.LayoutParams(dp(76), dp(48)));
        frame.addView(heading, new LinearLayout.LayoutParams(-1, -2));
        frame.addView(gap());

        heatPage = page(); ventPage = page(); settingsPage = page();
        final LinearLayout[] pages = {heatPage, ventPage, settingsPage};
        for (LinearLayout p : pages) p.setPadding(0, dp(12), 0, dp(12));
        LinearLayout navigation = new LinearLayout(this);
        final Button[] tabs = new Button[3];
        String[] names = {"Heating", "Ventilation", "Settings"};
        for (int i = 0; i < tabs.length; i++) {
            final int selected = i;
            tabs[i] = control(names[i], new Runnable() {
                public void run() {
                    for (int j = 0; j < pages.length; j++) {
                        pages[j].setVisibility(j == selected ? View.VISIBLE : View.GONE);
                        tabs[j].setSelected(j == selected);
                        styleButton(tabs[j], j == selected ? BLUE : GRAPHITE);
                        tabs[j].setTextSize(15);
                    }
                    bodyScroll.scrollTo(0, 0);
                }
            });
            styleButton(tabs[i], i == 0 ? BLUE : GRAPHITE);
            tabs[i].setTextSize(15);
            tabs[i].setSelected(i == 0);
            LinearLayout.LayoutParams tp = new LinearLayout.LayoutParams(0, dp(48), 1);
            tp.setMargins(i == 0 ? 0 : dp(4), 0, i == 2 ? 0 : dp(4), 0);
            navigation.addView(tabs[i], tp);
        }
        frame.addView(navigation, new LinearLayout.LayoutParams(-1, dp(48)));

        thrLabel = section("");
        thrLabel.setTextColor(Color.rgb(243, 241, 233));
        heatPage.addView(thrLabel);
        SeekBar cold = new SeekBar(this);
        cold.setMax(80); cold.setProgress(thresholdF);
        cold.setContentDescription("Heating threshold in Fahrenheit");
        cold.setOnSeekBarChangeListener(new SeekBar.OnSeekBarChangeListener() {
            public void onProgressChanged(SeekBar bar, int value, boolean user) { thresholdF = value; updateThr(); }
            public void onStartTrackingTouch(SeekBar bar) {}
            public void onStopTrackingTouch(SeekBar bar) {}
        });
        tintSlider(cold, HEAT);
        heatPage.addView(cold, new LinearLayout.LayoutParams(-1, dp(42)));
        drvBtn = control("", new Runnable() { public void run() { seatDrv = (seatDrv + 1) % 4; refresh(); }});
        passBtn = control("", new Runnable() { public void run() { seatPass = (seatPass + 1) % 4; refresh(); }});
        applyDrvHeat = command("", new Runnable() { public void run() { applyHeat(true); }});
        applyPassHeat = command("", new Runnable() { public void run() { applyHeat(false); }});
        heatPage.addView(seatPair(drvBtn, applyDrvHeat, passBtn, applyPassHeat));
        wheelBtn = control("", new Runnable() { public void run() { wheel = !wheel; refresh(); }});
        heatPage.addView(settingRow("Steering-wheel heating", "Included in the heating test", wheelBtn));
        heatTestBtn = command("Test heating now", new Runnable() { public void run() { testHeating(); }});
        styleButton(heatTestBtn, HEAT);
        heatPage.addView(heatTestBtn, fullButton());
        heatPage.addView(hint("Select a level, then Apply to change one seat. The heating test applies all selected heating options. Off selections are skipped during the test."));

        coolLabel = section("");
        coolLabel.setTextColor(Color.rgb(243, 241, 233));
        ventPage.addView(coolLabel);
        SeekBar warm = new SeekBar(this);
        warm.setMax(120); warm.setProgress(coolAboveF);
        warm.setContentDescription("Ventilation threshold in Fahrenheit");
        warm.setOnSeekBarChangeListener(new SeekBar.OnSeekBarChangeListener() {
            public void onProgressChanged(SeekBar bar, int value, boolean user) { coolAboveF = value; updateThr(); }
            public void onStartTrackingTouch(SeekBar bar) {}
            public void onStopTrackingTouch(SeekBar bar) {}
        });
        tintSlider(warm, BLUE);
        ventPage.addView(warm, new LinearLayout.LayoutParams(-1, dp(42)));
        ventDrvBtn = control("", new Runnable() { public void run() { ventDrv = (ventDrv + 1) % 4; refresh(); }});
        ventPassBtn = control("", new Runnable() { public void run() { ventPass = (ventPass + 1) % 4; refresh(); }});
        applyDrvVent = command("", new Runnable() { public void run() { applyVent(true); }});
        applyPassVent = command("", new Runnable() { public void run() { applyVent(false); }});
        ventPage.addView(seatPair(ventDrvBtn, applyDrvVent, ventPassBtn, applyPassVent));
        coolBtn = control("", new Runnable() { public void run() { coolEnabled = !coolEnabled; refresh(); }});
        ventPage.addView(settingRow("Automatic ventilation", "Uses the warm-start threshold", coolBtn));
        ventTestBtn = command("Test ventilation now", new Runnable() { public void run() { testVentilation(); }});
        styleButton(ventTestBtn, BLUE);
        ventPage.addView(ventTestBtn, fullButton());
        ventPage.addView(hint("Select a level, then Apply to change one seat. The ventilation test applies both selected seat levels. Off selections are skipped during the test."));

        enBtn = control("", new Runnable() { public void run() { enabled = !enabled; refresh(); }});
        settingsPage.addView(settingRow("Startup automation", "Apply saved settings at head-unit startup", enBtn));
        unitBtn = control("", new Runnable() { public void run() { uiTempIsC = !uiTempIsC; refresh(); }});
        settingsPage.addView(settingRow("Dashboard temperature unit", "Fallback when the log omits its unit", unitBtn));
        diagBtn = control("", new Runnable() { public void run() { diag = !diag; refresh(); }});
        settingsPage.addView(settingRow("Diagnostic logging", "Record startup and command details", diagBtn));
        settingsPage.addView(control("Copy diagnostic log to USB", new Runnable() { public void run() { copyLogToUsb(); }}), fullButton());
        Button save = command("Save startup settings", new Runnable() { public void run() { saveConfig(); }});
        styleButton(save, BLUE);
        settingsPage.addView(save, fullButton());
        settingsPage.addView(hint("Save stores the heating, ventilation, and startup selections. Saving does not apply them immediately."));

        bodyScroll = new ScrollView(this);
        bodyScroll.setFillViewport(false);
        LinearLayout content = page(); content.setPadding(0, 0, 0, 0);
        for (int i = 0; i < pages.length; i++) {
            content.addView(pages[i], new LinearLayout.LayoutParams(-1, -2));
            pages[i].setVisibility(i == 0 ? View.VISIBLE : View.GONE);
        }
        bodyScroll.addView(content, new ScrollView.LayoutParams(-1, -2));
        frame.addView(bodyScroll, new LinearLayout.LayoutParams(-1, 0, 1));
        Button allOff = command("All Off · Both seats + steering wheel", new Runnable() { public void run() { allOff(); }});
        frame.addView(allOff, fullButton());
        statusLabel = hint("");
        statusLabel.setPadding(0, dp(8), 0, 0);
        statusLabel.setMaxLines(2);
        statusLabel.setEllipsize(android.text.TextUtils.TruncateAt.END);
        frame.addView(statusLabel, new LinearLayout.LayoutParams(-1, -2));

        FrameLayout backdrop = new FrameLayout(this);
        backdrop.setBackgroundColor(Color.rgb(9, 11, 15));
        backdrop.setPadding(dp(16), dp(12), dp(16), dp(12));
        int available = getResources().getDisplayMetrics().widthPixels - dp(32);
        backdrop.addView(frame, new FrameLayout.LayoutParams(Math.min(dp(600), available), -1, Gravity.CENTER));
        setContentView(backdrop);
        refresh();
        if (loadError.length() > 0) statusLabel.setText(loadError);
    }

    Button control(String text, final Runnable action) {
        Button b = new Button(this); b.setText(text); styleButton(b, GRAPHITE);
        b.setOnClickListener(new View.OnClickListener() { public void onClick(View v) { action.run(); }});
        return b;
    }
    Button command(String text, Runnable action) {
        Button b = control(text, action); commandButtons.add(b); return b;
    }
    LinearLayout.LayoutParams fullButton() {
        LinearLayout.LayoutParams p = new LinearLayout.LayoutParams(-1, -2);
        p.setMargins(0, dp(8), 0, dp(8)); return p;
    }
    LinearLayout seatPair(Button driver, Button applyDriver, Button passenger, Button applyPassenger) {
        LinearLayout pair = new LinearLayout(this);
        Button[] levels = {driver, passenger}, apply = {applyDriver, applyPassenger};
        String[] labels = {"Driver seat", "Passenger seat"};
        for (int i = 0; i < 2; i++) {
            LinearLayout group = page(); group.setPadding(0, dp(10), 0, dp(10));
            TextView label = section(labels[i]); label.setTextColor(Color.rgb(243, 241, 233));
            group.addView(label);
            group.addView(levels[i], new LinearLayout.LayoutParams(-1, dp(70)));
            LinearLayout.LayoutParams ap = new LinearLayout.LayoutParams(-1, dp(54));
            ap.setMargins(0, dp(8), 0, 0);
            apply[i].setTextSize(14); group.addView(apply[i], ap);
            LinearLayout.LayoutParams gp = new LinearLayout.LayoutParams(0, -2, 1);
            gp.setMargins(i == 0 ? 0 : dp(8), 0, i == 0 ? dp(8) : 0, 0);
            pair.addView(group, gp);
        }
        return pair;
    }
    LinearLayout settingRow(String name, String description, Button option) {
        LinearLayout container = page(); container.setPadding(0, 0, 0, 0);
        View divider = new View(this); divider.setBackgroundColor(Color.rgb(76, 81, 92));
        container.addView(divider, new LinearLayout.LayoutParams(-1, dp(1)));
        LinearLayout row = new LinearLayout(this); row.setGravity(Gravity.CENTER_VERTICAL);
        row.setPadding(0, dp(12), 0, dp(12));
        LinearLayout labels = page(); labels.setPadding(0, 0, dp(12), 0);
        TextView label = section(name); label.setTextColor(Color.rgb(243, 241, 233));
        label.setPadding(0, 0, 0, dp(4)); labels.addView(label);
        TextView detail = hint(description); detail.setPadding(0, 0, 0, 0); labels.addView(detail);
        row.addView(labels, new LinearLayout.LayoutParams(0, -2, 1));
        row.addView(option, new LinearLayout.LayoutParams(dp(76), dp(48)));
        container.addView(row, new LinearLayout.LayoutParams(-1, -2));
        return container;
    }
    void updateThr() {
        if (thrLabel != null) thrLabel.setText("Heat below: " + thresholdF + " °F · " + Math.round((thresholdF - 32) * 5f / 9f) + " °C");
        if (coolLabel != null) coolLabel.setText("Ventilate above: " + coolAboveF + " °F · " + Math.round((coolAboveF - 32) * 5f / 9f) + " °C");
    }
    void levelButton(Button button, String label, int value, int color) {
        button.setText(SEAT[value] + "\nTap to change");
        button.setContentDescription(label + ": " + SEAT[value]);
        styleButton(button, value > 0 ? color : GRAPHITE);
        button.setTextSize(18);
    }
    void toggleButton(Button button, String label, boolean on, int color) {
        button.setText(on ? "On" : "Off");
        button.setContentDescription(label + ": " + (on ? "On" : "Off"));
        styleButton(button, on ? color : GRAPHITE);
    }
    void refresh() {
        levelButton(drvBtn, "Driver heating level", seatDrv, HEAT);
        levelButton(passBtn, "Passenger heating level", seatPass, HEAT);
        levelButton(ventDrvBtn, "Driver ventilation level", ventDrv, BLUE);
        levelButton(ventPassBtn, "Passenger ventilation level", ventPass, BLUE);
        toggleButton(wheelBtn, "Steering-wheel heating", wheel, HEAT);
        toggleButton(coolBtn, "Automatic ventilation", coolEnabled, BLUE);
        toggleButton(enBtn, "Startup automation", enabled, BLUE);
        toggleButton(diagBtn, "Diagnostic logging", diag, BLUE);
        unitBtn.setText(uiTempIsC ? "°C" : "°F");
        unitBtn.setContentDescription("Dashboard temperature unit: " + (uiTempIsC ? "°C" : "°F"));
        applyDrvHeat.setText(seatDrv == 0 ? "Turn driver seat Off" : "Apply driver heating");
        applyPassHeat.setText(seatPass == 0 ? "Turn passenger seat Off" : "Apply passenger heating");
        applyDrvVent.setText(ventDrv == 0 ? "Turn driver seat Off" : "Apply driver ventilation");
        applyPassVent.setText(ventPass == 0 ? "Turn passenger seat Off" : "Apply passenger ventilation");
        updateThr();
    }

    // ---- config I/O via `nemesis root -c` -------------------------------
    String runRoot(String cmd) {
        StringBuilder out = new StringBuilder();
        try {
            SeatCommands.shortRequest(cmd);
            Process p = new ProcessBuilder(NEM, "root", "-c", cmd).redirectErrorStream(true).start();
            BufferedReader r = new BufferedReader(new InputStreamReader(p.getInputStream()));
            String line;
            while ((line = r.readLine()) != null) out.append(line).append("\n");
            if (p.waitFor() != 0) return "ERR " + out.toString();
        } catch (Exception e) {
            return "ERR " + e.getMessage();
        }
        return out.toString();
    }

    int storedInt(java.util.Map<String, String> values, String name, int fallback) {
        try { return Integer.parseInt(values.get(name)); }
        catch (Exception e) { return fallback; }
    }

    void loadConfig() {
        String result = runRootBounded(SeatCommands.read());
        if (result.startsWith("ERR") || !result.contains("CONFIG_READ")) {
            loadError = "Could not load saved settings: " + result + ". Reopen the app before saving.";
            return;
        }
        java.util.Map<String, String> values = new java.util.HashMap<String, String>();
        for (String line : result.split("\n")) {
            int equal = line.indexOf('=');
            if (equal > 0) values.put(line.substring(0, equal), line.substring(equal + 1).trim());
        }
        coolEnabled = storedInt(values, "cool_enabled", 0) == 1;
        coolAboveF = clamp(storedInt(values, "cool_above_f", 75), 0, 120);
        ventDrv = clamp(storedInt(values, "vent_drv", 0), 0, 3);
        ventPass = clamp(storedInt(values, "vent_pass", 0), 0, 3);
        enabled = storedInt(values, "enabled", 1) == 1;
        thresholdF = clamp(storedInt(values, "threshold_f", 50), 0, 80);
        wheel = storedInt(values, "wheel", 1) == 1;
        seatDrv = clamp(storedInt(values, "seat_drv", 0), 0, 3);
        seatPass = clamp(storedInt(values, "seat_pass", 0), 0, 3);
        uiTempIsC = storedInt(values, "ui_temp_is_c", 0) == 1;
        diag = storedInt(values, "diag", 0) == 1;
    }

    void saveConfig() {
        if (loadError.length() > 0) {
            toast("Settings were not loaded. Reopen the app before saving.");
            return;
        }
        if (coolEnabled && coolAboveF <= thresholdF) {
            toast("Ventilation threshold must be higher than heating threshold");
            return;
        }
        executeSeatAction("Settings save", SeatCommands.save(enabled, thresholdF, wheel, seatDrv, seatPass,
                uiTempIsC, coolEnabled, coolAboveF, ventDrv, ventPass, diag));
    }

    // UI level 1/2/3 (Low/Med/High) -> seat enum 6/7/8 ; else 2 (off)

    void testHeating() {
        executeSeatAction("Heating test", SeatCommands.heating(wheel, seatDrv, seatPass));
    }

    void testVentilation() {
        executeSeatAction("Ventilation test", SeatCommands.ventilation(ventDrv, ventPass));
    }

    void applyHeat(boolean driver) {
        executeSeatAction(driver ? "Driver heating command" : "Passenger heating command",
                SeatCommands.singleHeat(driver, driver ? seatDrv : seatPass));
    }

    void applyVent(boolean driver) {
        executeSeatAction(driver ? "Driver seat command" : "Passenger seat command",
                SeatCommands.singleVent(driver, driver ? ventDrv : ventPass));
    }

    void allOff() {
        executeSeatAction("Turn off command", SeatCommands.off());
    }

    void executeSeatAction(final String name, String commands) {
        if (commands.length() == 0) {
            toast("Select at least one level above Off");
            return;
        }
        if (!commandBusy.compareAndSet(false, true)) {
            toast("A seat command is already running. Please wait.");
            return;
        }
        final String script = SeatCommands.shortRequest(commands);
        for (Button button : commandButtons) button.setEnabled(false);
        statusLabel.setText(name + " in progress...");
        new Thread(new Runnable() {
            public void run() {
                String response;
                try { response = runRootBounded(script); }
                catch (Exception e) { response = "ERR " + e.getMessage(); }
                final String result = response;
                commandBusy.set(false);
                runOnUiThread(new Runnable() {
                    public void run() {
                        for (Button button : commandButtons) button.setEnabled(true);
                        if (result.startsWith("ERR") || !result.contains("COMMANDS_ACCEPTED")) {
                            statusLabel.setText(name + " was not confirmed. " + result
                                    + " Some commands may already have applied; check the factory controls.");
                            toast("Command not confirmed");
                        } else {
                            if (name.equals("Settings save")) {
                                statusLabel.setText("Startup settings saved.");
                                toast("Settings saved");
                            } else {
                                statusLabel.setText(name + " sent. Check the factory indicators and seat response.");
                                toast("Command sent");
                            }
                        }
                    }
                });
            }
        }).start();
    }

    // KitKat-compatible timeout: no Process.waitFor(timeout) API required.
    String runRootBounded(String cmd) {
        Process started = null;
        try {
            SeatCommands.shortRequest(cmd);
            started = new ProcessBuilder(NEM, "root", "-c", cmd).redirectErrorStream(true).start();
            final Process process = started;
            final StringBuilder output = new StringBuilder();
            Thread drain = new Thread(new Runnable() {
                public void run() {
                    try {
                        BufferedReader reader = new BufferedReader(new InputStreamReader(process.getInputStream()));
                        String line;
                        while ((line = reader.readLine()) != null) {
                            synchronized (output) {
                                if (output.length() < 16384) output.append(line).append("\n");
                            }
                        }
                        reader.close();
                    } catch (Exception ignored) { }
                }
            });
            drain.setDaemon(true);
            drain.start();
            long end = android.os.SystemClock.elapsedRealtime() + 10000;
            int exit;
            for (;;) {
                try { exit = process.exitValue(); break; }
                catch (IllegalThreadStateException running) {
                    if (android.os.SystemClock.elapsedRealtime() >= end) {
                        process.destroy();
                        return "ERR timed out; vehicle state is unknown. Use the factory controls. "
                                + "If commands remain locked, restart the head unit.";
                    }
                    Thread.sleep(50);
                }
            }
            drain.join(500);
            synchronized (output) {
                return exit == 0 ? output.toString() : "ERR " + output.toString();
            }
        } catch (Exception e) {
            if (started != null) started.destroy();
            return "ERR " + e.getMessage();
        }
    }

    // copy diag.log onto a plugged-in USB stick (for users without ADB)
    void copyLogToUsb() {
        String cmd = "L=" + STATE + "/diag.log; [ -f \"$L\" ] || { echo NOLOG; exit 0; }; "
            + "for u in /storage/usb0 /storage/usb1 /mnt/media_rw/usb0 /mnt/usbhost0; do "
            + "[ -d \"$u\" ] && cp \"$L\" \"$u/coldstart-diag.log\" 2>/dev/null && { echo COPIED $u; break; }; done";
        String r = runRoot(cmd).trim();
        if (r.startsWith("COPIED")) {
            toast("Log copied to USB");
            statusLabel.setText("diag.log copied to " + r.substring(6).trim() + " as coldstart-diag.log");
        } else if (r.startsWith("NOLOG")) {
            toast("No log yet");
            statusLabel.setText("No diag.log yet. Turn Diagnostic logging On, Save, then start the car once.");
        } else {
            toast("No USB found");
            statusLabel.setText("No USB stick detected. Insert a FAT32 stick and try again.");
        }
    }

    // ---- small view helpers --------------------------------------------
    int dp(int v) { return (int) (v * getResources().getDisplayMetrics().density); }
    int clamp(int v, int lo, int hi) { return v < lo ? lo : (v > hi ? hi : v); }
    void toast(String s) { Toast.makeText(this, s, Toast.LENGTH_SHORT).show(); }

    TextView title(String s) {
        TextView t = new TextView(this);
        t.setText(s); t.setTextColor(Color.WHITE); t.setTextSize(26);
        t.setPadding(0, 0, 0, dp(8)); return t;
    }
    TextView section(String s) {
        TextView t = new TextView(this);
        t.setText(s); t.setTextColor(Color.rgb(100, 153, 255)); t.setTextSize(16);
        t.setPadding(0, dp(8), 0, dp(4)); return t;
    }
    TextView hint(String s) {
        TextView t = new TextView(this);
        t.setText(s); t.setTextColor(Color.rgb(191, 197, 208)); t.setTextSize(13);
        t.setPadding(0, 0, 0, dp(12)); return t;
    }
    LinearLayout page() {
        LinearLayout panel = new LinearLayout(this);
        panel.setOrientation(LinearLayout.VERTICAL);
        panel.setPadding(dp(16), dp(8), dp(16), dp(8));
        panel.setBackgroundColor(Color.TRANSPARENT);
        return panel;
    }
    void styleButton(Button button, int color) {
        android.graphics.drawable.StateListDrawable states = new android.graphics.drawable.StateListDrawable();
        states.addState(new int[] {-android.R.attr.state_enabled}, buttonFace(Color.rgb(44, 44, 44), Color.rgb(70, 70, 70)));
        int edge = color == HEAT ? Color.rgb(228, 107, 104) : color == BLUE ? Color.rgb(97, 148, 247) : Color.rgb(114, 122, 138);
        int pressed = Color.rgb(Math.min(255, Color.red(color) + 24), Math.min(255, Color.green(color) + 24), Math.min(255, Color.blue(color) + 24));
        states.addState(new int[] {android.R.attr.state_pressed}, buttonFace(pressed, edge));
        states.addState(new int[] {android.R.attr.state_focused}, buttonFace(color, edge));
        states.addState(new int[] {}, buttonFace(color, edge));
        button.setBackground(states);
        button.setTextColor(Color.rgb(243, 241, 233));
        button.setTextSize(16);
        button.setAllCaps(false);
        button.setMinimumHeight(dp(48));
        button.setPadding(dp(12), dp(8), dp(12), dp(8));
    }
    android.graphics.drawable.GradientDrawable buttonFace(int color, int border) {
        int top = Color.rgb(Math.min(255, Color.red(color) + 14), Math.min(255, Color.green(color) + 14), Math.min(255, Color.blue(color) + 14));
        android.graphics.drawable.GradientDrawable face = new android.graphics.drawable.GradientDrawable(
                android.graphics.drawable.GradientDrawable.Orientation.TOP_BOTTOM, new int[] {top, color});
        face.setCornerRadius(dp(12));
        face.setStroke(dp(1), border);
        return face;
    }
    void tintSlider(SeekBar slider, int color) {
        slider.getProgressDrawable().setColorFilter(color, android.graphics.PorterDuff.Mode.SRC_IN);
        if (slider.getThumb() != null) slider.getThumb().setColorFilter(Color.rgb(210, 225, 255), android.graphics.PorterDuff.Mode.SRC_IN);
        slider.setPadding(dp(10), dp(12), dp(10), dp(12));
    }
    // A plain View with WRAP_CONTENT may measure to all remaining height on KitKat.
    // Fixed-height spacers keep tabs and content inside the panel.
    View gap() {
        View spacer = new View(this);
        spacer.setLayoutParams(new LinearLayout.LayoutParams(-1, dp(10)));
        return spacer;
    }
}
