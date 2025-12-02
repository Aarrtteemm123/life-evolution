package com.life.evolution.model;

import lombok.AllArgsConstructor;
import lombok.Data;
import lombok.NoArgsConstructor;

import java.util.HashMap;
import java.util.Map;

import static java.lang.Math.hypot;

@Data
@NoArgsConstructor
@AllArgsConstructor
public class Action {

    public static final String DIVIDE = "DIVIDE";
    public static final String EMIT = "EMIT";
    public static final String ABSORB = "ABSORB";
    public static final String MOVE = "MOVE";
    public static final String HEALS = "HEALS";

    public static final String MOVE_RANDOM = "RANDOM";
    public static final String MOVE_TOWARD = "TOWARD";
    public static final String MOVE_AWAY = "AWAY";
    public static final String MOVE_AROUND = "AROUND";

    private String type;
    private double power;
    private String substanceName;
    private String moveMode;

    public Action(String type) {
        this(type, 1.0, null, null);
    }

    // ================================
    // EXECUTE
    // ================================
    public void execute(Cell cell, Environment environment) {
        switch (type) {
            case DIVIDE -> executeDivide(cell, environment);
            case EMIT -> {
                if (substanceName != null) executeEmit(cell, environment);
            }
            case ABSORB -> {
                if (substanceName != null) executeAbsorb(cell, environment);
            }
            case MOVE -> executeMove(cell, environment);
            case HEALS -> executeHeals(cell);
        }
    }

    private void executeDivide(Cell cell, Environment environment) {
        Cell newCell = cell.divide(environment);
        if (newCell != null) environment.addCellToBuffer(newCell);
    }

    private void executeEmit(Cell cell, Environment environment) {
        cell.emit(substanceName, power, environment);
    }

    private void executeAbsorb(Cell cell, Environment environment) {
        int[] pos = cell.getIntPosition();
        Substance s = environment.getGrid().getSubstance(pos[0], pos[1], substanceName);
        cell.absorb(s);
    }

    private void executeHeals(Cell cell) {
        cell.heals(power);
    }

    // ================================
    // MOVEMENT LOGIC
    // ================================
    private void executeMove(Cell cell, Environment environment) {
        if (moveMode == null) return;

        int[] pos = cell.getIntPosition();
        int x = pos[0];
        int y = pos[1];

        double dx = 0;
        double dy = 0;

        if (moveMode.equals(MOVE_RANDOM) || substanceName == null) {
            dx = Math.random() * 2 - 1;
            dy = Math.random() * 2 - 1;

        } else {
            double currentConcentration =
                    environment.getGrid().getConcentration(x, y, substanceName);

            int visionRadius = 3;
            Integer bestIx = null;
            Integer bestIy = null;
            Double bestValue = null;

            for (int ix = -visionRadius; ix <= visionRadius; ix++) {
                for (int iy = -visionRadius; iy <= visionRadius; iy++) {

                    if (ix == 0 && iy == 0) continue;

                    int nx = x + ix;
                    int ny = y + iy;

                    if (nx < 0 || nx >= environment.getGrid().getWidth()) continue;
                    if (ny < 0 || ny >= environment.getGrid().getHeight()) continue;

                    double val = environment.getGrid().getConcentration(nx, ny, substanceName);

                    switch (moveMode) {
                        case MOVE_TOWARD -> {
                            if (val > currentConcentration &&
                                    (bestValue == null || val > bestValue)) {
                                bestValue = val; bestIx = ix; bestIy = iy;
                            }
                        }
                        case MOVE_AWAY -> {
                            if (val < currentConcentration &&
                                    (bestValue == null || val < bestValue)) {
                                bestValue = val; bestIx = ix; bestIy = iy;
                            }
                        }
                        case MOVE_AROUND -> {
                            if (val > currentConcentration &&
                                    (bestValue == null || val > bestValue)) {
                                bestValue = val; bestIx = ix; bestIy = iy;
                            }
                        }
                    }
                }
            }

            if (bestIx == null) {
                dx = dy = 0;
            } else {
                dx = bestIx;
                dy = bestIy;

                if (moveMode.equals(MOVE_AROUND)) {
                    double temp = dx;
                    dx = -dy;
                    dy = temp;
                }
            }
        }

        double length = hypot(dx, dy);
        if (length == 0) return;

        dx = (dx / length) * power * 0.1;
        dy = (dy / length) * power * 0.1;

        cell.calculateNewVelocity(dx, dy);
    }

    // ================================
    // JSON SUPPORT
    // ================================
    public Map<String, Object> toMap() {
        Map<String, Object> map = new HashMap<>();
        map.put("type", type);
        map.put("power", power);
        map.put("substance_name", substanceName);
        map.put("move_mode", moveMode);
        return map;
    }

    public static Action fromMap(Map<String, Object> data) {
        return new Action(
                (String) data.get("type"),
                ((Number) data.getOrDefault("power", 1.0)).doubleValue(),
                (String) data.get("substance_name"),
                (String) data.get("move_mode")
        );
    }
}
