package com.fitu.fitu.domain.recommendation.exception;

import com.fitu.fitu.global.error.ErrorCode;
import com.fitu.fitu.global.error.exception.SystemException;

public class AiRecommendationServerException extends SystemException {
    public AiRecommendationServerException(final ErrorCode errorCode) {
        super(errorCode);
    }
}
