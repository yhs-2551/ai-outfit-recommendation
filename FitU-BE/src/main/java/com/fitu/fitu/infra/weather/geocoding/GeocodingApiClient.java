package com.fitu.fitu.infra.weather.geocoding;

import lombok.extern.slf4j.Slf4j;
import org.springframework.beans.factory.annotation.Value;
import org.springframework.http.HttpEntity;
import org.springframework.http.HttpHeaders;
import org.springframework.http.HttpMethod;
import org.springframework.stereotype.Component;
import org.springframework.web.client.RestTemplate;
import org.springframework.web.util.UriComponentsBuilder;

@Slf4j
@Component
public class GeocodingApiClient {

    private final RestTemplate restTemplate = new RestTemplate();

    private static final String BASE_URL = "https://dapi.kakao.com/v2/local/search/keyword";

    @Value("${infra.geocoding.api.service-key}")
    private String serviceKey;

    public GeocodingResponse getCoordinateAndAddress(final String query) {
        final HttpEntity<Void> headers = getHttpHeaders();
        final String requestUrl = getRequestUrl(query);

        GeocodingResponse response = null;

        try {
            response = restTemplate.exchange(requestUrl, HttpMethod.GET, headers, GeocodingResponse.class).getBody();
        } catch (final Exception e) {
            log.error("Geocoding API 호출 중 오류가 발생했습니다. 에러 메세지: {}", e.getMessage());
            return null;
        }

        return response;
    }

    private HttpEntity<Void> getHttpHeaders() {
        final HttpHeaders headers = new HttpHeaders();

        headers.set("Authorization", "KakaoAK " + serviceKey);

        return new HttpEntity<>(headers);
    }

    private String getRequestUrl(final String query) {
        return UriComponentsBuilder.fromUriString(BASE_URL)
                .queryParam("query", query)
                .build()
                .toUriString();
    }
}
