package com.life.evolution;

import org.springframework.boot.SpringApplication;
import org.springframework.boot.autoconfigure.SpringBootApplication;
import org.springframework.web.socket.config.annotation.EnableWebSocket;

@SpringBootApplication
@EnableWebSocket
public class EvolutionApplication {

	public static void main(String[] args) {
		SpringApplication.run(EvolutionApplication.class, args);
	}
}
