package com.fitu.fitu.domain.clothes.service;

import java.util.List;
import java.util.Optional;
import java.util.function.Supplier;
import java.util.stream.Collectors;

import org.springframework.stereotype.Service;
import org.springframework.transaction.annotation.Transactional;
import org.springframework.web.multipart.MultipartFile;

import com.fitu.fitu.domain.clothes.dto.request.ClothesFilterRequest;
import com.fitu.fitu.domain.clothes.dto.request.ClothesRequest;
import com.fitu.fitu.domain.clothes.dto.request.ClothesUpdateRequest;
import com.fitu.fitu.domain.clothes.dto.request.NewClothesRequest;
import com.fitu.fitu.domain.clothes.dto.response.ClothesListResponse;
import com.fitu.fitu.domain.clothes.dto.response.ClothesUpdateResponse;
import com.fitu.fitu.domain.clothes.entity.Clothes;
import com.fitu.fitu.domain.clothes.entity.enums.Category;
import com.fitu.fitu.domain.clothes.entity.enums.Color;
import com.fitu.fitu.domain.clothes.entity.enums.Pattern;
import com.fitu.fitu.domain.clothes.entity.enums.Type;
import com.fitu.fitu.domain.clothes.repository.ClothesRepository;
import com.fitu.fitu.global.error.ErrorCode;
import com.fitu.fitu.global.error.exception.BusinessException;
import com.fitu.fitu.infra.ai.ClothesAiModelClient;
import com.fitu.fitu.infra.ai.clothes.AiAnalysisResponse;
import com.fitu.fitu.infra.ai.clothes.AiClothesAnalysisResult;
import com.fitu.fitu.infra.s3.ClothesS3Service;

import lombok.RequiredArgsConstructor;
import lombok.extern.slf4j.Slf4j;

@Slf4j
@RequiredArgsConstructor
@Service
public class ClothesService {

    private final ClothesRepository clothesRepository;
    private final ClothesS3Service s3Service;
    private final ClothesAiModelClient aiModelClient;

    public AiAnalysisResponse analyzeClothes(final MultipartFile clothesImage) {

        final String contentType = clothesImage.getContentType();
        final String originalFileName = clothesImage.getOriginalFilename();
        final String extension = originalFileName.substring(originalFileName.lastIndexOf(".") + 1).toLowerCase();

        final List<String> allowedExtensions = List.of("jpg", "jpeg", "png", "webp");

        if (clothesImage == null || clothesImage.isEmpty() || contentType == null
                || !contentType.startsWith("image/")
                || !allowedExtensions.contains(extension)) {
            log.error("의류 이미지 검증 실패 - 빈 파일 이거나 잘못된 파일 형식",
                    "Content-Type: {}, Extensions: {}", contentType, extension);
            throw new BusinessException(ErrorCode.INVALID_INPUT_VALUE);
        }

        final String clothesImageUrl = s3Service.uploadFile(clothesImage, "temp");

        // Ai 모델로 의류 분석
        final AiClothesAnalysisResult analysisResult = aiModelClient.analyzeClothes(clothesImageUrl);

        if (!analysisResult.isValidClothes()) {
            log.error("의류 Ai 분석 오류: {}", analysisResult.errorMessage());
            throw new BusinessException(ErrorCode.CLOTHES_AI_ANALYSIS_FAILED);
        }

        return AiAnalysisResponse.success(
                analysisResult.type(),
                analysisResult.category(),
                analysisResult.pattern(),
                analysisResult.color(),
                analysisResult.segmentedImagePath());
    }

    // 오케스트레이터에서 호출하는 의류 생성 메서드
    public void createClothes(final String userId, final String imageUrl,
            final Type type, final Category category,
            final Pattern pattern, final Color color) {

        final Clothes clothes = Clothes.builder()
                .userId(userId)
                .imageUrl(imageUrl)
                .type(type)
                .category(category)
                .pattern(pattern)
                .color(color)
                .build();

        clothesRepository.save(clothes);
    }

    @Transactional
    public void saveUserClothes(final String userId, final NewClothesRequest request) {

        try {

            if (userId == null || userId.isBlank()) {
                log.error("새로운 의류 등록 - 사용자 ID가 비어있음");
                throw new BusinessException(ErrorCode.INVALID_INPUT_VALUE);
            }

            if (request.clothesItems() == null || request.clothesItems().isEmpty()) {
                log.error("새로운 의류 등록 - 의류 아이템이 비어있음");
                throw new BusinessException(ErrorCode.INVALID_INPUT_VALUE);
            }

            for (ClothesRequest clothesItem : request.clothesItems()) {

                // 각 이미지 속성 선택 여부 검사
                final List<Supplier<Object>> attributeSuppliers = List.of(
                        clothesItem::type,
                        clothesItem::category,
                        clothesItem::pattern,
                        clothesItem::color);

                attributeSuppliers.forEach(supplier -> Optional.ofNullable(supplier.get())
                        .orElseThrow(() -> new BusinessException(ErrorCode.CLOTHES_ATTRIBUTES_REQUIRED)));

                String clothesImageUrl;

                if (clothesItem.clothesImageFile() != null) {
                    // Ai분석에 실패한 의류 이미지 업로드
                    clothesImageUrl = s3Service.uploadFile(clothesItem.clothesImageFile(), "final/clothes");
                } else {
                    // Ai분석에 성공한 의류 이미지 업로드
                    clothesImageUrl = s3Service.moveFileFromTempBucket(clothesItem.clothesImageUrl(), "final/clothes");
                }
                createClothes(
                        userId,
                        clothesImageUrl,
                        clothesItem.type(),
                        clothesItem.category(),
                        clothesItem.pattern(),
                        clothesItem.color());
            }

        } catch (Exception e) {
            log.error("의류 및 사용자 정보 저장 중 오류 발생 - 오류: {}", e.getMessage(), e);
            throw e;
        }
    }

    /**
     * 사용자의 전체 의류 목록 조회
     */
    @Transactional(readOnly = true)
    public List<ClothesListResponse> getUserClothesList(final String userId) {
        try {
            if (userId == null || userId.isBlank()) {
                log.error("사용자 ID가 비어있음");
                throw new BusinessException(ErrorCode.INVALID_INPUT_VALUE);
            }

            final List<Clothes> clothesList = clothesRepository.findByUserId(userId);

            final List<ClothesListResponse> responseList = clothesList.stream()
                    .map(clothes -> new ClothesListResponse(
                            clothes.getId(),
                            clothes.getImageUrl(),
                            clothes.getType(),
                            clothes.getCategory(),
                            clothes.getPattern(),
                            clothes.getColor(),
                            clothes.getCreatedAt()))
                    .collect(Collectors.toList());

            return responseList;

        } catch (Exception e) {
            log.error("사용자 의류 목록 조회 중 오류 발생 - 사용자 ID: {}, 오류: {}", userId, e.getMessage(), e);
            throw e;
        }
    }

    /**
     * 필터링된 사용자 의류 목록 조회
     * 기본값(모두 선택 안함) = 전체 의류 조회
     */
    @Transactional(readOnly = true)
    public List<ClothesListResponse> getUserClothesListWithFilters(final String userId,
            final ClothesFilterRequest filterRequest) {

        if (userId == null || userId.isBlank()) {
            log.error("사용자 ID가 비어있음");
            throw new BusinessException(ErrorCode.INVALID_INPUT_VALUE);
        }

        try {
            List<Clothes> clothesList;

            if (filterRequest.isShowAll()) {
                clothesList = clothesRepository.findByUserId(userId);
            } else {
                clothesList = clothesRepository.findByUserIdWithFilters(
                        userId,
                        filterRequest.types(),
                        filterRequest.categories(),
                        filterRequest.patterns(),
                        filterRequest.colors());
            }

            final List<ClothesListResponse> responseList = clothesList.stream()
                    .map(clothes -> new ClothesListResponse(
                            clothes.getId(),
                            clothes.getImageUrl(),
                            clothes.getType(),
                            clothes.getCategory(),
                            clothes.getPattern(),
                            clothes.getColor(),
                            clothes.getCreatedAt()))
                    .collect(Collectors.toList());

            return responseList;

        } catch (Exception e) {
            log.error("필터링된 사용자 의류 목록 조회 중 오류 발생 - 사용자 ID: {}, 오류: {}",
                    userId, e.getMessage(), e);
            throw e;
        }
    }

    /**
     * 의류 정보 부분 수정 (PATCH)
     */
    @Transactional
    public ClothesUpdateResponse updateClothes(final Long clothesId, final ClothesUpdateRequest request,
            final String userId) {
        try {
            validateUpdateRequest(request);

            // 기존 의류 존재 여부 확인
            final Clothes existingClothes = clothesRepository.findById(clothesId)
                    .orElseThrow(() -> new BusinessException(ErrorCode.CLOTHES_NOT_FOUND_BY_ID));

            // 접근 권한 확인
            if (!existingClothes.getUserId().equals(userId)) {
                throw new BusinessException(ErrorCode.CLOTHES_ACCESS_DENIED);
            }

            final MultipartFile analySisFailureFile = request.newImage();
            final String analySisSuccessPrevUrl = request.prevImage();
            final String dbImageUrl = existingClothes.getImageUrl();

            String imageUrl;

            if (analySisFailureFile != null && !analySisFailureFile.isEmpty()) {
                // 분석 실패한 이미지 파일로 저장
                imageUrl = s3Service.updateFile(analySisFailureFile, null, dbImageUrl, "final/clothes", false);
            } else if (analySisSuccessPrevUrl != null && !analySisSuccessPrevUrl.isBlank()
                    && !analySisSuccessPrevUrl.equals(dbImageUrl)) {
                // 분석 성공한 새로운 이미지 URL 저장
                imageUrl = s3Service.updateFile(null, analySisSuccessPrevUrl, dbImageUrl, "final/clothes", true);
            } else {
                // 기존 분석 성공한 이미지 URL 유지
                imageUrl = analySisSuccessPrevUrl;
            }

            existingClothes.updateClothes(
                    imageUrl, // 변경된 경우: 새 URL, 변경 안된 경우: 기존 URL
                    request.type(), // AI 분석 결과 또는 사용자 수정값
                    request.category(),
                    request.pattern(),
                    request.color());

            final Clothes updatedClothes = clothesRepository.save(existingClothes);

            return ClothesUpdateResponse.success(
                    updatedClothes.getId(),
                    updatedClothes.getImageUrl(),
                    updatedClothes.getType(),
                    updatedClothes.getCategory(),
                    updatedClothes.getPattern(),
                    updatedClothes.getColor(),
                    "의류 정보가 성공적으로 수정되었습니다.");

        } catch (Exception e) {
            log.error("의류 정보 수정 중 오류 발생 - 의류 ID: {}, 사용자 ID: {}, 오류: {}",
                    clothesId, userId, e.getMessage(), e);
            throw e;

        }
    }

    /**
     * 의류 삭제.
     */
    @Transactional
    public void deleteClothes(final Long clothesId, final String userId) {
        try {
            final Clothes clothes = clothesRepository.findById(clothesId)
                    .orElseThrow(() -> new BusinessException(ErrorCode.CLOTHES_NOT_FOUND_BY_ID));
            if (!clothes.getUserId().equals(userId)) {
                throw new BusinessException(ErrorCode.CLOTHES_ACCESS_DENIED);
            }

            s3Service.deleteFile(clothes.getImageUrl());

            clothesRepository.delete(clothes);

        } catch (Exception e) {
            log.error("의류 삭제 중 오류 발생 - 의류 ID: {}, 사용자 ID: {}, 오류: {}",
                    clothesId, userId, e.getMessage(), e);
            throw e;
        }
    }

    private void validateUpdateRequest(final ClothesUpdateRequest request) {

        if ((request.prevImage() == null || request.prevImage().isBlank()) &&
                (request.newImage() == null || request.newImage().isEmpty())) {
            throw new BusinessException(ErrorCode.INVALID_INPUT_VALUE);
        }

        final List<Supplier<Object>> attributeSuppliers = List.of(
                request::type,
                request::category,
                request::pattern,
                request::color);

        attributeSuppliers.forEach(supplier -> Optional.ofNullable(supplier.get())
                .orElseThrow(() -> new BusinessException(ErrorCode.CLOTHES_ATTRIBUTES_REQUIRED)));
    }
}
