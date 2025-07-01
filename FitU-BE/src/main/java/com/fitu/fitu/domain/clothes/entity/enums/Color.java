package com.fitu.fitu.domain.clothes.entity.enums;

import com.fasterxml.jackson.annotation.JsonCreator;

public enum Color {
    LIGHT, // 밝은 계열
    DARK, // 어두운 계열
    NOT_CONSIDERED, // 고려하지 않음
    MANUAL_SELECTION; // 매핑되는 값이 없을 때 수동 선택을 위한 기본값

    @JsonCreator
    public static Color fromJson(final String koreanTone) {
        return switch (koreanTone) {
            case "LIGHT", "밝은 톤" -> LIGHT;
            case "DARK", "어두운 톤" -> DARK;
            case "NOT_CONSIDERED" -> NOT_CONSIDERED;
            default -> MANUAL_SELECTION;
        };
    }
}
