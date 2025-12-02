package com.life.evolution.model;

import com.life.evolution.config.Config;

import java.util.*;

public class SubstanceGrid {

    // --- coordinate pair for keys ---
    public record CellPos(int x, int y) {}

    private int width;
    private int height;

    // (x,y) -> list of substances
    private Map<CellPos, List<Substance>> grid;

    public SubstanceGrid(int width, int height) {
        this.width = width;
        this.height = height;
        this.grid = new HashMap<>();
    }

    // ------------------------------------------------------------
    // UPDATE (decay + diffusion)
    // ------------------------------------------------------------
    public void update() {
        if (Config.SUBSTANCE_DIFFUSION_RATE > 0) {
            diffuse(Config.SUBSTANCE_DIFFUSION_RATE);
        }

        for (CellPos pos : new ArrayList<>(grid.keySet())) {
            List<Substance> filtered = new ArrayList<>();

            for (Substance s : grid.get(pos)) {
                s.update();
                if (s.isActive()) filtered.add(s);
            }

            if (filtered.isEmpty()) grid.remove(pos);
            else grid.put(pos, filtered);
        }
    }

    // ------------------------------------------------------------
    // DIFFUSION
    // ------------------------------------------------------------
    public void diffuse(double rate) {
        if (rate <= 0) return;

        Map<CellPos, List<Substance>> next = new HashMap<>();

        for (var entry : grid.entrySet()) {
            CellPos pos = entry.getKey();
            int x = pos.x();
            int y = pos.y();

            for (Substance s : entry.getValue()) {
                if (s.getConcentration() < 0.01) continue;

                double original = s.getConcentration();
                double mainPart = original * (1 - rate);
                double spread = (original * rate) / 4.0;

                int neighborCount = 0;

                // Four main directions
                int[][] dirs = {
                        {1,0}, {-1,0}, {0,1}, {0,-1}
                };

                for (int[] d : dirs) {
                    int nx = x + d[0];
                    int ny = y + d[1];

                    if (nx < 0 || nx >= width || ny < 0 || ny >= height)
                        continue;

                    neighborCount++;

                    next.computeIfAbsent(new CellPos(nx, ny), k -> new ArrayList<>())
                            .add(new Substance(
                                    s.getName(),
                                    s.getType(),
                                    spread,
                                    s.getEnergy(),
                                    s.getVolatility()
                            ));
                }

                // If some neighbors unavailable, put leftover into main cell
                if (neighborCount < 4) {
                    mainPart += spread * (4 - neighborCount);
                }

                if (mainPart > 0.01) {
                    next.computeIfAbsent(pos, k -> new ArrayList<>())
                            .add(new Substance(
                                    s.getName(),
                                    s.getType(),
                                    mainPart,
                                    s.getEnergy(),
                                    s.getVolatility()
                            ));
                }
            }
        }

        // --- MERGING (combine same substances in same cell) ---
        Map<CellPos, List<Substance>> merged = new HashMap<>();

        for (var entry : next.entrySet()) {
            CellPos pos = entry.getKey();
            Map<String, Substance> byName = new HashMap<>();

            for (Substance s : entry.getValue()) {
                if (byName.containsKey(s.getName())) {
                    byName.get(s.getName()).setConcentration(
                            byName.get(s.getName()).getConcentration() + s.getConcentration()
                    );
                } else {
                    byName.put(s.getName(), s.cloneSubstance());
                }
            }

            merged.put(pos, new ArrayList<>(byName.values()));
        }

        this.grid = merged;
    }

    // ------------------------------------------------------------
    // QUERY
    // ------------------------------------------------------------
    public List<Substance> getSubstances(int x, int y) {
        return grid.getOrDefault(new CellPos(x, y), Collections.emptyList());
    }

    public Substance getSubstance(int x, int y, String name) {
        for (Substance s : grid.getOrDefault(new CellPos(x, y), Collections.emptyList())) {
            if (s.getName().equals(name)) return s;
        }
        return null;
    }

    public void setSubstances(int x, int y, List<Substance> list) {
        if (x < 0 || x >= width || y < 0 || y >= height) return;
        grid.put(new CellPos(x, y), list);
    }

    public void addSubstance(int x, int y, Substance s) {
        if (x < 0 || x >= width || y < 0 || y >= height) return;

        CellPos pos = new CellPos(x, y);
        List<Substance> list = grid.computeIfAbsent(pos, k -> new ArrayList<>());

        // Mix with same substance type
        for (Substance existing : list) {
            if (existing.getName().equals(s.getName())) {
                existing.setConcentration(existing.getConcentration() + s.getConcentration());
                return;
            }
        }

        list.add(s.cloneSubstance());
    }

    public double getConcentration(int x, int y, String name) {
        for (Substance s : grid.getOrDefault(new CellPos(x, y), Collections.emptyList())) {
            if (s.getName().equals(name)) {
                return s.getConcentration();
            }
        }
        return 0.0;
    }

    // ------------------------------------------------------------
    // SERIALIZATION
    // ------------------------------------------------------------
    public Map<String, Object> toMap() {
        Map<String, Object> m = new HashMap<>();
        List<Map<String, Object>> all = new ArrayList<>();

        for (var entry : grid.entrySet()) {
            int x = entry.getKey().x();
            int y = entry.getKey().y();

            for (Substance s : entry.getValue()) {
                Map<String, Object> d = s.toMap();
                d.put("x", x);
                d.put("y", y);
                all.add(d);
            }
        }

        m.put("width", width);
        m.put("height", height);
        m.put("substances", all);
        return m;
    }

    @SuppressWarnings("unchecked")
    public static SubstanceGrid fromMap(Map<String, Object> m) {
        int w = ((Number) m.get("width")).intValue();
        int h = ((Number) m.get("height")).intValue();

        SubstanceGrid grid = new SubstanceGrid(w, h);

        List<Map<String, Object>> list = (List<Map<String, Object>>) m.get("substances");
        for (Map<String, Object> subMap : list) {
            Substance s = Substance.fromMap(subMap);
            int x = ((Number) subMap.get("x")).intValue();
            int y = ((Number) subMap.get("y")).intValue();
            grid.addSubstance(x, y, s);
        }

        return grid;
    }

    @Override
    public String toString() {
        int cellCount = grid.size();
        int totalSubs = grid.values().stream().mapToInt(List::size).sum();

        return "SubstanceGrid(" +
                width + "x" + height +
                ", cells=" + cellCount +
                ", substances=" + totalSubs +
                ")";
    }

    // ------------------------------------------------------------
    // GETTERS
    // ------------------------------------------------------------
    public int getWidth() { return width; }
    public int getHeight() { return height; }
    public Map<CellPos, List<Substance>> getGrid() { return grid; }
}
