package com.fitu.fitu.domain.user.dto.request;

import com.fitu.fitu.domain.user.entity.User;
import com.fitu.fitu.domain.user.entity.enums.Gender;
import com.fitu.fitu.domain.user.entity.enums.SkinTone;
import jakarta.validation.constraints.NotNull;
import org.hibernate.validator.constraints.Range;

public record ProfileRequest(
        @Range(min = 10, max = 100)
        int age,
        @NotNull
        Gender gender,
        @Range(min = 100, max = 250)
        int height,
        @Range(min = 30, max = 300)
        int weight,
        @NotNull
        SkinTone skinTone,
        String bodyImageUrl
) {
    public User toEntity(final String id) {
        return User.builder()
                .id(id)
                .age(age)
                .gender(gender)
                .height(height)
                .weight(weight)
                .skinTone(skinTone)
                .bodyImageUrl(bodyImageUrl)
                .build();
    }
}