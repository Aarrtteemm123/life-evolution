package com.life.evolution.model;

import com.fasterxml.jackson.databind.ObjectMapper;
import com.life.evolution.config.Config;

import java.io.File;
import java.io.IOException;
import java.util.HashMap;
import java.util.LinkedHashMap;
import java.util.Map;

public class World {

    private Environment env;
    private int tick;
    private double tickTimeMs;

    private static final ObjectMapper mapper = new ObjectMapper();

    // ------------------------------------------------------------
    // CONSTRUCTOR
    // ------------------------------------------------------------
    public World(int width, int height) {
        this.env = new Environment(width, height);
        this.tick = 0;
        this.tickTimeMs = 0;
    }

    public World(int width, int height, int tick, double tickTimeMs) {
        this.env = new Environment(width, height);
        this.tick = tick;
        this.tickTimeMs = tickTimeMs;
    }

    // ------------------------------------------------------------
    // UPDATE TICK
    // ------------------------------------------------------------
    public void update() {
        long start = System.nanoTime();

        tick++;

        env.updateCells();
        env.applyPhysics();
        env.spawnRandomOrganic();
        env.updateSubGrid();
        env.updateEnvStats();

        if (Config.AUTO_SAVE && tick % Config.TICK_SAVE_PERIOD == 0) {
            File dir = new File(Config.SAVES_DIR);
            if (!dir.exists()) dir.mkdirs();

            String fname = Config.SAVES_DIR + "/simulation_state_" + tick + ".json";
            try {
                save(fname);
            } catch (IOException e) {
                throw new RuntimeException("Failed to save world state: " + fname, e);
            }
        }

        tickTimeMs = (System.nanoTime() - start) / 1_000_000.0;
    }

    // ------------------------------------------------------------
    // SERIALIZE TO MAP
    // ------------------------------------------------------------
    public Map<String, Object> toMap() {
        Map<String, Object> m = new LinkedHashMap<>();
        m.put("tick", tick);
        m.put("tick_time_ms", tickTimeMs);
        m.put("environment", env.toMap());
        m.put("substances", Config.SUBSTANCES);
        return m;
    }

    // ------------------------------------------------------------
    // FROM MAP (deserialize)
    // ------------------------------------------------------------
    @SuppressWarnings("unchecked")
    public static World fromMap(Map<String, Object> m) {

        Map<String, Object> envMap = (Map<String, Object>) m.get("environment");
        Map<String, Object> gridMap = (Map<String, Object>) envMap.get("grid");

        // Restore global SUBSTANCES from save
        Object subs = m.get("substances");
        if (subs instanceof Map) {
            Config.SUBSTANCES = (Map<String, Map<String, Object>>) subs;
        }

        int width = ((Number) gridMap.get("width")).intValue();
        int height = ((Number) gridMap.get("height")).intValue();

        int tick = ((Number) m.getOrDefault("tick", 0)).intValue();
        double tickMs = ((Number) m.getOrDefault("tick_time_ms", 0.0)).doubleValue();

        World world = new World(width, height, tick, tickMs);

        // Now restore the environment fully
        Environment loadedEnv = Environment.fromMap(envMap);
        world.env = loadedEnv;

        return world;
    }

    // ------------------------------------------------------------
    // SAVE TO FILE (JSON)
    // ------------------------------------------------------------
    public void save(String filename) throws IOException {
        mapper.writerWithDefaultPrettyPrinter()
                .writeValue(new File(filename), toMap());
    }

    // ------------------------------------------------------------
    // LOAD FROM FILE
    // ------------------------------------------------------------
    public static World load(String filename) throws IOException {
        Map<String, Object> map =
                mapper.readValue(new File(filename), Map.class);
        return fromMap(map);
    }

    // ------------------------------------------------------------
    // GETTERS
    // ------------------------------------------------------------
    public Environment getEnv() { return env; }
    public int getTick() { return tick; }
    public double getTickTimeMs() { return tickTimeMs; }
}
