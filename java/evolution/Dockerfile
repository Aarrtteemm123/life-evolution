FROM maven:3.9.6-eclipse-temurin-17 AS builder
WORKDIR /app

COPY pom.xml .
COPY src ./src

RUN mvn -q -e -DskipTests package

FROM eclipse-temurin:17-jre
WORKDIR /app

# --- create directory for saves (important for volume mounting) ---
RUN mkdir -p /app/saves

# --- optionally declare volume ---
VOLUME ["/app/saves"]

COPY --from=builder /app/target/*.jar app.jar

EXPOSE 8080
ENTRYPOINT ["java", "-jar", "app.jar"]
