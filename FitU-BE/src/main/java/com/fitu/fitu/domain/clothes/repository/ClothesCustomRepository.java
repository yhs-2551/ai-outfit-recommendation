package com.fitu.fitu.domain.clothes.repository;

import java.util.List;

import com.fitu.fitu.domain.clothes.entity.Clothes;
import com.fitu.fitu.domain.clothes.entity.enums.Category;
import com.fitu.fitu.domain.clothes.entity.enums.Color;
import com.fitu.fitu.domain.clothes.entity.enums.Pattern;
import com.fitu.fitu.domain.clothes.entity.enums.Type;

public interface ClothesCustomRepository {
    List<Clothes> findByUserIdWithFilters(
            String userId,
            List<Type> types,
            List<Category> categories,
            List<Pattern> patterns,
            List<Color> colors);
}
