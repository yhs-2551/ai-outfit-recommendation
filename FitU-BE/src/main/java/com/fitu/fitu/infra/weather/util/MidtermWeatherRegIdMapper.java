package com.fitu.fitu.infra.weather.util;

public class MidtermWeatherRegIdMapper {

    private static final String TEMP_SEOUL = "11B10101";
    private static final String TEMP_GANGWON = "11D20501";
    private static final String TEMP_CHUNGNAM = "11C20401";
    private static final String TEMP_CHUNGBUK = "11C10301";
    private static final String TEMP_JEONNAM = "11F20501";
    private static final String TEMP_JEONBUK = "11F10201";
    private static final String TEMP_GYEONGBUK = "11H10701";
    private static final String TEMP_GYEONGNAM = "11H20201";
    private static final String TEMP_JEJU = "11G00201";

    private static final String COND_SEOUL = "11B00000";
    private static final String COND_GANGWON = "11D20000";
    private static final String COND_CHUNGNAM = "11C20000";
    private static final String COND_CHUNGBUK = "11C10000";
    private static final String COND_JEONNAM = "11F20000";
    private static final String COND_JEONBUK = "11F10000";
    private static final String COND_GYEONGBUK = "11H10000";
    private static final String COND_GYEONGNAM = "11H20000";
    private static final String COND_JEJU = "11G00000";

    public static RegId map(final String region) {
        return switch(region) {
            case "강원특별자치도" -> new RegId(TEMP_GANGWON, COND_GANGWON);
            case "대전", "세종특별자치시", "충남" -> new RegId(TEMP_CHUNGNAM, COND_CHUNGNAM);
            case "충북" -> new RegId(TEMP_CHUNGBUK, COND_CHUNGBUK);
            case "광주", "전남" -> new RegId(TEMP_JEONNAM, COND_JEONNAM);
            case "전북특별자치도" -> new RegId(TEMP_JEONBUK, COND_JEONBUK);
            case "대구", "경북" -> new RegId(TEMP_GYEONGBUK, COND_GYEONGBUK);
            case "부산", "울산", "경남" -> new RegId(TEMP_GYEONGNAM, COND_GYEONGNAM);
            case "제주특별자치도" -> new RegId(TEMP_JEJU, COND_JEJU);
            default -> new RegId(TEMP_SEOUL, COND_SEOUL);
        };
    }

    public record RegId(String tempRegId, String condRegId) {}
}
