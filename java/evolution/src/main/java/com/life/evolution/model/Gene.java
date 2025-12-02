package com.life.evolution.model;

import com.life.evolution.config.Config;

import java.util.*;

public class Gene {

    private String receptor;           // substance or parameter name
    private Trigger trigger;           // activation condition
    private Action action;             // action to execute
    private boolean active;            // gene enabled/disabled
    private double mutationRate;       // probability of mutation

    public Gene(String receptor, Trigger trigger, Action action,
                boolean active, double mutationRate) {

        this.receptor = receptor;
        this.trigger = trigger;
        this.action = action;
        this.active = active;
        this.mutationRate = mutationRate;
    }

    public Gene(String receptor, Trigger trigger, Action action) {
        this(receptor, trigger, action, true, 0.07);
    }

    // --------------------------------------------------------
    // EXECUTION
    // --------------------------------------------------------
    public void tryActivate(Cell cell, Environment env) {
        if (!active) return;

        Double value = null;

        // Try reading substance from environment grid
        if (!Objects.equals(receptor, "energy") &&
                !Objects.equals(receptor, "health")) {

            int[] pos = cell.getIntPosition();
            Substance s = env.getGrid().getSubstance(pos[0], pos[1], receptor);

            if (s != null) value = s.getConcentration();
        }

        // fallback to cell field
        if (value == null) {
            value = switch (receptor) {
                case "energy" -> cell.getEnergy();
                case "health" -> cell.getHealth();
                default -> null;
            };
        }

        if (value == null) return;

        if (trigger.check(value)) {
            action.execute(cell, env);
        }
    }

    // --------------------------------------------------------
    // MUTATION
    // --------------------------------------------------------
    public Gene mutate() {

        if (isTriggeredMutation()) {
            active = !active;
        }

        if (isTriggeredMutation()) {
            receptor = Config.randomSubstanceName();
        }

        if (isTriggeredMutation()) {
            if (receptor.equals("energy") || receptor.equals("health")) {
                trigger.setThreshold(randomDouble(1, 100));
            } else {
                trigger.setThreshold(randomDouble(0.1, 10));
            }
        }

        if (isTriggeredMutation()) {
            action.setPower(randomDouble(0.1, 10));
        }

        if (isTriggeredMutation()) {
            return Gene.createRandomGene();
        }

        if (isTriggeredMutation()) {
            action.setMoveMode(randomChoice(List.of(
                    Action.MOVE_RANDOM,
                    Action.MOVE_TOWARD,
                    Action.MOVE_AWAY,
                    Action.MOVE_AROUND,
                    null
            )));
        }

        if (isTriggeredMutation()) {
            mutationRate *= randomChoice(List.of(1.15, 0.85));
            mutationRate = Math.min(mutationRate, 1.0);
        }

        return null;
    }

    private boolean isTriggeredMutation() {
        return Math.random() < mutationRate;
    }

    // --------------------------------------------------------
    // RANDOM GENE FACTORY
    // --------------------------------------------------------
    public static Gene createRandomGene() {

        String receptor;

        if (Math.random() < 0.85) {
            receptor = Config.randomSubstanceName();
        } else {
            receptor = randomChoice(List.of("energy", "health"));
        }

        double threshold;
        if (receptor.equals("energy") || receptor.equals("health")) {
            threshold = randomDouble(1, 100);
        } else {
            threshold = randomDouble(0.1, 10);
        }

        String mode = randomChoice(List.of(Trigger.LESS, Trigger.GREATER));
        Trigger trig = new Trigger(threshold, mode);

        String actionType = randomChoice(List.of(
                Action.DIVIDE,
                Action.EMIT,
                Action.ABSORB,
                Action.MOVE,
                Action.HEALS
        ));

        String moveMode = null;
        String substanceName;

        if (actionType.equals(Action.MOVE)) {
            moveMode = randomChoice(List.of(
                    Action.MOVE_RANDOM,
                    Action.MOVE_TOWARD,
                    Action.MOVE_AWAY,
                    Action.MOVE_AROUND
            ));
            substanceName = Config.randomSubstanceName();
        } else {
            substanceName = Config.randomSubstanceName();
        }

        Action action = new Action(
                actionType,
                randomDouble(0.1, 10),
                substanceName,
                moveMode
        );

        return new Gene(receptor, trig, action);
    }

    // --------------------------------------------------------
    // JSON SERIALIZATION
    // --------------------------------------------------------
    public Map<String, Object> toMap() {
        Map<String, Object> m = new HashMap<>();
        m.put("receptor", receptor);
        m.put("trigger", trigger.toMap());
        m.put("action", action.toMap());
        m.put("active", active);
        m.put("mutation_rate", mutationRate);
        return m;
    }

    @SuppressWarnings("unchecked")
    public static Gene fromMap(Map<String, Object> m) {
        return new Gene(
                (String) m.get("receptor"),
                Trigger.fromMap((Map<String, Object>) m.get("trigger")),
                Action.fromMap((Map<String, Object>) m.get("action")),
                (boolean) m.getOrDefault("active", true),
                ((Number) m.getOrDefault("mutation_rate", 0.07)).doubleValue()
        );
    }

    // --------------------------------------------------------
    // SIGNATURE (used for color)
    // --------------------------------------------------------
    public String toTuple() {
        return String.join("|",
                receptor,
                trigger.getMode(),
                String.format("%.3f", trigger.getThreshold()),
                action.getType(),
                String.format("%.3f", action.getPower()),
                action.getSubstanceName() != null ? action.getSubstanceName() : "",
                action.getMoveMode() != null ? action.getMoveMode() : "",
                Boolean.toString(active)
        );
    }

    // --------------------------------------------------------
    // UTIL
    // --------------------------------------------------------
    private static double randomDouble(double a, double b) {
        return Math.random() * (b - a) + a;
    }

    private static <T> T randomChoice(List<T> items) {
        return items.get((int) (Math.random() * items.size()));
    }

    // --------------------------------------------------------
    // GETTERS
    // --------------------------------------------------------
    public String getReceptor() { return receptor; }
    public Trigger getTrigger() { return trigger; }
    public Action getAction() { return action; }
    public boolean isActive() { return active; }
    public double getMutationRate() { return mutationRate; }
}
