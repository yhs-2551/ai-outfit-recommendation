package com.fitu.fitu.domain.clothes.service;

import java.util.ArrayList;
import java.util.List;
import java.util.Optional;
import java.util.function.Supplier;

import org.springframework.stereotype.Service;
import org.springframework.transaction.annotation.Transactional;

import com.fitu.fitu.domain.clothes.dto.request.ClothesAndUserInfoRequest;
import com.fitu.fitu.domain.clothes.dto.request.ClothesRequest;
import com.fitu.fitu.domain.clothes.entity.enums.Type;
import com.fitu.fitu.domain.user.service.UserService;
import com.fitu.fitu.global.error.ErrorCode;
import com.fitu.fitu.global.error.exception.BusinessException;
import com.fitu.fitu.infra.s3.ClothesS3Service;

import lombok.RequiredArgsConstructor;
import lombok.extern.slf4j.Slf4j;

@Slf4j
@RequiredArgsConstructor
@Service
public class RegistrationOrchestrator {

    private final ClothesService clothesService;
    private final ClothesS3Service s3Service;
    private final UserService userService;

    /*
     * 최종 의류 및 사용자 정보 저장을 오케스트레이션
     * UserService에서 UUID 생성 및 사용자 정보 저장
     */
    @Transactional
    public String saveClothesAndUserInfo(ClothesAndUserInfoRequest request) {
        try {

            validateClothesItems(request.clothesItems());

            String userId = userService.registerProfile(request.userProfileInfo()).getId();

            for (ClothesRequest clothesItem : request.clothesItems()) {

                String clothesImageUrl;

                if (clothesItem.clothesImageFile() != null && clothesItem.clothesImageUrl() == null) {
                    // 분석에 실패한 의류 이미지 S3 업로드
                    clothesImageUrl = s3Service.uploadFile(clothesItem.clothesImageFile(), "final/clothes");
                } else {
                    // 분석에 성공한 의류 이미지 S3 업로드
                    clothesImageUrl = s3Service.moveFileFromTempBucket(clothesItem.clothesImageUrl(), "final/clothes");
                }

                clothesService.createClothes(
                        userId,
                        clothesImageUrl,
                        clothesItem.type(),
                        clothesItem.category(),
                        clothesItem.pattern(),
                        clothesItem.color());
            }

            return userId;

        } catch (Exception e) {
            log.error("의류 및 사용자 정보 저장 중 오류 발생 - 오류: {}", e.getMessage(), e);
            throw e;
        }
    }

    private void validateClothesItems(List<ClothesRequest> clothesItems) {
        if (clothesItems == null || clothesItems.isEmpty()) {
            log.error("초기 방문 시 의류 등록 - 의류 아이템이 비어있음");
            throw new BusinessException(ErrorCode.INVALID_INPUT_VALUE);
        }

        final List<Type> topItems = new ArrayList<>();
        final List<Type> bottomItems = new ArrayList<>();

        for (ClothesRequest item : clothesItems) {
            final List<Supplier<Object>> attributeSuppliers = List.of(
                    item::type,
                    item::category,
                    item::pattern,
                    item::color);

            attributeSuppliers.forEach(supplier -> Optional.ofNullable(supplier.get())
                    .orElseThrow(() -> new BusinessException(ErrorCode.CLOTHES_ATTRIBUTES_REQUIRED)));

            if (item.type() == Type.TOP) {
                topItems.add(item.type());
            } else if (item.type() == Type.BOTTOM) {
                bottomItems.add(item.type());
            }
        }

        final int possibleSets = Math.min(topItems.size(), bottomItems.size());

        if (possibleSets < 3) {
            log.error("유효하지 않은 의류 조합: 상의와 하의 조합으로 최소 3세트가 필요함. 현재 세트: {}", possibleSets);
            throw new BusinessException(ErrorCode.CLOTHES_INVALID_CLOTHES_COMBINATION);
        }
    }

}
