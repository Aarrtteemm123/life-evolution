package com.life.evolution.component;

import com.life.evolution.config.Config;
import com.life.evolution.model.*;

import java.io.File;
import java.io.IOException;
import java.util.*;

public final class Helper {

    private Helper() {}

    private static final Random rnd = new Random();

    // ========================================================================
    // GENERATE SUBSTANCES
    // ========================================================================
    public static void generateSubstances(Map<String, Map<String, Object>> container) {
        container.clear();

        // --- Organic ---
        for (Map<String, Object> d : Config.ORGANIC_TYPES) {
            container.put(
                    (String) d.get("name"),
                    Map.of(
                            "type", Substance.ORGANIC,
                            "energy", (double) d.get("energy")
                    )
            );
        }

        // --- Toxins ---
        for (Map<String, Object> d : Config.TOXIN_TYPES) {
            container.put(
                    (String) d.get("name"),
                    Map.of(
                            "type", Substance.TOXIN,
                            "energy", (double) d.get("energy")
                    )
            );
        }

        // --- Inorganic ---
        for (Map<String, Object> d : Config.INORGANIC_TYPES) {
            container.put(
                    (String) d.get("name"),
                    Map.of(
                            "type", Substance.INORGANIC,
                            "energy", (double) d.get("energy")
                    )
            );
        }
    }

    // ========================================================================
    // RANDOM SUBSTANCE
    // ========================================================================
    public static Substance randomSubstance(String type) {

        List<String> names;

        if (type != null) {
            names = new ArrayList<>();
            for (var e : Config.SUBSTANCES.entrySet()) {
                if (Objects.equals(e.getValue().get("type"), type)) {
                    names.add(e.getKey());
                }
            }
            if (names.isEmpty()) return null;
        } else {
            names = new ArrayList<>(Config.SUBSTANCES.keySet());
        }

        String name = names.get(rnd.nextInt(names.size()));
        Map<String, Object> data = Config.SUBSTANCES.get(name);

        double conc = randomRange(0.1, 100.0);

        return new Substance(
                name,
                (String) data.get("type"),
                conc,
                (double) data.get("energy")
        );
    }

    public static Substance randomSubstance() {
        return randomSubstance(null);
    }

    // ========================================================================
    // BASE GENES
    // ========================================================================
    public static List<Gene> baseGenes() {
        List<Gene> genes = new ArrayList<>();

        // 1. Move toward organic ("food")
        for (Map<String, Object> org : Config.ORGANIC_TYPES) {
            String name = (String) org.get("name");

            Gene moveToFood = new Gene(
                    name,
                    new Trigger(0.1, Trigger.GREATER),
                    new Action(Action.MOVE, 1.0, null, Action.MOVE_TOWARD)
            );
            genes.add(moveToFood);
        }

        // 2. Absorb organic when concentration high enough
        for (Map<String, Object> org : Config.ORGANIC_TYPES) {
            String name = (String) org.get("name");

            Gene absorb = new Gene(
                    name,
                    new Trigger(0.3, Trigger.GREATER),
                    new Action(Action.ABSORB, 1.0, name, null)
            );
            genes.add(absorb);
        }

        // 3. Divide on high energy
        Gene divideEnergy = new Gene(
                "energy",
                new Trigger(90, Trigger.GREATER),
                new Action(Action.DIVIDE, 1.0, null, null)
        );
        genes.add(divideEnergy);

        return genes;
    }

    // ========================================================================
    // RANDOM CELL
    // ========================================================================
    public static Cell randomCell(int x, int y) {
        return randomCell(x, y, Config.INCLUDE_BASE_GENES);
    }

    public static Cell randomCell(int x, int y, boolean includeBaseGenes) {

        Cell c = new Cell(
                x + rnd.nextDouble(),         // x
                y + rnd.nextDouble(),         // y
                100.0,                        // energy
                100.0,                        // health
                0,                            // age
                true,                         // alive
                new ArrayList<>(),            // genes
                null,                         // colorHex
                0.1,                          // mutationRate
                0.0,                          // vx
                0.0,                          // vy
                0                              // speciesDuration
        );

        if (includeBaseGenes) {
            c.getGenes().addAll(baseGenes());
        }

        int geneCount = weightedChoice(
                new int[]{1,2,3,4,5,6,7,8,9,10},
                new int[]{10,15,20,20,15,10,5,3,1,1}
        );

        for (int i = 0; i < geneCount; i++) {
            c.getGenes().add(Gene.createRandomGene());
        }

        return c;
    }

    // ========================================================================
    // POPULATE WORLD
    // ========================================================================
    public static void populateWorld(World world) {
        Environment env = world.getEnv();

        // Create substance definitions
        generateSubstances(Config.SUBSTANCES);

        // 1. Populate grid with random substance sources
        for (var entry : Config.SUBSTANCE_DISTRIBUTION.entrySet()) {
            String category = entry.getKey();
            int count = entry.getValue();

            for (int i = 0; i < count; i++) {
                int x = rnd.nextInt(env.getGrid().getWidth());
                int y = rnd.nextInt(env.getGrid().getHeight());
                Substance s = randomSubstance(category);
                if (s != null) env.addSubstance(x, y, s);
            }
        }

        // 2. Spawn initial cells
        for (int i = 0; i < Config.CELL_COUNT; i++) {
            int x = rnd.nextInt(env.getGrid().getWidth());
            int y = rnd.nextInt(env.getGrid().getHeight());
            Cell c = randomCell(x, y);
            env.addCellToBuffer(c);
        }

        env.loadFromBuffer();
    }

    // ========================================================================
    // RUN OFFLINE SIMULATION (like Python)
    // ========================================================================
    public static void runSimulation() {
        System.out.println("🔬 Initializing world...");
        World world = new World(Config.WORLD_WIDTH, Config.WORLD_HEIGHT);
        populateWorld(world);

        System.out.println("🌎 World created: " +
                world.getEnv().getCells().size() + " cells, " +
                world.getEnv().getGrid().getGrid().size() + " active substance cells.");

        System.out.println("🚀 Starting simulation...");

        long start = System.nanoTime();
        long last = start;

        for (int step = 0; step < Config.SIMULATION_STEPS; step++) {

            world.update();

            if (step % 10 == 0 && step > 0) {
                long now = System.nanoTime();
                double elapsed = (now - last) / 1e9;
                double tps = 10 / elapsed;
                double msPerTick = (elapsed / 10) * 1000;

                System.out.printf(
                        "Step %4d | tick=%4d | cells=%3d | %.2f tps | %.2f ms/tick\n",
                        step, world.getTick(), world.getEnv().getCells().size(), tps, msPerTick
                );

                last = now;
            }
        }

        double totalSec = (System.nanoTime() - start) / 1e9;
        double avgTick = totalSec / Config.SIMULATION_STEPS;

        System.out.println("⏱️ Total time: " + String.format("%.2fs", totalSec));
        System.out.println("⚡ Avg speed: " +
                String.format("%.2f ticks/sec (%.2f ms/tick)", 1/avgTick, avgTick*1000));

        // === SAVE ===
        File dir = new File(Config.SAVES_DIR);
        if (!dir.exists()) dir.mkdirs();

        String savePath = Config.SAVES_DIR + "/simulation_state.json";

        System.out.println("💾 Saving state...");
        try {
            world.save(savePath);
        } catch (IOException e) {
            throw new RuntimeException(e);
        }

        System.out.println("✅ Simulation saved to " + savePath);

        // === LOAD TEST ===
        try {
            World restored = World.load(savePath);
            System.out.println("♻️ Load successful! Tick: " + restored.getTick());
        } catch (IOException e) {
            throw new RuntimeException("Failed to reload world!", e);
        }
    }

    // ========================================================================
    // UTILS
    // ========================================================================
    private static double randomRange(double a, double b) {
        return rnd.nextDouble() * (b - a) + a;
    }

    private static int weightedChoice(int[] values, int[] weights) {
        int sum = 0;
        for (int w : weights) sum += w;

        int r = rnd.nextInt(sum);
        int cumulative = 0;

        for (int i = 0; i < values.length; i++) {
            cumulative += weights[i];
            if (r < cumulative) return values[i];
        }
        return values[values.length - 1];
    }
}
