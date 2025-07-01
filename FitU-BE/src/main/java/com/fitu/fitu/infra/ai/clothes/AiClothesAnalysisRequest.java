package com.fitu.fitu.infra.ai.clothes;

import com.fasterxml.jackson.annotation.JsonProperty;

public record AiClothesAnalysisRequest(
        @JsonProperty("s3_url") String imageUrl
) {

}
