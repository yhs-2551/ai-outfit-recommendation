package com.fitu.fitu.domain.clothes.dto.response;

import java.time.LocalDateTime;

import com.fitu.fitu.domain.clothes.entity.enums.Category;
import com.fitu.fitu.domain.clothes.entity.enums.Color;
import com.fitu.fitu.domain.clothes.entity.enums.Pattern;
import com.fitu.fitu.domain.clothes.entity.enums.Type;

public record ClothesListResponse(
        Long clothesId,
        String clothesImageUrl,
        Type type,
        Category category,
        Pattern pattern,
        Color color,
        LocalDateTime createdAt
) {
        
}