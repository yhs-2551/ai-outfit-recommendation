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
public class ShortTermWeatherApiClient {

    private final RestTemplate restTemplate = new RestTemplate();

    private static final String BASE_URL = "http://apis.data.go.kr/1360000/VilageFcstInfoService_2.0/getVilageFcst";

    @Value("${infra.weather.api.service-key}")
    private String serviceKey;

    public ShortTermWeatherResponse getWeather(final int nx, final int ny) {
        final URI requestUrl = getRequestUrl(LocalDateTime.now(), nx, ny);

        ShortTermWeatherResponse response = null;

        try {
            response = restTemplate.getForEntity(requestUrl, ShortTermWeatherResponse.class).getBody();
        } catch (final Exception e) {
            log.error("단기예보 API 호출 중 오류가 발생했습니다. 에러 메세지: {}", e.getMessage());
            return null;
        }

        return response;
    }

    private URI getRequestUrl(final LocalDateTime now, final int nx, final int ny) {
        final BaseDateTimeGenerator.BaseDateTime baseDateTime = BaseDateTimeGenerator.generateBaseDateTimeForShortTerm(now);

        final String requestUrl = UriComponentsBuilder.fromUriString(BASE_URL)
                .queryParam("serviceKey", serviceKey)
                .queryParam("pageNo", "1")
                .queryParam("numOfRows", "1000")
                .queryParam("dataType", "JSON")
                .queryParam("base_date", baseDateTime.baseDate())
                .queryParam("base_time", baseDateTime.baseTime())
                .queryParam("nx", nx)
                .queryParam("ny", ny)
                .build()
                .toUriString();

        return URI.create(requestUrl);
    }
}
