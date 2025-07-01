package com.fitu.fitu.domain.clothes.exception;

import com.fitu.fitu.global.error.ErrorCode;
import com.fitu.fitu.global.error.exception.EntityNotFoundException;

public class ClothesNotFoundException extends EntityNotFoundException {
    public ClothesNotFoundException(final Long target) {
        super(target + " Is Not Found", ErrorCode.CLOTHES_NOT_FOUND);
    }

    public ClothesNotFoundException(final ErrorCode errorCode) {
        super(errorCode.getMessage(), ErrorCode.CLOTHES_NOT_FOUND);
    }
}
