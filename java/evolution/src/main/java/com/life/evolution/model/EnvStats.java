package com.life.evolution.model;

import com.life.evolution.config.Config;

import java.util.*;
import java.util.stream.Collectors;

public class EnvStats {

    private int cellsTotal;
    private int cellsLimit;
    private int uniqueCells;

    private double avgEnergy;
    private double avgHealth;
    private double avgAge;
    private double avgGenes;
    private double avgActiveGenes;

    private List<Map<String, Object>> topCells;
    private List<Map<String, Object>> topCellsBySpeciesDuration;

    private int totalUniqueSubstances;
    private Map<String, Integer> totalSubstancesByType;
    private Map<String, Double> totalSubstancesConcentrationByType;

    public EnvStats() {
        this.cellsTotal = 0;
        this.cellsLimit = Config.CELLS_LIMIT;
        this.uniqueCells = 0;

        this.avgEnergy = 0;
        this.avgHealth = 0;
        this.avgAge = 0;
        this.avgGenes = 0;
        this.avgActiveGenes = 0;

        this.topCells = new ArrayList<>();
        this.topCellsBySpeciesDuration = new ArrayList<>();

        this.totalUniqueSubstances = 0;
        this.totalSubstancesByType = new HashMap<>();
        this.totalSubstancesConcentrationByType = new HashMap<>();
    }

    // ------------------------------------------------------------
    // UPDATE
    // ------------------------------------------------------------
    public void update(Environment env) {
        List<Cell> cells = env.getCells();
        SubstanceGrid grid = env.getGrid();

        this.cellsTotal = cells.size();

        // ------------------------------
        // 1. Cells
        // ------------------------------
        List<Cell> alive = cells.stream()
                .filter(Cell::isAlive)
                .collect(Collectors.toList());

        if (!alive.isEmpty()) {
            avgEnergy = alive.stream().mapToDouble(Cell::getEnergy).average().orElse(0);
            avgHealth = alive.stream().mapToDouble(Cell::getHealth).average().orElse(0);
            avgAge = alive.stream().mapToDouble(Cell::getAge).average().orElse(0);
            avgGenes = alive.stream().mapToDouble(c -> c.getGenes().size()).average().orElse(0);

            avgActiveGenes = alive.stream()
                    .mapToDouble(c ->
                            c.getGenes().stream().filter(Gene::isActive).count()
                    )
                    .average()
                    .orElse(0);
        } else {
            avgEnergy = avgHealth = avgAge = avgGenes = avgActiveGenes = 0;
        }

        // --- 1.1. Top variants by count (species)
        Map<String, Long> geneCount = alive.stream()
                .collect(Collectors.groupingBy(Cell::getColorHex, Collectors.counting()));

        this.uniqueCells = geneCount.size();

        this.topCells = geneCount.entrySet().stream()
                .sorted((a, b) -> Long.compare(b.getValue(), a.getValue()))
                .limit(5)
                .map(e -> {
                    Map<String, Object> m = new HashMap<>();
                    m.put("key", e.getKey());
                    m.put("count", e.getValue());
                    return m;
                })
                .collect(Collectors.toList());

        // --- 1.2. Top species by max speciesDuration
        Map<String, Integer> speciesDurationMap = new HashMap<>();

        for (Cell c : alive) {
            String key = c.getColorHex();
            int sd = c.getSpeciesDuration();

            speciesDurationMap.put(key,
                    Math.max(speciesDurationMap.getOrDefault(key, 0), sd));
        }

        this.topCellsBySpeciesDuration = speciesDurationMap.entrySet().stream()
                .sorted((a, b) -> Integer.compare(b.getValue(), a.getValue()))
                .limit(5)
                .map(e -> {
                    Map<String, Object> m = new HashMap<>();
                    m.put("key", e.getKey());
                    m.put("species_duration", e.getValue());
                    return m;
                })
                .collect(Collectors.toList());

        // ------------------------------
        // 2. Substances
        // ------------------------------
        Map<String, Double> unique = new HashMap<>();

        for (List<Substance> list : grid.getGrid().values()) {
            for (Substance s : list) {
                String k = s.getName() + "|" + s.getType();
                unique.put(k, unique.getOrDefault(k, 0.0) + s.getConcentration());
            }
        }

        this.totalUniqueSubstances = unique.size();

        Map<String, Integer> countByType = new HashMap<>();
        Map<String, Double> concByType = new HashMap<>();

        for (Map.Entry<String, Double> e : unique.entrySet()) {
            String[] parts = e.getKey().split("\\|");
            String type = parts[1];
            double conc = e.getValue();

            countByType.put(type, countByType.getOrDefault(type, 0) + 1);
            concByType.put(type, concByType.getOrDefault(type, 0.0) + conc);
        }

        // consistent ordering
        List<String> types = List.of("ORGANIC", "INORGANIC", "TOXIN");

        this.totalSubstancesByType = new HashMap<>();
        this.totalSubstancesConcentrationByType = new HashMap<>();

        for (String t : types) {
            totalSubstancesByType.put(t, countByType.getOrDefault(t, 0));
            totalSubstancesConcentrationByType.put(
                    t,
                    Math.round(concByType.getOrDefault(t, 0.0) * 1000) / 1000.0
            );
        }
    }

    // ------------------------------------------------------------
    // SERIALIZATION
    // ------------------------------------------------------------
    public Map<String, Object> toMap() {
        Map<String, Object> m = new LinkedHashMap<>();

        m.put("cells_total", cellsTotal);
        m.put("cells_limit", cellsLimit);
        m.put("unique_cells", uniqueCells);

        m.put("avg_energy", avgEnergy);
        m.put("avg_health", avgHealth);
        m.put("avg_age", avgAge);
        m.put("avg_genes", avgGenes);
        m.put("avg_active_genes", avgActiveGenes);

        m.put("top_cells", topCells);
        m.put("top_cells_by_species_duration", topCellsBySpeciesDuration);

        m.put("total_unique_substances", totalUniqueSubstances);
        m.put("substances_by_type", totalSubstancesByType);
        m.put("substances_concentration_by_type", totalSubstancesConcentrationByType);

        return m;
    }

    @SuppressWarnings("unchecked")
    public static EnvStats fromMap(Map<String, Object> m) {
        EnvStats s = new EnvStats();

        s.cellsTotal = ((Number) m.getOrDefault("cells_total", 0)).intValue();
        s.cellsLimit = ((Number) m.getOrDefault("cells_limit", 0)).intValue();
        s.uniqueCells = ((Number) m.getOrDefault("unique_cells", 0)).intValue();

        s.avgEnergy = ((Number) m.getOrDefault("avg_energy", 0.0)).doubleValue();
        s.avgHealth = ((Number) m.getOrDefault("avg_health", 0.0)).doubleValue();
        s.avgAge = ((Number) m.getOrDefault("avg_age", 0.0)).doubleValue();
        s.avgGenes = ((Number) m.getOrDefault("avg_genes", 0.0)).doubleValue();
        s.avgActiveGenes = ((Number) m.getOrDefault("avg_active_genes", 0.0)).doubleValue();

        s.topCells = (List<Map<String, Object>>) m.getOrDefault("top_cells", new ArrayList<>());
        s.topCellsBySpeciesDuration = (List<Map<String, Object>>) m.getOrDefault("top_cells_by_species_duration", new ArrayList<>());

        s.totalUniqueSubstances = ((Number) m.getOrDefault("total_unique_substances", 0)).intValue();

        Object t1 = m.getOrDefault("substances_by_type", new HashMap<>());
        s.totalSubstancesByType = (Map<String, Integer>) t1;

        Object t2 = m.getOrDefault("substances_concentration_by_type", new HashMap<>());
        s.totalSubstancesConcentrationByType = (Map<String, Double>) t2;

        return s;
    }

    @Override
    public String toString() {
        return "EnvStats{" +
                "cells=" + cellsTotal +
                ", E=" + avgEnergy +
                ", H=" + avgHealth +
                ", age=" + avgAge +
                ", genes=" + avgGenes +
                ", avgActiveGenes=" + avgActiveGenes +
                ", topCells=" + topCells +
                ", topCellsBySpeciesDuration=" + topCellsBySpeciesDuration +
                ", uniqueCells=" + uniqueCells +
                ", totalUniqueSubstances=" + totalUniqueSubstances +
                ", substancesByType=" + totalSubstancesByType +
                ", substancesConcentrationByType=" + totalSubstancesConcentrationByType +
                '}';
    }

    // ------------------------------------------------------------
    // GETTERS (optional)
    // ------------------------------------------------------------
    public int getCellsTotal() { return cellsTotal; }
    public int getCellsLimit() { return cellsLimit; }
    public int getUniqueCells() { return uniqueCells; }
    public double getAvgEnergy() { return avgEnergy; }
    public double getAvgHealth() { return avgHealth; }
    public double getAvgAge() { return avgAge; }
    public double getAvgGenes() { return avgGenes; }
    public double getAvgActiveGenes() { return avgActiveGenes; }
    public List<Map<String, Object>> getTopCells() { return topCells; }
    public List<Map<String, Object>> getTopCellsBySpeciesDuration() { return topCellsBySpeciesDuration; }
    public int getTotalUniqueSubstances() { return totalUniqueSubstances; }
    public Map<String, Integer> getTotalSubstancesByType() { return totalSubstancesByType; }
    public Map<String, Double> getTotalSubstancesConcentrationByType() { return totalSubstancesConcentrationByType; }
}
