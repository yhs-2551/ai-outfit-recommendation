package com.fitu.fitu.domain.clothes.dto.request;

import org.springframework.web.multipart.MultipartFile;

import com.fitu.fitu.domain.clothes.entity.enums.Category;
import com.fitu.fitu.domain.clothes.entity.enums.Color;
import com.fitu.fitu.domain.clothes.entity.enums.Pattern;
import com.fitu.fitu.domain.clothes.entity.enums.Type;

public record ClothesUpdateRequest(
        String prevImage,
        MultipartFile newImage, 
        Type type,  
        Category category,  
        Pattern pattern,  
        Color color  
) {

}
