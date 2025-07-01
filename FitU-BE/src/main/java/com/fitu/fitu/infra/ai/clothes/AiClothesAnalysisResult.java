package com.fitu.fitu.infra.ai.clothes;

import com.fasterxml.jackson.annotation.JsonProperty;
import com.fitu.fitu.domain.clothes.entity.enums.Category;
import com.fitu.fitu.domain.clothes.entity.enums.Color;
import com.fitu.fitu.domain.clothes.entity.enums.Pattern;
import com.fitu.fitu.domain.clothes.entity.enums.Type;

public record AiClothesAnalysisResult(
        boolean isValidClothes,
        @JsonProperty("category") Type type,
        @JsonProperty("subcategory") Category category,
        Pattern pattern,
        @JsonProperty("tone") Color color,
        @JsonProperty("segmented_image_path") String segmentedImagePath,
        String errorMessage
) {

    public static AiClothesAnalysisResult success(final Type type, final Category category, final Pattern pattern,
            final Color color,
            final String segmentedImagePath) {
        return new AiClothesAnalysisResult(true, type, category, pattern, color, segmentedImagePath, null);
    }

    public static AiClothesAnalysisResult failure(final String errorMessage) {
        return new AiClothesAnalysisResult(false, null, null, null, null, null, errorMessage);
    }
}
