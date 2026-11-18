package com.nemesis.coldstart;

/** Only short, validated requests cross the NEMESIS root IPC channel. */
final class SeatCommands {
    static final String HELPER = "/system/bin/sh /data/nemesis/apps/coldstart.heat/scripts/seat-action.sh";
    private SeatCommands() {}
    static int level(int value) {
        if (value < 0 || value > 3) throw new IllegalArgumentException("Seat level must be 0..3");
        return value;
    }
    static String shortRequest(String request) {
        // Actual receiver rejects >=768 bytes. Keep generous headroom.
        try {
            if (request.getBytes("UTF-8").length > 512) throw new IllegalArgumentException("NEMESIS request too long");
        } catch (java.io.UnsupportedEncodingException e) { throw new IllegalStateException(e); }
        return request;
    }
    static String heating(boolean wheel, int driver, int passenger) {
        level(driver); level(passenger);
        if (!wheel && driver == 0 && passenger == 0) return "";
        return shortRequest(HELPER + " heat " + (wheel ? 1 : 0) + " " + driver + " " + passenger);
    }
    static String ventilation(int driver, int passenger) {
        level(driver); level(passenger);
        if (driver == 0 && passenger == 0) return "";
        return shortRequest(HELPER + " vent " + driver + " " + passenger);
    }
    static String singleHeat(boolean driver, int value) {
        level(value);
        return shortRequest(HELPER + (driver ? " driver_heat " : " passenger_heat ") + value);
    }
    static String singleVent(boolean driver, int value) {
        level(value);
        return shortRequest(HELPER + (driver ? " driver " : " passenger ") + value);
    }
    static String off() { return shortRequest(HELPER + " off"); }
    static String read() { return shortRequest(HELPER + " read"); }
    static String save(boolean enabled, int threshold, boolean wheel, int driver, int passenger,
            boolean celsius, boolean cooling, int above, int ventDriver, int ventPassenger, boolean diag) {
        level(driver); level(passenger); level(ventDriver); level(ventPassenger);
        if (threshold < 0 || threshold > 80 || above < 0 || above > 120 || (cooling && above <= threshold))
            throw new IllegalArgumentException("Invalid temperature thresholds");
        return shortRequest(HELPER + " save " + (enabled ? 1 : 0) + " " + threshold + " " + (wheel ? 1 : 0)
                + " " + driver + " " + passenger + " " + (celsius ? 1 : 0) + " " + (cooling ? 1 : 0)
                + " " + above + " " + ventDriver + " " + ventPassenger + " " + (diag ? 1 : 0));
    }
}
