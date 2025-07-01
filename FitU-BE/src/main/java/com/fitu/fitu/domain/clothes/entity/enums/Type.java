package com.fitu.fitu.domain.clothes.entity.enums;

import java.util.Arrays;

import com.fasterxml.jackson.annotation.JsonCreator;

public enum Type {
    TOP, // 상의
    BOTTOM, // 하의
    ONEPIECE, // 원피스
    MANUAL_SELECTION; // 매핑되는 값이 없을 때 수동 선택을 위한 기본값

    @JsonCreator
    public static Type fromJson(final String jsonValue) {
        return Arrays.stream(Type.values())
                .filter(type -> type.name().equalsIgnoreCase(jsonValue))
                .findFirst()
                .orElse(MANUAL_SELECTION);
    }
}
