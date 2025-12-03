package com.life.evolution.model;

import com.life.evolution.config.Config;

import java.security.MessageDigest;
import java.security.NoSuchAlgorithmException;
import java.util.*;
import static java.lang.Math.*;

public class Cell {

    // ---------------------------------------------------------------
    // FIELDS
    // ---------------------------------------------------------------
    private double x;
    private double y;

    private double vx;
    private double vy;

    private double energy;
    private double health;
    private int age;
    private boolean alive = true;

    private List<Gene> genes;
    private String colorHex;
    private double mutationRate;
    private int speciesDuration;

    // ---------------------------------------------------------------
    // CONSTRUCTORS
    // ---------------------------------------------------------------
    public Cell() {
        this(
                0, 0,            // x,y
                100, 100,        // energy, health
                0, true,         // age, alive
                new ArrayList<>(),
                null,            // color
                0.1,             // mutation rate
                0, 0,            // vx, vy
                0                // species duration
        );
    }

    public Cell(
            double x,
            double y,
            double energy,
            double health,
            int age,
            boolean alive,
            List<Gene> genes,
            String colorHex,
            double mutationRate,
            double vx,
            double vy,
            int speciesDuration
    ) {
        this.x = x;
        this.y = y;
        this.energy = energy;
        this.health = health;
        this.age = age;
        this.alive = alive;
        this.genes = (genes != null) ? genes : new ArrayList<>();
        this.colorHex = colorHex;
        this.mutationRate = mutationRate;
        this.vx = vx;
        this.vy = vy;
        this.speciesDuration = speciesDuration;

        if (this.colorHex == null) {
            updateColor();
        }
    }

    // ---------------------------------------------------------------
    // UPDATE LOOP
    // ---------------------------------------------------------------
    public void update(Environment env) {
        if (!alive) return;

        age++;
        speciesDuration++;
        energy -= 0.1;

        applyToxinDamage(env);

        for (Gene g : genes) {
            g.tryActivate(this, env);
        }

        move(env);

        if (energy <= 0.01 || health <= 0.01) {
            die(env);
        }
    }

    // ---------------------------------------------------------------
    // GET INT POSITION (Required by Action)
    // ---------------------------------------------------------------
    public int[] getIntPosition() {
        return new int[] { (int) x, (int) y };
    }

    // ---------------------------------------------------------------
    // TOXIN DAMAGE
    // ---------------------------------------------------------------
    private void applyToxinDamage(Environment env) {
        int cx = (int) x;
        int cy = (int) y;

        List<Substance> subs = env.getGrid().getSubstances(cx, cy);
        if (subs == null) return;

        double total = 0;

        for (Substance s : subs) {
            if (Substance.TOXIN.equals(s.getType()) && s.getConcentration() > 0.01) {
                total += s.getEnergy() * s.getConcentration();
            }
        }

        if (total > 0) {
            health -= total;
            if (health < 0) health = 0;
        }
    }

    // ---------------------------------------------------------------
    // ABSORB / EMIT
    // ---------------------------------------------------------------
    public void absorb(Substance sub) {
        if (sub == null || sub.getConcentration() <= 0.01) return;

        energy += sub.getConcentration() * sub.getEnergy();
        sub.setConcentration(0);
    }

    public void emit(String name, double amount, Environment env) {
        if (energy <= 0.001 || amount <= 0.001) return;

        var data = Substance.findSubstance(name);
        double e = (double) data.get("energy");

        double energyCost = amount * e;
        if (energy < energyCost) {
            amount = energy / e;
            energyCost = amount * e;
        }
        energy -= energyCost;

        int cx = (int) x;
        int cy = (int) y;

        int[][] dirs = {
                {0,0}, {-1,0},{1,0},{0,-1},{0,1},
                {-1,-1},{-1,1},{1,-1},{1,1}
        };

        double part = amount / dirs.length;

        for (int[] d : dirs) {
            int nx = cx + d[0];
            int ny = cy + d[1];

            if (nx < 0 || nx >= env.getGrid().getWidth()) continue;
            if (ny < 0 || ny >= env.getGrid().getHeight()) continue;

            env.addSubstance(nx, ny, new Substance(
                    name,
                    (String) data.get("type"),
                    part,
                    e
            ));
        }
    }

    // ---------------------------------------------------------------
    // MOVEMENT
    // ---------------------------------------------------------------
    public void move(Environment env) {

        vx *= Config.FRICTION;
        vy *= Config.FRICTION;

        double speed = hypot(vx, vy);
        if (speed > Config.MAX_VELOCITY) {
            vx = (vx / speed) * Config.MAX_VELOCITY;
            vy = (vy / speed) * Config.MAX_VELOCITY;
        }

        double newX = x + vx;
        double newY = y + vy;

        int maxX = env.getGrid().getWidth();
        int maxY = env.getGrid().getHeight();

        if (newX < 0) { newX = Config.CELL_RADIUS; vx = 0; }
        else if (newX > maxX) { newX = maxX - Config.CELL_RADIUS; vx = 0; }

        if (newY < 0) { newY = Config.CELL_RADIUS; vy = 0; }
        else if (newY > maxY) { newY = maxY - Config.CELL_RADIUS; vy = 0; }

        x = newX;
        y = newY;

        energy -= 0.05 * speed;
    }

    public void calculateNewVelocity(double dx, double dy) {
        double len = hypot(dx, dy);
        if (len == 0) return;

        double ndx = (dx / len) * Config.MAX_ACCELERATION;
        double ndy = (dy / len) * Config.MAX_ACCELERATION;

        vx = vx * (1 - Config.ACCELERATION_FACTOR) + ndx * Config.ACCELERATION_FACTOR;
        vy = vy * (1 - Config.ACCELERATION_FACTOR) + ndy * Config.ACCELERATION_FACTOR;
    }

    // ---------------------------------------------------------------
    // DIVISION / MUTATION
    // ---------------------------------------------------------------
    public Cell divide(Environment env) {
        if (energy < 0.1 ||
                env.getCells().size() + env.getBufferCells().size() > Config.CELLS_LIMIT) {
            return null;
        }

        Cell c = cloneCell();

        c.age = 0;

        double half = energy / 2;
        energy = half;
        c.energy = half;

        c.x = x + (Math.random() < 0.5 ? 0.5 : -0.5);
        c.y = y + (Math.random() < 0.5 ? 0.5 : -0.5);

        c.vx = random(-0.5, 0.5);
        c.vy = random(-0.5, 0.5);

        if (isTriggeredMutation() && c.mutate()) {
            c.speciesDuration = 0;
            c.updateColor();
        }

        return c;
    }

    private static double random(double a, double b) {
        return Math.random() * (b - a) + a;
    }

    public boolean mutate() {
        boolean changed = false;
        List<Gene> newGenes = new ArrayList<>();

        for (Gene g : genes) {
            var before = g.toMap();
            Gene created = g.mutate();

            if (created != null) {
                newGenes.add(created);
                changed = true;
            } else if (!g.toMap().equals(before)) {
                changed = true;
            }
        }

        if (!newGenes.isEmpty()) {
            genes.addAll(newGenes);
            changed = true;
        }

        return changed;
    }

    public boolean isTriggeredMutation() {
        return Math.random() < mutationRate;
    }

    // ---------------------------------------------------------------
    // DEATH & HEAL
    // ---------------------------------------------------------------
    public void die(Environment env) {
        alive = false;

        int cx = (int) x;
        int cy = (int) y;

        double total = energy;

        if (total > 0) {
            Map<String, Object> org = Config.randomOrganicType();

            String name = (String) org.get("name");
            double e = (double) org.get("energy");

            double concentration = total / e;

            env.addSubstance(cx, cy, new Substance(
                    name,
                    Substance.ORGANIC,
                    concentration,
                    e
            ));
        }

        energy = 0;
        health = 0;
    }

    public void heals(double amount) {
        if (amount < 1) amount = 1;
        if (energy < amount + 5 || health > 100) return;

        energy -= amount;
        health += amount;
        if (health > 100) health = 100;
    }

    // ---------------------------------------------------------------
    // COLOR (SHA-1 HASH)
    // ---------------------------------------------------------------
    public void updateColor() {
        try {
            MessageDigest sha1 = MessageDigest.getInstance("SHA-1");
            byte[] digest = sha1.digest(getGenesSignature().getBytes());

            int r = digest[0] ^ digest[3] ^ digest[6] ^ digest[9];
            int g = digest[1] ^ digest[4] ^ digest[7] ^ digest[10];
            int b = digest[2] ^ digest[5] ^ digest[8] ^ digest[11];

            r = Math.min(255, 100 + r / 2);
            g = Math.min(255, 100 + g / 2);
            b = Math.min(255, 100 + b / 2);

            this.colorHex = String.format("#%02X%02X%02X", r, g, b);
        }
        catch (NoSuchAlgorithmException e) {
            this.colorHex = "#FFFFFF";
        }
    }

    public String getGenesSignature() {
        List<String> list = new ArrayList<>();
        for (Gene g : genes) list.add(g.toTuple());
        list.sort(String::compareTo);
        return String.join("|", list);
    }

    // ---------------------------------------------------------------
    // CLONE & MAP SERIALIZATION
    // ---------------------------------------------------------------
    public Cell cloneCell() {
        return fromMap(toMap());
    }

    public Map<String, Object> toMap() {
        Map<String, Object> m = new HashMap<>();

        m.put("position", List.of(x, y));
        m.put("velocity", List.of(vx, vy));
        m.put("species_duration", speciesDuration);
        m.put("energy", energy);
        m.put("health", health);
        m.put("age", age);
        m.put("color_hex", colorHex);
        m.put("mutation_rate", mutationRate);

        List<Map<String,Object>> geneList = new ArrayList<>();
        for (Gene g : genes) geneList.add(g.toMap());
        m.put("genes", geneList);

        return m;
    }

    @SuppressWarnings("unchecked")
    public static Cell fromMap(Map<String, Object> m) {
        List<Number> pos = (List<Number>) m.get("position");
        List<Number> vel = (List<Number>) m.getOrDefault("velocity", List.of(0,0));

        Cell c = new Cell(
                pos.get(0).doubleValue(),
                pos.get(1).doubleValue(),
                ((Number)m.get("energy")).doubleValue(),
                ((Number)m.get("health")).doubleValue(),
                ((Number)m.get("age")).intValue(),
                true,
                new ArrayList<>(),
                (String)m.get("color_hex"),
                ((Number)m.get("mutation_rate")).doubleValue(),
                vel.get(0).doubleValue(),
                vel.get(1).doubleValue(),
                ((Number)m.get("species_duration")).intValue()
        );

        List<Map<String,Object>> gList =
                (List<Map<String,Object>>) m.getOrDefault("genes", List.of());
        for (Map<String,Object> gm : gList) {
            c.genes.add(Gene.fromMap(gm));
        }

        return c;
    }

    // ---------------------------------------------------------------
    // GETTERS
    // ---------------------------------------------------------------
    public boolean isAlive() { return alive; }
    public double getX() { return x; }
    public double getY() { return y; }
    public double getVx() { return vx; }
    public double getVy() { return vy; }
    public String getColorHex() { return colorHex; }
    public List<Gene> getGenes() { return genes; }
    public double getEnergy() {
        return energy;
    }

    public double getHealth() {
        return health;
    }

    public int getAge() {
        return age;
    }

    public int getSpeciesDuration() {
        return speciesDuration;
    }

    public double getMutationRate() {
        return mutationRate;
    }

    public void setVelocity(double vx, double vy) {
        this.vx = vx;
        this.vy = vy;
    }

    @Override
    public String toString() {
        return "Cell{" +
                "pos=(" + x + "," + y + ")" +
                ", E=" + energy +
                ", H=" + health +
                ", age=" + age +
                ", vel=(" + vx + "," + vy + ")" +
                ", genes=" + genes.size() +
                ", color=" + colorHex +
                ", mutationRate=" + mutationRate +
                ", speciesDur=" + speciesDuration +
                '}';
    }
}
