package com.fitu.fitu.domain.recommendation.entity;

import jakarta.persistence.Column;
import jakarta.persistence.Embeddable;
import lombok.AccessLevel;
import lombok.Builder;
import lombok.Getter;
import lombok.NoArgsConstructor;

@Getter
@NoArgsConstructor(access = AccessLevel.PROTECTED)
@Embeddable
public class Content {

    @Column(nullable = false, columnDefinition = "LONGTEXT")
    private String clothesCombination;

    @Column(nullable = false, columnDefinition = "LONGTEXT")
    private String selectedClothes;

    @Column(nullable = false, columnDefinition = "LONGTEXT")
    private String description;

    @Column
    private String imageUrl;

    @Builder
    public Content(final String clothesCombination, final String selectedClothes, final String description, final String imageUrl) {
        this.clothesCombination = clothesCombination;
        this.selectedClothes = selectedClothes;
        this.description = description;
        this.imageUrl = imageUrl;
    }
}
