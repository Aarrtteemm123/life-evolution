package com.life.evolution.model;

import com.life.evolution.config.Config;

import java.util.HashMap;
import java.util.Map;

public class Substance {

    public static final String ORGANIC = "ORGANIC";
    public static final String INORGANIC = "INORGANIC";
    public static final String TOXIN = "TOXIN";

    private String name;
    private String type;
    private double concentration;
    private double energy;
    private double volatility;   // 0.0 stable, 0.9 fast decay

    public Substance(String name, String type, double concentration, double energy, double volatility) {
        this.name = name;
        this.type = type;
        this.concentration = concentration;
        this.energy = energy;
        this.volatility = volatility;
    }

    public Substance(String name, String type, double concentration, double energy) {
        this(name, type, concentration, energy, 0.01);
    }

    // ---------------------------------------------------------
    // UPDATE
    // ---------------------------------------------------------
    public void update() {
        concentration *= (1.0 - volatility);
        if (concentration < 0.01) {
            concentration = 0;
        }
    }

    public boolean isActive() {
        return concentration > 0;
    }

    // ---------------------------------------------------------
    // SUBSTANCE TYPE INFO (LOOKUP FROM CONFIG)
    // ---------------------------------------------------------
    public static Map<String, Object> findSubstance(String name) {
        return Config.SUBSTANCES.get(name);
    }

    // ---------------------------------------------------------
    // CLONE / COPY
    // ---------------------------------------------------------
    public Substance cloneSubstance() {
        return fromMap(toMap());
    }

    // ---------------------------------------------------------
    // JSON MAPPING
    // ---------------------------------------------------------
    public Map<String, Object> toMap() {
        Map<String, Object> m = new HashMap<>();
        m.put("name", name);
        m.put("type", type);
        m.put("concentration", concentration);
        m.put("energy", energy);
        m.put("volatility", volatility);
        return m;
    }

    @SuppressWarnings("unchecked")
    public static Substance fromMap(Map<String, Object> m) {
        return new Substance(
                (String) m.get("name"),
                (String) m.get("type"),
                ((Number) m.get("concentration")).doubleValue(),
                ((Number) m.get("energy")).doubleValue(),
                ((Number) m.getOrDefault("volatility", 0.01)).doubleValue()
        );
    }

    @Override
    public String toString() {
        return "Substance(" +
                "name=" + name +
                ", type=" + type +
                ", conc=" + String.format("%.3f", concentration) +
                ", energy=" + String.format("%.2f", energy) +
                ", volatility=" + String.format("%.3f", volatility) +
                ')';
    }

    // ---------------------------------------------------------
    // GETTERS / SETTERS
    // ---------------------------------------------------------
    public String getName() { return name; }
    public String getType() { return type; }
    public double getConcentration() { return concentration; }
    public void setConcentration(double c) { this.concentration = c; }
    public double getEnergy() { return energy; }
    public double getVolatility() { return volatility; }
}
