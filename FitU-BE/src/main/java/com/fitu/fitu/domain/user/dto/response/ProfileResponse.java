package com.fitu.fitu.domain.user.dto.response;

import com.fitu.fitu.domain.user.entity.User;
import com.fitu.fitu.domain.user.entity.enums.Gender;
import com.fitu.fitu.domain.user.entity.enums.SkinTone;

public record ProfileResponse(
        String userId,
        int age,
        Gender gender,
        int height,
        int weight,
        SkinTone skinTone,
        String bodyImageUrl
) {
    public static ProfileResponse of(final User user) {
        return new ProfileResponse(user.getId(), user.getAge(), user.getGender(), user.getHeight(), user.getWeight(),
                user.getSkinTone(), user.getBodyImageUrl());
    }
}