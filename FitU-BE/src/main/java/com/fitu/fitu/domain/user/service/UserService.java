package com.fitu.fitu.domain.user.service;

import com.fitu.fitu.domain.user.dto.request.ProfileRequest;
import com.fitu.fitu.domain.user.dto.response.BodyImageAnalysisResponse;
import com.fitu.fitu.infra.ai.bodyimage.AiBodyImageResponse;
import com.fitu.fitu.domain.user.entity.User;
import com.fitu.fitu.domain.user.entity.enums.Gender;
import com.fitu.fitu.domain.user.exception.UserNotFoundException;
import com.fitu.fitu.domain.user.repository.UserRepository;
import com.fitu.fitu.global.util.FileValidator;
import com.fitu.fitu.infra.ai.bodyimage.AiBodyImageClient;
import com.fitu.fitu.infra.s3.S3Uploader;
import lombok.RequiredArgsConstructor;
import org.springframework.beans.factory.annotation.Value;
import org.springframework.stereotype.Service;
import org.springframework.transaction.annotation.Transactional;
import org.springframework.util.StringUtils;
import org.springframework.web.multipart.MultipartFile;

import java.util.Objects;
import java.util.UUID;

@RequiredArgsConstructor
@Service
public class UserService {

    @Value("${s3.path.temp}")
    private String S3_TEMP_PATH;

    @Value("${s3.path.body-image}")
    private String S3_BODY_IMAGE_PATH;

    private final UserRepository userRepository;
    private final S3Uploader s3Uploader;
    private final FileValidator fileValidator;
    private final AiBodyImageClient aiBodyImageClient;

    @Transactional
    public User registerProfile(final ProfileRequest requestDto) {

        final String userId;

        if (requestDto.gender() == Gender.MALE) {
            userId = "474e8758-eb04-4b8d-a41f-5ef50c80cc1d";
        } else if (requestDto.gender() == Gender.FEMALE) {
            userId = "15ac1f5b-85b5-407f-a90e-ee757db56085";
        } else {
            userId = generateUserId();
        }

        final User user = requestDto.toEntity(userId);

        if (user.getBodyImageUrl() != null && !user.getBodyImageUrl().isEmpty()) {
            user.updateBodyImageUrl(s3Uploader.copy(user.getBodyImageUrl(), S3_BODY_IMAGE_PATH));
        }

        return userRepository.save(user);
    }

    @Transactional
    public User updateProfile(final String userId, final ProfileRequest requestDto) {
        final User user = findById(userId);

        user.updateProfile(requestDto.age(), requestDto.gender(), requestDto.height(), requestDto.weight(),
                requestDto.skinTone());

        if (!Objects.equals(user.getBodyImageUrl(), requestDto.bodyImageUrl())) {
            final String originBodyImageUrl = user.getBodyImageUrl();

            updateBodyImage(user, requestDto.bodyImageUrl());

            deleteBodyImage(originBodyImageUrl);
        }

        return user;
    }

    public BodyImageAnalysisResponse analyzeBodyImage(final MultipartFile file) {
        fileValidator.validateImage(file);

        final String s3Url = s3Uploader.upload(S3_TEMP_PATH, file);

        final AiBodyImageResponse response = aiBodyImageClient.analyzeBodyImage(s3Url);

        return new BodyImageAnalysisResponse(s3Url, response.warnings());
    }

    @Transactional(readOnly = true)
    public User getProfile(final String userId) {
        final User user = findById(userId);

        return user;
    }

    private String generateUserId() {
        return UUID.randomUUID().toString();
    }

    private User findById(final String userId) {
        return userRepository.findById(userId)
                .orElseThrow(() -> new UserNotFoundException(userId));
    }

    private void updateBodyImage(final User user, final String bodyImageUrl) {
        if (StringUtils.hasText(bodyImageUrl)) {
            user.updateBodyImageUrl(s3Uploader.copy(bodyImageUrl, S3_BODY_IMAGE_PATH));
        } else {
            user.updateBodyImageUrl(null);
        }
    }

    private void deleteBodyImage(final String bodyImageUrl) {
        if (StringUtils.hasText(bodyImageUrl)) {
            s3Uploader.delete(bodyImageUrl);
        }
    }
}