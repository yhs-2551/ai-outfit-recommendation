package com.fitu.fitu.global.common.annotation;

import jakarta.validation.Constraint;
import jakarta.validation.Payload;

import java.lang.annotation.ElementType;
import java.lang.annotation.Retention;
import java.lang.annotation.RetentionPolicy;
import java.lang.annotation.Target;

@Retention(RetentionPolicy.RUNTIME)
@Target({ElementType.FIELD, ElementType.PARAMETER})
@Constraint(validatedBy = DateRangeValidator.class)
public @interface ValidDateRange {

    String message() default "Date Must Be In 10 Days.";

    Class<?>[] groups() default {};

    Class<? extends Payload>[] payload() default {};

    long range() default 10;
}
