package com.fitu.fitu.infra.ai.clothes;

import com.fitu.fitu.domain.clothes.entity.enums.Category;
import com.fitu.fitu.domain.clothes.entity.enums.Color;
import com.fitu.fitu.domain.clothes.entity.enums.Pattern;
import com.fitu.fitu.domain.clothes.entity.enums.Type;

public record AiAnalysisResponse(
        Type type,
        Category category,
        Pattern pattern,
        Color color,
        String imageUrl
) {
 
    public static AiAnalysisResponse success(final Type type, final Category category, final Pattern pattern,
            final Color color,
            final String imageUrl) {
        return new AiAnalysisResponse(type, category, pattern, color, imageUrl);
    }

}
