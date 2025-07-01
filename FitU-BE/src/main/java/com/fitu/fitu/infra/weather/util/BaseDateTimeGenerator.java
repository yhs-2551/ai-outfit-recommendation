package com.fitu.fitu.infra.weather.util;

import java.time.LocalDateTime;
import java.time.format.DateTimeFormatter;
import java.util.List;

public class BaseDateTimeGenerator {

    private static final List<Integer> SHORT_TERM_BASE_HOURS = List.of(2, 5, 8, 11, 14, 17, 20, 23);
    private static final List<Integer> MIDTERM_BASE_HOURS = List.of(6, 18);
    private static final int MINUTE_OFFSET = 10;

    public static BaseDateTime generateBaseDateTimeForShortTerm(final LocalDateTime now) {
        return getBaseDateTime(SHORT_TERM_BASE_HOURS, now);
    }

    public static String generateBaseDateTimeForMidTerm(final LocalDateTime now) {
        final BaseDateTime baseDateTime = getBaseDateTime(MIDTERM_BASE_HOURS, now);

        return baseDateTime.baseDate + baseDateTime.baseTime;
    }

    private static BaseDateTime getBaseDateTime(final List<Integer> baseHours, LocalDateTime now) {
        now = now.minusMinutes(MINUTE_OFFSET);

        final int nowHour = now.getHour();
        int baseHour;

        if (nowHour < baseHours.getFirst()) {
            now = now.minusDays(1);
            baseHour = baseHours.getLast();
        } else {
            baseHour = baseHours.stream()
                    .filter(h -> nowHour >= h)
                    .max(Integer::compareTo)
                    .orElse(baseHours.getFirst());
        }

        final String baseDate = now.format(DateTimeFormatter.ofPattern("yyyyMMdd"));
        final String baseTime = String.format("%02d00", baseHour);

        return new BaseDateTime(baseDate, baseTime);
    }

    public record BaseDateTime(String baseDate, String baseTime) {}
}
