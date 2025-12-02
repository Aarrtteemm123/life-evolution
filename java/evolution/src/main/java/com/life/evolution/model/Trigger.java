package com.life.evolution.model;

import java.util.HashMap;
import java.util.Map;

public class Trigger {

    public static final String LESS = "LESS";
    public static final String GREATER = "GREATER";

    private double threshold;
    private String mode;

    public Trigger(double threshold, String mode) {
        this.threshold = threshold;
        this.mode = mode;
    }

    public Trigger(double threshold) {
        this(threshold, LESS);
    }

    // ----------------------------------------------------
    // CHECK CONDITION
    // ----------------------------------------------------
    public boolean check(double value) {
        return switch (mode) {
            case LESS -> value < threshold;
            case GREATER -> value > threshold;
            default -> false;
        };
    }

    // ----------------------------------------------------
    // JSON SERIALIZATION
    // ----------------------------------------------------
    public Map<String, Object> toMap() {
        Map<String, Object> m = new HashMap<>();
        m.put("threshold", threshold);
        m.put("mode", mode);
        return m;
    }

    @SuppressWarnings("unchecked")
    public static Trigger fromMap(Map<String, Object> m) {
        return new Trigger(
                ((Number) m.get("threshold")).doubleValue(),
                (String) m.get("mode")
        );
    }

    @Override
    public String toString() {
        return "Trigger(threshold=" + threshold + ", mode=" + mode + ")";
    }

    // ----------------------------------------------------
    // GETTERS / SETTERS
    // ----------------------------------------------------
    public double getThreshold() { return threshold; }
    public void setThreshold(double threshold) { this.threshold = threshold; }

    public String getMode() { return mode; }
    public void setMode(String mode) { this.mode = mode; }
}
