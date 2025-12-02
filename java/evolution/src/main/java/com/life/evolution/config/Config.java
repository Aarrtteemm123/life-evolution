package com.life.evolution.config;

import java.util.*;

public final class Config {

    private Config() {} // no instances allowed

    // ========================================================================
    // WORLD / GRID
    // ========================================================================
    public static final int WORLD_WIDTH = 50;
    public static final int WORLD_HEIGHT = 50;

    // ========================================================================
    // CELLS / POPULATION
    // ========================================================================
    public static final int CELL_COUNT = 50;
    public static final int CELLS_LIMIT = 1000;

    public static final double CELL_RADIUS = 0.5;

    // ========================================================================
    // CELL PHYSICS
    // ========================================================================
    public static final double CELL_REPULSION_FORCE = 2.5;

    public static final double FRICTION = 0.85;

    public static final double MAX_VELOCITY = 1.0;

    public static final double ACCELERATION_FACTOR = 0.07;

    public static final double MAX_ACCELERATION = 0.85;

    // ========================================================================
    // TIME / SIMULATION STEPS
    // ========================================================================
    public static final int SIMULATION_STEPS = 1000;

    public static final int FPS = 60;
    public static final double FRAME_TIME = 1.0 / FPS;

    public static final String SAVES_DIR = "saves/";

    public static boolean AUTO_SAVE = true;
    public static int TICK_SAVE_PERIOD = 10000;

    public static final boolean INCLUDE_BASE_GENES = true;

    // ========================================================================
    // SUBSTANCES / GENERATION / DIFFUSION
    // ========================================================================
    public static final Map<String, Integer> SUBSTANCE_DISTRIBUTION = Map.of(
            "ORGANIC", 100,
            "TOXIN", 10,
            "INORGANIC", 10
    );

    public static final int UNIQUE_INORGANIC_COUNT = 30;

    public static final double ORGANIC_SPAWN_PROBABILITY_PER_CELL_PER_TICK = 0.0008;

    public static final double SUBSTANCE_DIFFUSION_RATE = 0.1;

    // ========================================================================
    // SUBSTANCE TYPE LISTS
    // ========================================================================
    public static final List<Map<String, Object>> ORGANIC_TYPES = List.of(
            Map.of("name", "ORGANIC_0", "energy", 1.5, "concentration", List.of(0.1, 10.0)),
            Map.of("name", "ORGANIC_1", "energy", 3.0, "concentration", List.of(0.1, 10.0)),
            Map.of("name", "ORGANIC_2", "energy", 5.0, "concentration", List.of(0.1, 10.0))
    );

    public static final List<Map<String, Object>> TOXIN_TYPES = List.of(
            Map.of("name", "TOXIN_0", "energy", 1.0, "concentration", List.of(0.1, 10.0)),
            Map.of("name", "TOXIN_1", "energy", 3.0, "concentration", List.of(0.1, 10.0)),
            Map.of("name", "TOXIN_2", "energy", 4.0, "concentration", List.of(0.1, 10.0))
    );

    public static final List<Map<String, Object>> INORGANIC_TYPES = generateInorganicTypes();

    private static List<Map<String, Object>> generateInorganicTypes() {
        List<Map<String, Object>> list = new ArrayList<>();
        for (int i = 0; i < UNIQUE_INORGANIC_COUNT; i++) {
            list.add(
                    Map.of(
                            "name", "INORGANIC_" + i,
                            "energy", 0.5,
                            "concentration", List.of(0.1, 10.0)
                    )
            );
        }
        return List.copyOf(list);
    }

    // ========================================================================
    // ALL SUBSTANCE NAMES
    // ========================================================================
    public static final List<String> ALL_SUBSTANCE_NAMES = generateAllNames();

    private static List<String> generateAllNames() {
        List<String> names = new ArrayList<>();

        names.add("ORGANIC_0");
        names.add("ORGANIC_1");
        names.add("ORGANIC_2");

        names.add("TOXIN_0");
        names.add("TOXIN_1");
        names.add("TOXIN_2");

        for (int i = 0; i < UNIQUE_INORGANIC_COUNT; i++) {
            names.add("INORGANIC_" + i);
        }

        return List.copyOf(names);
    }

    // ========================================================================
    // GLOBAL SUBSTANCE PARAMETER STORAGE
    // Filled dynamically by World.load(...)
    // ========================================================================
    public static Map<String, Map<String, Object>> SUBSTANCES = new HashMap<>();

    // ========================================================================
    // HELPERS
    // ========================================================================
    public static String randomSubstanceName() {
        Random r = new Random();
        return ALL_SUBSTANCE_NAMES.get(r.nextInt(ALL_SUBSTANCE_NAMES.size()));
    }

    public static Map<String, Object> randomOrganicType() {
        Random r = new Random();
        return ORGANIC_TYPES.get(r.nextInt(ORGANIC_TYPES.size()));
    }
}
