package com.fitu.fitu.global.common.annotation;

import jakarta.validation.ConstraintValidator;
import jakarta.validation.ConstraintValidatorContext;

import java.time.LocalDate;
import java.time.temporal.ChronoUnit;

public class DateRangeValidator implements ConstraintValidator<ValidDateRange, LocalDate> {

    private long range;

    @Override
    public void initialize(final ValidDateRange constraintAnnotation) {
        this.range = constraintAnnotation.range();
    }

    public boolean isValid(final LocalDate value, final ConstraintValidatorContext context) {
        if (value == null) {
            return true;
        }

        final long dayDiff = ChronoUnit.DAYS.between(LocalDate.now(), value);

        return dayDiff >= 0 && dayDiff <= range;
    }
}
