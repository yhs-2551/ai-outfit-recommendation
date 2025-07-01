package com.fitu.fitu.domain.recommendation.dto.response;

import com.fitu.fitu.domain.recommendation.entity.AiRecommendation;
import com.fitu.fitu.domain.recommendation.entity.Content;

import java.util.List;

public record AiRecommendationResponse(
        String summary,
        String weather,
        List<RecommendationContent> contents
) {

    public record RecommendationContent(
            String clothesCombination,
            String description,
            String imageUrl,
            List<String> clothesImageUrls
    ) {

        public static RecommendationContent of(final Content content, final List<String> clothesImageUrls) {
            return new RecommendationContent(content.getClothesCombination(), content.getDescription(), content.getImageUrl(), clothesImageUrls);
        }
    }

    public static AiRecommendationResponse of(final AiRecommendation aiRecommendation, final List<List<String>> clothesImageUrls) {
        return new AiRecommendationResponse(aiRecommendation.getSummary(),
             aiRecommendation.getWeather(),
             List.of(
                     RecommendationContent.of(aiRecommendation.getContent1(), clothesImageUrls.getFirst()),
                     RecommendationContent.of(aiRecommendation.getContent2(), clothesImageUrls.get(1)),
                     RecommendationContent.of(aiRecommendation.getContent3(), clothesImageUrls.getLast())
             )
        );
    }
}
