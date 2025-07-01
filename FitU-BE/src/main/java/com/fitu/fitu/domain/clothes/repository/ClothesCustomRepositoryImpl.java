package com.fitu.fitu.domain.clothes.repository;

import java.util.List;

import org.springframework.stereotype.Repository;

import com.fitu.fitu.domain.clothes.entity.Clothes;
import com.fitu.fitu.domain.clothes.entity.QClothes;
import com.fitu.fitu.domain.clothes.entity.enums.Category;
import com.fitu.fitu.domain.clothes.entity.enums.Color;
import com.fitu.fitu.domain.clothes.entity.enums.Pattern;
import com.fitu.fitu.domain.clothes.entity.enums.Type;
import com.querydsl.core.BooleanBuilder;
import com.querydsl.jpa.impl.JPAQueryFactory;

import lombok.RequiredArgsConstructor;

@RequiredArgsConstructor
@Repository
public class ClothesCustomRepositoryImpl implements ClothesCustomRepository {

    private final JPAQueryFactory queryFactory;

    @Override
    public List<Clothes> findByUserIdWithFilters(
            final String userId,
            final List<Type> types,
            final List<Category> categories,
            final List<Pattern> patterns,
            final List<Color> colors) {

        final QClothes clothes = QClothes.clothes;
        final BooleanBuilder builder = new BooleanBuilder();

        builder.and(clothes.userId.eq(userId));

        if (types != null && !types.isEmpty()) {
            builder.and(clothes.type.in(types));
        }

        if (categories != null && !categories.isEmpty()) {
            builder.and(clothes.category.in(categories));
        }

        if (patterns != null && !patterns.isEmpty()) {
            builder.and(clothes.pattern.in(patterns));
        }

        if (colors != null && !colors.isEmpty()) {
            builder.and(clothes.color.in(colors));
        }

        return queryFactory
                .selectFrom(clothes)
                .where(builder)
                .orderBy(clothes.createdAt.desc())
                .fetch();
    }
}