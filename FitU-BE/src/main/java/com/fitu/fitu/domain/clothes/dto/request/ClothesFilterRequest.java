package com.fitu.fitu.domain.clothes.dto.request;

import java.util.List;

import com.fitu.fitu.domain.clothes.entity.enums.Category;
import com.fitu.fitu.domain.clothes.entity.enums.Color;
import com.fitu.fitu.domain.clothes.entity.enums.Pattern;
import com.fitu.fitu.domain.clothes.entity.enums.Type;

public record ClothesFilterRequest(
        List<Type> types, // null or 빈 리스트 = 전체 타입. 아래도 동일
        List<Category> categories, 
        List<Pattern> patterns,  
        List<Color> colors 
) {
    /**
     * 모든 필터가 비어있는지 확인 (기본값 = 전체 조회)
     */
    public boolean isShowAll() {
        return (types == null || types.isEmpty()) &&
                (categories == null || categories.isEmpty()) &&
                (patterns == null || patterns.isEmpty()) &&
                (colors == null || colors.isEmpty());
    }
}