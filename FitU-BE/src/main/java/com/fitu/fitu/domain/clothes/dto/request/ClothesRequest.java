package com.fitu.fitu.domain.clothes.dto.request;

import org.springframework.web.multipart.MultipartFile;

import com.fitu.fitu.domain.clothes.entity.enums.Category;
import com.fitu.fitu.domain.clothes.entity.enums.Color;
import com.fitu.fitu.domain.clothes.entity.enums.Pattern;
import com.fitu.fitu.domain.clothes.entity.enums.Type;

public record ClothesRequest(
        MultipartFile clothesImageFile, // ai 분석에 실패했을 때 파일 저장
        String clothesImageUrl, // ai 분석 성공 시 
        Category category,
        Type type,
        Pattern pattern,
        Color color
) {
        
}
