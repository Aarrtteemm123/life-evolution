package com.life.evolution.utils;

import com.life.evolution.config.Config;
import com.life.evolution.model.*;

import java.util.*;

public class RenderStateBuilder {

    public static Map<String, Object> buildState(World world) {

        Environment env = world.getEnv();

        List<Map<String, Object>> substances = new ArrayList<>();

        for (var entry : env.getGrid().getGrid().entrySet()) {
            var pos = entry.getKey();
            var list = entry.getValue();

            for (Substance s : list) {
                if (s.getConcentration() <= 0) continue;

                substances.add(Map.of(
                        "x", pos.x(),
                        "y", pos.y(),
                        "type", s.getType(),
                        "concentration", s.getConcentration()
                ));
            }
        }

        List<Map<String, Object>> cells = new ArrayList<>();
        for (Cell c : env.getCells()) {
            cells.add(Map.of(
                    "position", List.of(c.getX(), c.getY()),
                    "color_hex", c.getColorHex()
            ));
        }

        return Map.of(
                "tick", world.getTick(),
                "tick_time_ms", world.getTickTimeMs(),
                "cell_radius", Config.CELL_RADIUS,
                "environment", Map.of(
                        "grid", Map.of(
                                "width", env.getGrid().getWidth(),
                                "height", env.getGrid().getHeight(),
                                "substances", substances
                        ),
                        "cells", cells,
                        "env_stats", env.getEnvStats().toMap()
                )
        );
    }
}
