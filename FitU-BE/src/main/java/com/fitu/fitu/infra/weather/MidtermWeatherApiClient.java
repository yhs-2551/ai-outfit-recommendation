package com.fitu.fitu.infra.weather;

import com.fitu.fitu.infra.weather.util.BaseDateTimeGenerator;
import lombok.extern.slf4j.Slf4j;
import org.springframework.beans.factory.annotation.Value;
import org.springframework.stereotype.Component;
import org.springframework.web.client.RestTemplate;
import org.springframework.web.util.UriComponentsBuilder;

import java.net.URI;
import java.time.LocalDateTime;

@Slf4j
@Component
public class MidtermWeatherApiClient {

    private final RestTemplate restTemplate = new RestTemplate();

    private static final String WEATHER_CONDITION_BASE_URL = "http://apis.data.go.kr/1360000/MidFcstInfoService/getMidLandFcst";
    private static final String TEMPERATURE_BASE_URL = "http://apis.data.go.kr/1360000/MidFcstInfoService/getMidTa";

    @Value("${infra.weather.api.service-key}")
    private String serviceKey;

    public MidtermWeatherConditionResponse getWeatherCondition(final String regId) {
        final URI requestUrl = getRequestUrl(WEATHER_CONDITION_BASE_URL, regId, LocalDateTime.now());

        MidtermWeatherConditionResponse response = null;

        try {
            response = restTemplate.getForEntity(requestUrl, MidtermWeatherConditionResponse.class).getBody();
        } catch (final Exception e) {
            log.error("중기육상예보 API 호출 중 오류가 발생했습니다. 에러 메세지: {}", e.getMessage());
            return null;
        }
        return response;
    }

    public MidtermTemperatureResponse getTemperature(final String regId) {
        final URI requestUrl = getRequestUrl(TEMPERATURE_BASE_URL, regId, LocalDateTime.now());

        MidtermTemperatureResponse response = null;

        try {
            response = restTemplate.getForEntity(requestUrl, MidtermTemperatureResponse.class).getBody();
        } catch (final Exception e) {
            log.error("중기기온예보 API 호출 중 오류가 발생했습니다. 에러 메세지: {}", e.getMessage());
            return null;
        }

        return response;
    }

    private URI getRequestUrl(final String baseUrl, final String regId, final LocalDateTime now) {
        final String baseDateTime = BaseDateTimeGenerator.generateBaseDateTimeForMidTerm(now);

        final String requestUrl = UriComponentsBuilder.fromUriString(baseUrl)
                .queryParam("ServiceKey", serviceKey)
                .queryParam("pageNo", "1")
                .queryParam("numOfRows", "10")
                .queryParam("dataType", "JSON")
                .queryParam("regId", regId)
                .queryParam("tmFc", baseDateTime)
                .build()
                .toUriString();

        return URI.create(requestUrl);
    }
}
