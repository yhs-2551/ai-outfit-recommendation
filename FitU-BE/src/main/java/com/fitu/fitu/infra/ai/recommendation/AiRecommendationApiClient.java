package com.fitu.fitu.infra.ai.recommendation;

import com.fitu.fitu.domain.recommendation.dto.request.RecommendOutfitRequest;
import com.fitu.fitu.domain.recommendation.exception.AiRecommendationServerException;
import com.fitu.fitu.domain.recommendation.service.WeatherService.Weather;
import com.fitu.fitu.global.error.ErrorCode;
import org.springframework.beans.factory.annotation.Value;
import org.springframework.http.HttpEntity;
import org.springframework.http.HttpMethod;
import org.springframework.stereotype.Component;
import org.springframework.web.client.RestTemplate;

@Component
public class AiRecommendationApiClient {

    private final RestTemplate restTemplate = new RestTemplate();

    @Value("${infra.ai.api.recommendation.base-url}")
    private String BASE_URL;

    public AiRecommendationApiResponse getAiRecommendation(final String userId, final RecommendOutfitRequest recommendOutfitRequest, final Weather weather) {
        final AiRecommendationRequest requestBody = getRequestBody(userId, recommendOutfitRequest, weather);
        final HttpEntity<AiRecommendationRequest> requestHttpEntity = new HttpEntity<>(requestBody);

        try {
            return restTemplate.exchange(BASE_URL, HttpMethod.POST, requestHttpEntity, AiRecommendationApiResponse.class).getBody();
        } catch (Exception e) {
            throw new AiRecommendationServerException(ErrorCode.AI_RECOMMENDATION_SERVER_ERROR);
        }
    }

    private AiRecommendationRequest getRequestBody(final String userId, final RecommendOutfitRequest recommendOutfitRequest, final Weather weather) {
        return AiRecommendationRequest.builder()
                .userId(userId)
                .recommendOutfitRequest(recommendOutfitRequest)
                .weather(weather)
                .build();
    }
}
