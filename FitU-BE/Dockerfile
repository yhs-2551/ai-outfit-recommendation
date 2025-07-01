FROM gradle:jdk21-jammy as builder

WORKDIR /build

COPY build.gradle settings.gradle ./

COPY gradle ./gradle
COPY gradlew ./           
COPY gradlew.bat ./        

RUN chmod +x ./gradlew

RUN ./gradlew dependencies --no-daemon

COPY src ./src

RUN ./gradlew build -x test --no-daemon

FROM openjdk:21-jdk-slim

WORKDIR /app

COPY --from=builder /build/build/libs/*.jar app.jar

EXPOSE 8080

ENTRYPOINT ["java", "-jar", "app.jar"]