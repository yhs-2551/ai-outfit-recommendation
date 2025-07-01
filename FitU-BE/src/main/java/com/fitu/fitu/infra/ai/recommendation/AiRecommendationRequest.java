package com.fitu.fitu.infra.ai.recommendation;

import com.fasterxml.jackson.annotation.JsonProperty;
import com.fitu.fitu.domain.recommendation.dto.request.RecommendOutfitRequest;
import com.fitu.fitu.domain.recommendation.service.WeatherService.Weather;
import lombok.Builder;
import lombok.Getter;

@Getter
public class AiRecommendationRequest {
    @JsonProperty("user_id")
    private String userId;
    private String situation;
    private String targetTime;
    private String targetPlace;
    private int highTemperature;
    private int lowTemperature;
    private int rainPercent;
    private String status;
    private boolean showClosetOnly;

    @Builder
    public AiRecommendationRequest(final String userId, final RecommendOutfitRequest recommendOutfitRequest, final Weather weather) {
        this.userId = userId;
        this.situation = recommendOutfitRequest.situation();
        this.targetTime = recommendOutfitRequest.date().toString();
        this.targetPlace = recommendOutfitRequest.place();
        this.highTemperature = weather.maxTemperature();
        this.lowTemperature = weather.minTemperature();
        this.rainPercent = weather.rainPercent();
        this.status = weather.weatherCondition();
        this.showClosetOnly = recommendOutfitRequest.useOnlyClosetItems();
    }
}
