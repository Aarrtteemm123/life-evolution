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

        // Queue initial status (never send directly!)
        state.outgoing.offer(new TextMessage(
                mapper.writeValueAsString(Map.of(
                        "type", "status",
                        "running", true,
                        "max_speed", false
                ))
        ));

        // schedule simulation loop
        executor.scheduleAtFixedRate(
                () -> tickLoop(session, state),
                0,
                (long) (Config.FRAME_TIME * 1_000_000_000L),   // FRAME_TIME seconds → nanoseconds
                TimeUnit.NANOSECONDS
        );
    }

    private void tickLoop(WebSocketSession session, ClientState state) {
        if (!session.isOpen()) return;

        try {
            long start = System.nanoTime();

            // MAX SPEED MODE (update only, no rendering)
            if (state.simRunning && state.maxSpeed) {
                state.world.update();
            } else {

                // Normal mode
                if (state.simRunning) {
                    state.world.update();
                }

                Map<String, Object> renderState = RenderStateBuilder.buildState(state.world);
                state.lastState = renderState;

                // Queue frame for sending
                state.outgoing.offer(new TextMessage(
                        mapper.writeValueAsString(renderState)
                ));
            }

            // SEND QUEUED MESSAGES (ONLY THIS THREAD!)
            TextMessage msg;
            while ((msg = state.outgoing.poll()) != null) {
                if (session.isOpen()) {
                    session.sendMessage(msg);
                }
            }

            if (!state.maxSpeed) {
                long elapsed = System.nanoTime() - start;
                long target = (long) (Config.FRAME_TIME * 1_000_000_000L);
                long remaining = target - elapsed;

                if (remaining > 0) {
                    Thread.sleep(remaining / 1_000_000, (int) (remaining % 1_000_000));
                }
            }
        } catch (Exception ignored) {}
    }

    @Override
    public void handleTextMessage(WebSocketSession session, TextMessage message) throws Exception {

        ClientState state = clients.get(session);
        if (state == null) return;

        String raw = message.getPayload();

        // Ping/pong
        if (raw.equals("ping")) {
            state.outgoing.offer(new TextMessage("pong"));
            return;
        }

        Map<String, Object> data = mapper.readValue(raw, Map.class);
        if (!"control".equals(data.get("type"))) return;

        String command = (String) data.get("command");

        switch (command) {

            case "start" -> {
                state.simRunning = true;
                queueStatus(state);
            }

            case "stop" -> {
                state.simRunning = false;
                queueStatus(state);
            }

            case "speed" -> {
                Object ms = data.get("max_speed");
                if (ms instanceof Boolean b) {
                    state.maxSpeed = b;
                }
                queueStatus(state);
            }

            case "save" -> {
                Map<String, Object> full = state.world.toMap();

                // send save response through queue
                state.outgoing.offer(new TextMessage(
                        mapper.writeValueAsString(Map.of(
                                "type", "save",
                                "filename", "world_state_tick_" + state.world.getTick() + ".json",
                                "state", full
                        ))
                ));
            }

            case "load" -> {
                Map<String, Object> saved = (Map<String, Object>) data.get("state");
                if (saved == null) {
                    queueError(state, "invalid_state");
                    return;
                }

                try {
                    World newWorld = World.fromMap(saved);
                    state.world = newWorld;

                    // Rebuild render state
                    state.lastState = RenderStateBuilder.buildState(newWorld);

                    // Continue simulation automatically
                    state.simRunning = true;

                    // Clear old queue frames
                    state.outgoing.clear();

                    // Status after loading
                    state.outgoing.offer(new TextMessage(
                            mapper.writeValueAsString(Map.of(
                                    "type", "status",
                                    "running", true,
                                    "max_speed", state.maxSpeed,
                                    "loaded_tick", newWorld.getTick()
                            ))
                    ));

                    // Send first world frame
                    state.outgoing.offer(new TextMessage(
                            mapper.writeValueAsString(state.lastState)
                    ));

                } catch (Exception e) {
                    queueError(state, "load_failed");
                }
            }
        }
    }

    private void queueStatus(ClientState state) {
        try {
            state.outgoing.offer(new TextMessage(
                    mapper.writeValueAsString(Map.of(
                            "type", "status",
                            "running", state.simRunning,
                            "max_speed", state.maxSpeed
                    ))
            ));
        } catch (Exception ignored) {}
    }

    private void queueError(ClientState state, String err) {
        try {
            state.outgoing.offer(new TextMessage(
                    mapper.writeValueAsString(Map.of(
                            "type", "status",
                            "running", state.simRunning,
                            "max_speed", state.maxSpeed,
                            "error", err
                    ))
            ));
        } catch (Exception ignored) {}
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

        // Queue of outgoing messages — only tickLoop sends!
        final BlockingQueue<TextMessage> outgoing = new LinkedBlockingQueue<>();

        ClientState(World world) {
            this.world = world;
        }
    }
}
