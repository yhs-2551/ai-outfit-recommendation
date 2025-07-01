package com.fitu.fitu.infra.ai.bodyimage;

import lombok.RequiredArgsConstructor;
import org.springframework.beans.factory.annotation.Value;
import org.springframework.stereotype.Component;
import org.springframework.web.client.RestClientException;
import org.springframework.web.client.RestTemplate;

@RequiredArgsConstructor
@Component
public class AiBodyImageClient {

    @Value("${infra.ai.api.body-image}")
    private String baseUrl;

    private final RestTemplate restTemplate;

    public AiBodyImageResponse analyzeBodyImage(final String s3Url) {
        final String url = baseUrl + "/user/profile/image-analysis";

        final AiBodyImageRequest request = new AiBodyImageRequest(s3Url);

        try {
            return restTemplate.postForObject(url, request, AiBodyImageResponse.class);
        } catch (RestClientException e) {
            throw new RuntimeException("Failed to analyze body image: " + e.getMessage());
        }
    }
}