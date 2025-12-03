package com.life.evolution.model;

import com.fasterxml.jackson.databind.ObjectMapper;
import com.life.evolution.component.Helper;
import com.life.evolution.config.Config;

import java.io.File;
import java.io.IOException;
import java.util.*;

public class World {

    private Environment env;
    private int tick;
    private double tickTimeMs;
    private String uuid;

    private static final ObjectMapper mapper = new ObjectMapper();

    // ------------------------------------------------------------
    // CONSTRUCTORS
    // ------------------------------------------------------------
    public World(int width, int height) {
        this.env = new Environment(width, height);
        this.tick = 0;
        this.tickTimeMs = 0;
        this.uuid = UUID.randomUUID().toString();
    }

    public World(int width, int height, int tick, double tickTimeMs) {
        this.env = new Environment(width, height);
        this.tick = tick;
        this.tickTimeMs = tickTimeMs;
        this.uuid = UUID.randomUUID().toString();
    }

    // ------------------------------------------------------------
    // UPDATE
    // ------------------------------------------------------------
    public void update() {
        long start = System.nanoTime();
        tick++;

        env.updateCells();
        env.applyPhysics();
        env.spawnRandomOrganic();
        env.updateSubGrid();
        env.updateEnvStats();

        // 💥 Auto-restore if no cells
        if (env.getCells().isEmpty()) {
            restoreLastSave();
            return;
        }

        // 💾 Auto-save world
        if (Config.AUTO_SAVE && tick % Config.TICK_SAVE_PERIOD == 0) {
            File dir = new File(Config.SAVES_DIR);
            if (!dir.exists()) dir.mkdirs();

            String fname = Config.SAVES_DIR + "/simulation_state_" + uuid + "_" + tick + ".json";
            try {
                save(fname);
            } catch (IOException e) {
                throw new RuntimeException("Failed to save world state: " + fname, e);
            }
        }

        tickTimeMs = (System.nanoTime() - start) / 1_000_000.0;
    }

    // ------------------------------------------------------------
    // RESTORE LAST SAVE (new logic)
    // ------------------------------------------------------------
    private void restoreLastSave() {
        File dir = new File(Config.SAVES_DIR);
        if (!dir.exists() || !dir.isDirectory()) return;

        File[] files = dir.listFiles((d, name) ->
                name.startsWith("simulation_state_" + uuid)
                        && name.endsWith(".json")
        );

        if (files == null || files.length == 0) return;

        // find file with max tick
        File last = null;
        int bestTick = -1;

        for (File f : files) {
            String name = f.getName();
            try {
                String tStr = name
                        .replace("simulation_state_" + uuid + "_", "")
                        .replace(".json", "");

                int t = Integer.parseInt(tStr);
                if (t > bestTick) {
                    bestTick = t;
                    last = f;
                }
            } catch (Exception ignored) {}
        }

        if (last == null) return;

        System.out.println("Restoring last save: " + last.getAbsolutePath());

        try {
            World restored = World.load(last.getAbsolutePath());
            this.env = restored.env;
            this.tick = restored.tick;
            this.tickTimeMs = restored.tickTimeMs;
            this.uuid = restored.uuid;
        } catch (IOException ignored) {}
    }

    // ------------------------------------------------------------
    // SERIALIZE
    // ------------------------------------------------------------
    public Map<String, Object> toMap() {
        Map<String, Object> m = new LinkedHashMap<>();
        m.put("uuid", uuid);
        m.put("tick", tick);
        m.put("tick_time_ms", tickTimeMs);
        m.put("environment", env.toMap());
        m.put("substances", Config.SUBSTANCES);
        return m;
    }

    // ------------------------------------------------------------
    // DESERIALIZE
    // ------------------------------------------------------------
    @SuppressWarnings("unchecked")
    public static World fromMap(Map<String, Object> m) {

        Map<String, Object> envMap = (Map<String, Object>) m.get("environment");
        Map<String, Object> gridMap = (Map<String, Object>) envMap.get("grid");

        int width = ((Number) gridMap.get("width")).intValue();
        int height = ((Number) gridMap.get("height")).intValue();

        int tick = ((Number) m.getOrDefault("tick", 0)).intValue();
        double tickMs = ((Number) m.getOrDefault("tick_time_ms", 0.0)).doubleValue();

        World world = new World(width, height, tick, tickMs);

        // uuid
        Object uuidObj = m.get("uuid");
        if (uuidObj instanceof String) {
            world.uuid = (String) uuidObj;
        }

        // Restore or regenerate SUBSTANCES
        Object subs = m.get("substances");
        if (subs instanceof Map) {
            Config.SUBSTANCES = (Map<String, Map<String, Object>>) subs;
        } else {
            Helper.generateSubstances(Config.SUBSTANCES); // 🔧 you must implement similar to python generate_substances()
        }

        // Restore environment
        Environment loadedEnv = Environment.fromMap(envMap);
        world.env = loadedEnv;

        return world;
    }

    // ------------------------------------------------------------
    // SAVE
    // ------------------------------------------------------------
    public void save(String filename) throws IOException {
        mapper.writerWithDefaultPrettyPrinter()
                .writeValue(new File(filename), toMap());
    }

    // ------------------------------------------------------------
    // LOAD
    // ------------------------------------------------------------
    public static World load(String filename) throws IOException {
        Map<String, Object> map = mapper.readValue(new File(filename), Map.class);
        return fromMap(map);
    }

    // ------------------------------------------------------------
    // GETTERS
    // ------------------------------------------------------------
    public Environment getEnv() { return env; }
    public int getTick() { return tick; }
    public double getTickTimeMs() { return tickTimeMs; }
    public String getUuid() { return uuid; }
}
