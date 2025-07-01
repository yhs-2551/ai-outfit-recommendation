package com.fitu.fitu.domain.user.entity;

import com.fitu.fitu.domain.user.entity.enums.Gender;
import com.fitu.fitu.domain.user.entity.enums.SkinTone;
import com.fitu.fitu.global.common.domain.BaseEntity;
import jakarta.persistence.*;
import lombok.*;

@Getter
@NoArgsConstructor(access = AccessLevel.PROTECTED)
@Table(name = "users")
@Entity
public class User extends BaseEntity {

    @Id
    private String id;

    @Column(nullable = false)
    private int age;

    @Enumerated(EnumType.STRING)
    @Column(nullable = false)
    private Gender gender;

    @Column(nullable = false)
    private int height;

    @Column(nullable = false)
    private int weight;

    @Enumerated(EnumType.STRING)
    @Column(nullable = false)
    private SkinTone skinTone;

    @Column
    private String bodyImageUrl;

    @Builder
    public User(final String id, final int age, final Gender gender,
                final int height, final int weight, final SkinTone skinTone, final String bodyImageUrl) {
        this.id = id;
        this.age = age;
        this.gender = gender;
        this.height = height;
        this.weight = weight;
        this.skinTone = skinTone;
        this.bodyImageUrl = bodyImageUrl;
    }

    public void updateProfile(final int age, final Gender gender, final int height, final int weight,
                              final SkinTone skinTone) {
        this.age = age;
        this.gender = gender;
        this.height = height;
        this.weight = weight;
        this.skinTone = skinTone;
    }

    public void updateBodyImageUrl(final String bodyImageUrl) {
        this.bodyImageUrl = bodyImageUrl;
    }
}
