package com.fitu.fitu.domain.clothes.dto.response;

import com.fitu.fitu.domain.clothes.entity.enums.Category;
import com.fitu.fitu.domain.clothes.entity.enums.Color;
import com.fitu.fitu.domain.clothes.entity.enums.Pattern;
import com.fitu.fitu.domain.clothes.entity.enums.Type;

public record ClothesUpdateResponse(
        Long clothesId,
        String clothesImageUrl,
        Type type,
        Category category,
        Pattern pattern,
        Color color,
        String message,
        boolean success
) {

    public static ClothesUpdateResponse success(final Long clothesId, final String clothesImageUrl,
            final Type type, final Category category, final Pattern pattern, final Color color,
            final String message) {
        return new ClothesUpdateResponse(clothesId, clothesImageUrl, type, category, pattern, color, message, true);
    }

    public static ClothesUpdateResponse failure(final String message) {
        return new ClothesUpdateResponse(null, null, null, null, null, null, message, false);
    }
}
