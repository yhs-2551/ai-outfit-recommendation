package com.fitu.fitu.global.error.exception;

import com.fitu.fitu.global.error.ErrorCode;

public class SystemException extends RuntimeException {
    private final ErrorCode errorCode;

    public SystemException(final ErrorCode errorCode) {
        super(errorCode.getMessage());
        this.errorCode = errorCode;
    }

    public SystemException(final String message, final ErrorCode errorCode) {
        super(message);
        this.errorCode = errorCode;
    }
}
