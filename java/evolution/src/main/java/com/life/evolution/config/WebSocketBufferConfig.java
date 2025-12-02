package com.life.evolution.config;

import org.springframework.context.annotation.Bean;
import org.springframework.context.annotation.Configuration;
import org.springframework.web.socket.server.standard.ServletServerContainerFactoryBean;

@Configuration
public class WebSocketBufferConfig {

    @Bean
    public ServletServerContainerFactoryBean createWebSocketContainer() {
        ServletServerContainerFactoryBean container = new ServletServerContainerFactoryBean();

        // allow huge frames from "load" world JSON
        container.setMaxTextMessageBufferSize(100 * 1024 * 1024);     // 10 MB
        container.setMaxBinaryMessageBufferSize(100 * 1024 * 1024);   // 10 MB
        container.setAsyncSendTimeout(30_000L);                      // 30 sec
        container.setMaxSessionIdleTimeout(0L);                      // never timeout

        return container;
    }
}