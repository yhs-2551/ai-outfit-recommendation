package com.fitu.fitu.domain.user.dto.response;

import com.fasterxml.jackson.annotation.JsonInclude;

import java.util.List;

public record BodyImageAnalysisResponse(
        String s3Url,
        @JsonInclude(JsonInclude.Include.NON_EMPTY)
        List<String> warnings
) {
}