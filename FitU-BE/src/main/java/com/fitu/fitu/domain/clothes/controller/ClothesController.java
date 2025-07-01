package com.fitu.fitu.domain.clothes.controller;

import java.util.List;

import org.springframework.http.HttpStatus;
import org.springframework.http.MediaType;
import org.springframework.http.ResponseEntity;
import org.springframework.web.bind.annotation.DeleteMapping;
import org.springframework.web.bind.annotation.GetMapping;
import org.springframework.web.bind.annotation.ModelAttribute;
import org.springframework.web.bind.annotation.PatchMapping;
import org.springframework.web.bind.annotation.PathVariable;
import org.springframework.web.bind.annotation.PostMapping;
import org.springframework.web.bind.annotation.RequestBody;
import org.springframework.web.bind.annotation.RequestHeader;
import org.springframework.web.bind.annotation.RequestMapping;
import org.springframework.web.bind.annotation.RequestParam;
import org.springframework.web.bind.annotation.RestController;
import org.springframework.web.multipart.MultipartFile;

import com.fitu.fitu.domain.clothes.dto.request.ClothesAndUserInfoRequest;
import com.fitu.fitu.domain.clothes.dto.request.ClothesFilterRequest; 
import com.fitu.fitu.domain.clothes.dto.request.ClothesUpdateRequest;
import com.fitu.fitu.domain.clothes.dto.request.NewClothesRequest;
import com.fitu.fitu.domain.clothes.dto.response.ClothesListResponse;
import com.fitu.fitu.domain.clothes.dto.response.ClothesSuccessResponse;
import com.fitu.fitu.domain.clothes.dto.response.ClothesUpdateResponse;
import com.fitu.fitu.domain.clothes.service.ClothesService;
import com.fitu.fitu.domain.clothes.service.RegistrationOrchestrator;
import com.fitu.fitu.infra.ai.clothes.AiAnalysisResponse;
 
import jakarta.validation.Valid;
import lombok.RequiredArgsConstructor;
import lombok.extern.slf4j.Slf4j;

@Slf4j
@RequiredArgsConstructor
@RequestMapping("/clothes")
@RestController
public class ClothesController {

    private final ClothesService clothesService;
    private final RegistrationOrchestrator registrationOrchestrator;

    @PostMapping("/image-analysis")
    public ResponseEntity<ClothesSuccessResponse<AiAnalysisResponse>> analyzeClothes(
            @RequestParam("clothesImage") final MultipartFile clothesImage) {
        log.info("의류 AI 분석 요청");
        final AiAnalysisResponse result = clothesService.analyzeClothes(clothesImage);
        log.info("AI 의류 분석 완료");
        return ResponseEntity
                .status(HttpStatus.OK)
                .body(ClothesSuccessResponse.of("의류 AI 분석이 완료되었습니다.", result));
    }

    /**
     * 최종 의류 및 사용자 정보 저장
     * S3 업로드 + DB 저장 모두 수행
     * UserService에서 UUID 생성하여 반환
     */
    @PostMapping("/registration")
    public ResponseEntity<ClothesSuccessResponse<String>> saveClothesAndUserInfo(
            @Valid @ModelAttribute final ClothesAndUserInfoRequest request) {

        log.info("의류 및 사용자 정보 저장 요청");
        final String registrationResponse = registrationOrchestrator.saveClothesAndUserInfo(request);
        log.info("의류 및 사용자 정보 저장 완료 - 사용자 ID: {}", registrationResponse);
        return ResponseEntity
                .status(HttpStatus.CREATED)
                .body(ClothesSuccessResponse.of("의류 및 사용자 정보가 저장되었습니다.", registrationResponse));
    }

    /**
     * 사용자의 새로운 의류 등록
     */
    @PostMapping
    public ResponseEntity<ClothesSuccessResponse<Void>> saveUserClothes(
            @RequestHeader(name = "Fitu-User-UUID", required = true) final String userId,
            @ModelAttribute final NewClothesRequest request) {

        log.info("새로운 의류 등록 요청 - 사용자 ID: {}", userId);
        clothesService.saveUserClothes(userId, request);
        log.info("새로운 의류 등록 완료");
        return ResponseEntity
                .status(HttpStatus.CREATED)
                .body(ClothesSuccessResponse.of("의류 정보가 저장되었습니다."));
    }

    /**
     * 사용자의 전체 의류 목록 조회(필터링 기능 사용 전).
     */
    @GetMapping
    public ResponseEntity<ClothesSuccessResponse<List<ClothesListResponse>>> getUserClothesList(
            @RequestHeader(name = "Fitu-User-UUID", required = true) final String userId) {

        log.info("사용자 의류 목록 조회 요청 - 사용자 ID: {}", userId);
        final List<ClothesListResponse> response = clothesService.getUserClothesList(userId);
        log.info("사용자 의류 목록 조회 완료 - 의류 개수: {}", response.size());

        return ResponseEntity
                .status(HttpStatus.OK)
                .body(ClothesSuccessResponse.of("사용자 의류가 조회되었습니다.", response));

    }

    /**
     * 필터링된 사용자 의류 목록 조회
     * 초기화 선택 시: 아무것도 선택 안함 = 전체 의류 조회
     */
    @PostMapping("/filter")
    public ResponseEntity<ClothesSuccessResponse<List<ClothesListResponse>>> getUserClothesListWithFilters(
            @RequestBody final ClothesFilterRequest filterRequest,
            @RequestHeader(name = "Fitu-User-UUID", required = true) final String userId) {

        log.info("필터링된 사용자 의류 목록 조회 요청 - 사용자 ID: {}", userId);
        final List<ClothesListResponse> response = clothesService.getUserClothesListWithFilters(userId, filterRequest);
        log.info("필터링된 사용자 의류 목록 조회 완료 - 의류 개수: {}", response.size());
        return ResponseEntity
                .status(HttpStatus.OK)
                .body(ClothesSuccessResponse.of("필터링된 사용자 의류 목록이 조회되었습니다.", response));
    }

    /**
     * 의류 정보 부분 수정 (PATCH)
     * 이미지 변경 또는 속성 값만 변경 가능
     */
    @PatchMapping("/{clothesId}")
    public ResponseEntity<ClothesSuccessResponse<ClothesUpdateResponse>> updateClothes(
            @PathVariable("clothesId") final Long clothesId,
            @ModelAttribute final ClothesUpdateRequest request,
            @RequestHeader(name = "Fitu-User-UUID", required = true) final String userId) {
        log.info("의류 정보 수정 요청 - 의류 ID: {}, 사용자 ID: {}", clothesId, userId);
        final ClothesUpdateResponse response = clothesService.updateClothes(clothesId, request, userId);
        log.info("의류 정보 수정 완료");
        return ResponseEntity
                .status(HttpStatus.OK)
                .body(ClothesSuccessResponse.of("의류 정보가 수정되었습니다.", response));
    }

    /**
     * 의류 삭제
     */
    @DeleteMapping("/{clothesId}")
    public ResponseEntity<ClothesSuccessResponse<Void>> deleteClothes(
            @PathVariable("clothesId") final Long clothesId,
            @RequestHeader(name = "Fitu-User-UUID", required = true) final String userId) {

        log.info("의류 삭제 요청 - 의류 ID: {}, 사용자 ID: {}", clothesId, userId);
        clothesService.deleteClothes(clothesId, userId);
        log.info("의류 삭제 완료");
        return ResponseEntity
                .status(HttpStatus.OK)
                .body(ClothesSuccessResponse.of("의류 정보가 삭제되었습니다."));
    }

}
