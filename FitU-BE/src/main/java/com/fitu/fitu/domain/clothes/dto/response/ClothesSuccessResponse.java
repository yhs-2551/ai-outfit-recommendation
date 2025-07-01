package com.fitu.fitu.domain.clothes.dto.response;

import lombok.Getter;

@Getter
public class ClothesSuccessResponse<T> {
    private final boolean success = true;
    private final String message;
    private final T data;

    private ClothesSuccessResponse(final String message, final T data) {
        this.message = message;
        this.data = data;
    }

    public static <T> ClothesSuccessResponse<T> of(final String message, final T data) {
        return new ClothesSuccessResponse<>(message, data);
    }

    public static ClothesSuccessResponse<Void> of(final String message) {
        return new ClothesSuccessResponse<>(message, null);
    }
}
