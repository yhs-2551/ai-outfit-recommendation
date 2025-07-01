package com.fitu.fitu.domain.user.exception;

import com.fitu.fitu.global.error.ErrorCode;
import com.fitu.fitu.global.error.exception.EntityNotFoundException;

public class UserNotFoundException extends EntityNotFoundException {
    public UserNotFoundException(final String target) {
        super(target + " Is Not Found", ErrorCode.USER_NOT_FOUND);
    }

    public UserNotFoundException(final ErrorCode errorCode) {
        super(errorCode.getMessage(), errorCode);
    }
}
