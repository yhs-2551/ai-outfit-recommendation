package com.fitu.fitu.domain.recommendation.exception;

import com.fitu.fitu.global.error.ErrorCode;
import com.fitu.fitu.global.error.exception.BusinessException;

public class NoRecommendationException extends BusinessException {
    public NoRecommendationException(final ErrorCode errorCode) {
        super(errorCode);
    }
}
