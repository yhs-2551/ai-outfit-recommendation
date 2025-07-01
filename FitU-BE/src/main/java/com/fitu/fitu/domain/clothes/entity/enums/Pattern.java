package com.fitu.fitu.domain.clothes.entity.enums;

import java.util.Arrays;

import com.fasterxml.jackson.annotation.JsonCreator;

public enum Pattern {
    ANIMAL, // 동물
    ARTIFACT, // 아티팩트
    CHECK, // 체크
    DOT, // 도트
    ETC, // 기타
    ETCNATURE, // 자연
    GEOMETRIC, // 기하학
    PLANTS, // 식물
    STRIPE, // 줄무늬
    SYMBOL, // 심볼
    MANUAL_SELECTION; // 매핑되는 값이 없을 때 수동 선택을 위한 기본값

    @JsonCreator
    public static Pattern fromJson(final String jsonValue) {
        return Arrays.stream(Pattern.values())
                .filter(pt -> pt.name().equalsIgnoreCase(jsonValue))
                .findFirst()
                .orElse(MANUAL_SELECTION);
    }
}
