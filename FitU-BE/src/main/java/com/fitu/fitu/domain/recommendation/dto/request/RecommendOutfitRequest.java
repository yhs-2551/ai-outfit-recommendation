package com.fitu.fitu.domain.recommendation.dto.request;

import com.fitu.fitu.global.common.annotation.ValidDateRange;
import jakarta.validation.constraints.NotBlank;
import jakarta.validation.constraints.NotNull;

import java.time.LocalDate;

public record RecommendOutfitRequest(
        @NotBlank
        String situation,
        @NotNull
        @ValidDateRange(range = 10)
        LocalDate date,
        @NotBlank
        String place,
        @NotNull
        Boolean useOnlyClosetItems
) {
}
