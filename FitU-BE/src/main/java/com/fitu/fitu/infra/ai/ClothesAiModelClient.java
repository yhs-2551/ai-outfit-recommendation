package com.fitu.fitu.infra.ai;

import org.springframework.beans.factory.annotation.Qualifier;
import org.springframework.beans.factory.annotation.Value;
import org.springframework.http.HttpEntity;
import org.springframework.http.HttpHeaders;
import org.springframework.http.MediaType;
import org.springframework.http.ResponseEntity;
import org.springframework.stereotype.Component;
import org.springframework.web.client.RestClientException;
import org.springframework.web.client.RestTemplate;

import com.fasterxml.jackson.core.JsonProcessingException;
import com.fasterxml.jackson.databind.ObjectMapper;
import com.fitu.fitu.global.error.ErrorCode;
import com.fitu.fitu.global.error.exception.BusinessException;
import com.fitu.fitu.infra.ai.clothes.AiClothesAnalysisRequest;
import com.fitu.fitu.infra.ai.clothes.AiClothesAnalysisResult;
import com.fitu.fitu.infra.ai.clothes.AiClothesAnalysisWrapper;

import lombok.RequiredArgsConstructor;
import lombok.extern.slf4j.Slf4j;

@Slf4j
@RequiredArgsConstructor
@Component
public class ClothesAiModelClient {

    private final RestTemplate restTemplate;

    private final ObjectMapper objectMapper;

    @Value("${ai.model.base-url}")
    private String aiModelBaseUrl;

    public AiClothesAnalysisResult analyzeClothes(final String clothesImageUrl) {
        try {
            final AiClothesAnalysisRequest aiClothesAnalysisRequest = new AiClothesAnalysisRequest(clothesImageUrl);

            final String jsonRequestBody = objectMapper.writeValueAsString(aiClothesAnalysisRequest);

            final HttpHeaders headers = new HttpHeaders();
            headers.setContentType(MediaType.APPLICATION_JSON);

            final HttpEntity<String> requestEntity = new HttpEntity<>(jsonRequestBody, headers);

            final ResponseEntity<AiClothesAnalysisWrapper> responseEntity = restTemplate.postForEntity(
                    aiModelBaseUrl + "/clothes/image-analysis",
                    requestEntity,
                    AiClothesAnalysisWrapper.class);

            final AiClothesAnalysisWrapper aiResponse = responseEntity.getBody();

            if (aiResponse == null || aiResponse.analyses() == null || aiResponse.analyses().isEmpty()) {
                return AiClothesAnalysisResult.failure("AI 의류 분석 결과가 없음.");
            }

            if (aiResponse.status().equals("single_cloth")) {
                AiClothesAnalysisResult singleClothesResponse = aiResponse.analyses().get(0);
                return AiClothesAnalysisResult.success(singleClothesResponse.type(),
                        singleClothesResponse.category(), singleClothesResponse.pattern(),
                        singleClothesResponse.color(), singleClothesResponse.segmentedImagePath());
            } else {
                return AiClothesAnalysisResult.failure(aiResponse.status());
            }

        } catch (JsonProcessingException e) {
            log.error("AI 의류 분석 요청 본문 JSON 변환 실패 - 오류: {}", e.getMessage(), e);
            throw new BusinessException(ErrorCode.CLOTHES_AI_ANALYSIS_FAILED);
        } catch (RestClientException e) {
            log.error("AI 의류 분석 API 호출 실패 - 오류: {}", e.getMessage(), e);
            throw new BusinessException(ErrorCode.CLOTHES_AI_ANALYSIS_FAILED);
        } catch (Exception e) {
            log.error("AI 의류 분석 중 예상치 못한 오류 발생 - 오류: {}", e.getMessage(), e);
            throw e;
        }
    }

}
