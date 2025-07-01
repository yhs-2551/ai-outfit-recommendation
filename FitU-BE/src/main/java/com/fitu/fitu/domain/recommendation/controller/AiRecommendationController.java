package com.fitu.fitu.domain.recommendation.controller;

import com.fitu.fitu.domain.recommendation.dto.request.RecommendOutfitRequest;
import com.fitu.fitu.domain.recommendation.dto.response.AiRecommendationResponse;
import com.fitu.fitu.domain.recommendation.entity.AiRecommendation;
import com.fitu.fitu.domain.recommendation.service.AiRecommendationService;
import jakarta.validation.Valid;
import lombok.RequiredArgsConstructor;
import org.springframework.web.bind.annotation.*;

@RequiredArgsConstructor
@RequestMapping("/recommendation")
@RestController
public class AiRecommendationController {

    private final AiRecommendationService aiRecommendationService;

    @PostMapping
    public AiRecommendationResponse recommendOutfit(@RequestHeader("Fitu-User-UUID") final String userId, @Valid @RequestBody final RecommendOutfitRequest requestDto) {
        return aiRecommendationService.recommendOutfit(userId, requestDto);
    }
}
