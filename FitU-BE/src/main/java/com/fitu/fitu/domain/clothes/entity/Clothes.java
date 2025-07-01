package com.fitu.fitu.domain.clothes.entity;

import com.fitu.fitu.domain.clothes.entity.enums.Category;
import com.fitu.fitu.domain.clothes.entity.enums.Color;
import com.fitu.fitu.domain.clothes.entity.enums.Pattern;
import com.fitu.fitu.domain.clothes.entity.enums.Type;
import com.fitu.fitu.global.common.domain.BaseEntity;
import jakarta.persistence.*;
import lombok.AccessLevel;
import lombok.Builder;
import lombok.Getter;
import lombok.NoArgsConstructor;

@Getter
@NoArgsConstructor(access = AccessLevel.PROTECTED)
@Entity
public class Clothes extends BaseEntity {

    @Id
    @GeneratedValue(strategy = GenerationType.IDENTITY)
    private Long id;

    @Column(nullable = false)
    private String userId;

    @Column(nullable = false)
    private String imageUrl;

    @Enumerated(EnumType.STRING)
    @Column(nullable = false)
    private Type type;

    @Enumerated(EnumType.STRING)
    @Column(nullable = false)
    private Category category;

    @Enumerated(EnumType.STRING)
    @Column(nullable = false)
    private Pattern pattern;

    @Enumerated(EnumType.STRING)
    @Column(nullable = false)
    private Color color;

    @Builder
    public Clothes(final String userId, final String imageUrl,
            final Type type, final Category category, final Pattern pattern, final Color color) {
        this.userId = userId;
        this.imageUrl = imageUrl;
        this.type = type;
        this.category = category;
        this.pattern = pattern;
        this.color = color;
    }

    public void updateClothes(final String newImageUrl, final Type newType, final Category newCategory, final Pattern newPattern,
            final Color newColor) {
        this.imageUrl = newImageUrl;
        this.type = newType;
        this.category = newCategory;
        this.pattern = newPattern;
        this.color = newColor;
    }
}
