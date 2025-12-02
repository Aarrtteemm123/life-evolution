package com.life.evolution.component;

import com.fasterxml.jackson.databind.ObjectMapper;
import com.life.evolution.config.Config;
import com.life.evolution.model.World;
import com.life.evolution.utils.RenderStateBuilder;
import org.springframework.stereotype.Component;
import org.springframework.web.socket.*;
import org.springframework.web.socket.handler.TextWebSocketHandler;

import java.util.Map;
import java.util.concurrent.*;

@Component
public class SimulationWebSocketHandler extends TextWebSocketHandler {

    private final ObjectMapper mapper = new ObjectMapper();

    // one simulation loop per client
    private final ConcurrentHashMap<WebSocketSession, ClientState> clients = new ConcurrentHashMap<>();
    private final ScheduledExecutorService executor = Executors.newScheduledThreadPool(8);

    @Override
    public void afterConnectionEstablished(WebSocketSession session) throws Exception {

        System.out.println("🌐 Client connected");

        // Create world for this client
        World world = new World(Config.WORLD_WIDTH, Config.WORLD_HEIGHT);
        Helper.populateWorld(world);

        ClientState state = new ClientState(world);
        clients.put(session, state);

        // Send status immediately
        session.sendMessage(new TextMessage(mapper.writeValueAsString(Map.of(
                "type", "status",
                "running", true,
                "max_speed", false
        ))));

        // schedule simulation loop
        executor.scheduleAtFixedRate(() -> tickLoop(session, state),
                0, (long) (Config.FRAME_TIME * 1000), TimeUnit.MICROSECONDS);
    }

    private void tickLoop(WebSocketSession session, ClientState state) {
        if (!session.isOpen()) return;

        try {
            if (state.maxSpeed && state.simRunning) {
                state.world.update();
                return;
            }

            long start = System.nanoTime();

            if (state.simRunning) {
                state.world.update();
            }

            Map<String, Object> renderState = RenderStateBuilder.buildState(state.world);
            state.lastState = renderState;

            session.sendMessage(new TextMessage(mapper.writeValueAsString(renderState)));

            long elapsed = System.nanoTime() - start;
            long delay = (long) (Config.FRAME_TIME * 1_000_000) - elapsed;

            if (delay > 0) Thread.sleep(delay / 1_000_000);

        } catch (Exception ignored) {}
    }

    @Override
    public void handleTextMessage(WebSocketSession session, TextMessage message) throws Exception {

        ClientState state = clients.get(session);
        if (state == null) return;

        String raw = message.getPayload();

        if (raw.equals("ping")) {
            session.sendMessage(new TextMessage("pong"));
            return;
        }

        Map<String, Object> data = mapper.readValue(raw, Map.class);
        if (!"control".equals(data.get("type"))) return;

        String command = (String) data.get("command");

        switch (command) {

            case "start" -> {
                state.simRunning = true;
                sendStatus(session, state);
            }

            case "stop" -> {
                state.simRunning = false;
                sendStatus(session, state);
            }

            case "speed" -> {
                Object ms = data.get("max_speed");
                if (ms instanceof Boolean b) {
                    state.maxSpeed = b;
                }
                sendStatus(session, state);
            }

            case "save" -> {
                Map<String, Object> full = state.world.toMap();
                session.sendMessage(new TextMessage(mapper.writeValueAsString(Map.of(
                        "type", "save",
                        "filename", "world_state_tick_" + state.world.getTick() + ".json",
                        "state", full
                ))));
            }

            case "load" -> {
                Map<String, Object> saved = (Map<String, Object>) data.get("state");
                if (saved == null) {
                    sendError(session, state, "invalid_state");
                    return;
                }

                try {
                    World newWorld = World.fromMap(saved);
                    state.world = newWorld;
                    state.lastState = RenderStateBuilder.buildState(newWorld);
                    state.simRunning = true;

                    session.sendMessage(new TextMessage(mapper.writeValueAsString(Map.of(
                            "type", "status",
                            "running", true,
                            "max_speed", state.maxSpeed,
                            "loaded_tick", newWorld.getTick()
                    ))));

                    session.sendMessage(new TextMessage(mapper.writeValueAsString(state.lastState)));

                } catch (Exception e) {
                    sendError(session, state, "load_failed");
                }
            }
        }
    }

    private void sendStatus(WebSocketSession session, ClientState state) throws Exception {
        session.sendMessage(new TextMessage(mapper.writeValueAsString(Map.of(
                "type", "status",
                "running", state.simRunning,
                "max_speed", state.maxSpeed
        ))));
    }

    private void sendError(WebSocketSession session, ClientState state, String err) throws Exception {
        session.sendMessage(new TextMessage(mapper.writeValueAsString(Map.of(
                "type", "status",
                "running", state.simRunning,
                "max_speed", state.maxSpeed,
                "error", err
        ))));
    }

    @Override
    public void afterConnectionClosed(WebSocketSession session, CloseStatus status) {
        System.out.println("❌ Client disconnected");
        clients.remove(session);
    }

    private static class ClientState {
        World world;
        boolean simRunning = true;
        boolean maxSpeed = false;
        Map<String, Object> lastState;

        ClientState(World world) {
            this.world = world;
        }
    }
}
