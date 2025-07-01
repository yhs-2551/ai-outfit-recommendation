package com.fitu.fitu.global.error.exception;

import com.fitu.fitu.global.error.ErrorCode;

public class EntityNotFoundException extends BusinessException {

    public EntityNotFoundException(final String message) {
        super(message, ErrorCode.ENTITY_NOT_FOUND);
    }

    public EntityNotFoundException(final ErrorCode errorCode) {
        super(errorCode.getMessage(), errorCode);
    }

    public EntityNotFoundException(final String message, final ErrorCode errorCode) {
        super(message, errorCode);
    }
}
