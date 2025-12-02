package com.life.evolution.model;

import com.life.evolution.config.Config;

import java.util.*;
import static java.lang.Math.*;

public class Environment {

    private SubstanceGrid grid;
    private List<Cell> cells;
    private List<Cell> bufferCells;
    private EnvStats envStats;

    public Environment(int width, int height) {
        this.grid = new SubstanceGrid(width, height);
        this.cells = new ArrayList<>();
        this.bufferCells = new ArrayList<>();
        this.envStats = new EnvStats();
    }

    // -----------------------------------------------------------
    // CELL MANAGEMENT
    // -----------------------------------------------------------
    public void addCellToBuffer(Cell c) {
        bufferCells.add(c);
    }

    public void loadFromBuffer() {
        cells.addAll(bufferCells);
        bufferCells.clear();
    }

    public void removeCell(Cell c) {
        cells.remove(c);
    }

    // -----------------------------------------------------------
    // SUBSTANCE MANAGEMENT
    // -----------------------------------------------------------
    public void addSubstance(int x, int y, Substance s) {
        grid.addSubstance(x, y, s);
    }

    // -----------------------------------------------------------
    // RANDOM ORGANIC SPAWNING
    // -----------------------------------------------------------
    public void spawnRandomOrganic() {
        for (int x = 0; x < grid.getWidth(); x++) {
            for (int y = 0; y < grid.getHeight(); y++) {

                if (Math.random() < Config.ORGANIC_SPAWN_PROBABILITY_PER_CELL_PER_TICK) {

                    Map<String, Object> org = Config.randomOrganicType();

                    String name = (String) org.get("name");
                    double energy = (double) org.get("energy");

                    Substance organic = new Substance(
                            name,
                            Substance.ORGANIC,
                            10.0,
                            energy
                    );

                    addSubstance(x, y, organic);
                }
            }
        }
    }

    // -----------------------------------------------------------
    // UPDATE SUBSTANCE GRID (diffusion / decay)
    // -----------------------------------------------------------
    public void updateSubGrid() {
        grid.update();
    }

    // -----------------------------------------------------------
    // UPDATE STATS
    // -----------------------------------------------------------
    public void updateEnvStats() {
        envStats.update(this);
    }

    // -----------------------------------------------------------
    // PHYSICS: cell repulsion
    // -----------------------------------------------------------
    public void applyPhysics() {
        if (cells.size() < 2) return;

        double minDist = 1.8 * Config.CELL_RADIUS;

        for (int i = 0; i < cells.size(); i++) {
            Cell c1 = cells.get(i);

            for (int j = i + 1; j < cells.size(); j++) {
                Cell c2 = cells.get(j);

                double dx = c1.getX() - c2.getX();
                double dy = c1.getY() - c2.getY();

                double dist = hypot(dx, dy);

                if (dist < minDist && dist > 0) {

                    double overlap = minDist - dist;
                    double force = overlap * Config.CELL_REPULSION_FORCE;

                    double nx, ny;

                    if (dist > 0) {
                        nx = dx / dist;
                        ny = dy / dist;
                    } else {
                        double angle = Math.PI * 2 * (i % 8) / 8;
                        nx = cos(angle);
                        ny = sin(angle);
                    }

                    // Apply to c1
                    c1.setVelocity(
                            c1.getVx() + nx * force,
                            c1.getVy() + ny * force
                    );

                    // Apply to c2 (opposite direction)
                    c2.setVelocity(
                            c2.getVx() - nx * force,
                            c2.getVy() - ny * force
                    );
                }
            }
        }
    }

    // -----------------------------------------------------------
    // UPDATE CELLS
    // -----------------------------------------------------------
    public void updateCells() {
        for (Cell c : cells) {
            if (c.isAlive()) c.update(this);
        }

        loadFromBuffer();
        cells.removeIf(c -> !c.isAlive());
    }

    // -----------------------------------------------------------
    // SERIALIZATION
    // -----------------------------------------------------------
    public Map<String, Object> toMap() {
        Map<String, Object> m = new HashMap<>();

        List<Map<String,Object>> cellsList = new ArrayList<>();
        for (Cell c : cells) cellsList.add(c.toMap());

        m.put("grid", grid.toMap());
        m.put("cells", cellsList);
        m.put("env_stats", envStats.toMap());

        return m;
    }

    @SuppressWarnings("unchecked")
    public static Environment fromMap(Map<String, Object> m) {
        Map<String, Object> gridData = (Map<String, Object>) m.get("grid");
        List<Map<String, Object>> cellsData = (List<Map<String, Object>>) m.get("cells");
        Map<String, Object> statsData = (Map<String, Object>) m.get("env_stats");

        int width = ((Number) gridData.get("width")).intValue();
        int height = ((Number) gridData.get("height")).intValue();

        Environment env = new Environment(width, height);
        env.grid = SubstanceGrid.fromMap(gridData);

        env.cells = new ArrayList<>();
        for (Map<String, Object> cMap : cellsData) {
            env.cells.add(Cell.fromMap(cMap));
        }

        env.envStats = EnvStats.fromMap(statsData);

        return env;
    }

    // -----------------------------------------------------------
    // GETTERS
    // -----------------------------------------------------------
    public SubstanceGrid getGrid() { return grid; }
    public List<Cell> getCells() { return cells; }
    public List<Cell> getBufferCells() { return bufferCells; }
    public EnvStats getEnvStats() { return envStats; }
}
