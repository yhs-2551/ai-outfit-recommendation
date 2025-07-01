package com.fitu.fitu.domain.recommendation.service;

import com.fitu.fitu.infra.weather.*;
import com.fitu.fitu.infra.weather.geocoding.GeocodingApiClient;
import com.fitu.fitu.infra.weather.geocoding.GeocodingResponse;
import com.fitu.fitu.infra.weather.util.MidtermWeatherRegIdMapper;
import com.fitu.fitu.infra.weather.util.MidtermWeatherRegIdMapper.RegId;
import com.fitu.fitu.infra.weather.util.ShortTermWeatherGridConverter;
import com.fitu.fitu.infra.weather.util.ShortTermWeatherGridConverter.Grid;
import lombok.RequiredArgsConstructor;
import org.springframework.stereotype.Service;

import java.time.LocalDate;
import java.time.format.DateTimeFormatter;
import java.time.temporal.ChronoUnit;
import java.util.List;
import java.util.Map;
import java.util.Optional;
import java.util.stream.Collectors;

@RequiredArgsConstructor
@Service
public class WeatherService {

    private final GeocodingApiClient geocodingApiClient;
    private final ShortTermWeatherApiClient shortTermWeatherApiClient;
    private final MidtermWeatherApiClient midtermWeatherApiClient;

    private static final int SHORT_TERM_THRESHOLD_DAYS = 4;

    private static final double DEFAULT_LONGITUDE = 126.978652258823; // 서울특별시청 경도
    private static final double DEFAULT_LATITUDE = 37.56682420267543; // 서울특별시청 위도
    private static final String DEFAULT_ADDRESS = "서울 중구 태평로1가 31";

    private static final String DEFAULT_FCST_TIME = "1200";
    private static final String MIN_TEMPERATURE_CODE = "TMN";
    private static final String MAX_TEMPERATURE_CODE = "TMX";
    private static final String HOUR_TEMPERATURE_CODE = "TMP";
    private static final String RAIN_PERCENT_CODE = "POP";
    private static final String WEATHER_CONDITION_CODE = "SKY";
    private static final int DEFAULT_TEMPERATURE = 13;
    private static final int DEFAULT_RAIN_PERCENT = 0;
    private static final String DEFAULT_WEATHER_CONDITION = "0";
    private static final String DEFAULT_WEATHER_CONDITION_STRING = "맑음";

    public Weather getWeather(final LocalDate targetTime, final String targetPlace) {
        final LocalDate now = LocalDate.now();

        return (isShortTerm(now, targetTime))
                ? getShortTermWeather(now, targetTime, targetPlace)
                : getMidtermWeather(now, targetTime, targetPlace);
    }

    private boolean isShortTerm(final LocalDate now, final LocalDate targetTime) {
        return ChronoUnit.DAYS.between(now, targetTime) <= SHORT_TERM_THRESHOLD_DAYS;
    }

    private Weather getShortTermWeather(final LocalDate now, final LocalDate targetTime, final String targetPlace) {
        final Grid grid = getGridForShortTermWeather(targetPlace);

        final ShortTermWeatherResponse weatherResponse = shortTermWeatherApiClient.getWeather(grid.nx(), grid.ny());

        return parseShortTermWeatherResponse(now, targetTime, weatherResponse);
    }

    private Grid getGridForShortTermWeather(final String targetPlace) {
        final GeocodingResponse geocodingResponse = geocodingApiClient.getCoordinateAndAddress(targetPlace);

        double lon = DEFAULT_LONGITUDE;
        double lat = DEFAULT_LATITUDE;

        if (geocodingResponse == null) {
            return ShortTermWeatherGridConverter.convert(lat, lon);
        }

        final List<GeocodingResponse.Document> documents = geocodingResponse.getDocuments();

        if (!documents.isEmpty()) {
            lon = Double.parseDouble(geocodingResponse.getDocuments().getFirst().getX());
            lat = Double.parseDouble(geocodingResponse.getDocuments().getFirst().getY());
        }

        return ShortTermWeatherGridConverter.convert(lat, lon);
    }

    private Weather parseShortTermWeatherResponse(final LocalDate now, final LocalDate targetTime, final ShortTermWeatherResponse weatherResponse) {
        final String targetTimeStr = targetTime.format(DateTimeFormatter.ofPattern("yyyyMMdd"));

        if (weatherResponse == null) {
            return new Weather(getDefaultTemperature(now), getDefaultTemperature(now), DEFAULT_RAIN_PERCENT, DEFAULT_WEATHER_CONDITION_STRING);
        }

        final List<ShortTermWeatherResponse.Item> items = weatherResponse.getResponse().getBody().getItems().getItem();
        final List<ShortTermWeatherResponse.Item> filteredItems = items.stream()
                .filter(item -> item.getFcstDate().equals(targetTimeStr))
                .toList();

        final Map<String, String> noonItem = filteredItems.stream()
                .filter(item -> DEFAULT_FCST_TIME.equals(item.getFcstTime()))
                .collect(Collectors.toMap(ShortTermWeatherResponse.Item::getCategory, ShortTermWeatherResponse.Item::getFcstValue, (oldValue, newValue) -> newValue));

        final Temperature temperature = getTemperature(now, filteredItems, noonItem);
        final int rainPercent = parseRainPercentFieldForShortTermWeather(noonItem);
        final String weatherCondition = parseWeatherConditionFieldForShortTermWeather(noonItem);

        return new Weather(temperature.minTemperature, temperature.maxTemperature, rainPercent, weatherCondition);
    }

    private Temperature getTemperature(final LocalDate now, final List<ShortTermWeatherResponse.Item> filteredItems, final Map<String, String> noonItem) {
        int minTemperature = parseTemperatureFieldForShortTermWeather(filteredItems, MIN_TEMPERATURE_CODE, getDefaultTemperature(now));
        int maxTemperature = parseTemperatureFieldForShortTermWeather(filteredItems, MAX_TEMPERATURE_CODE, getDefaultTemperature(now));

        if (minTemperature != Integer.MIN_VALUE && maxTemperature != Integer.MIN_VALUE) {
            return new Temperature(minTemperature, maxTemperature);
        }

        int noonTemperature = Optional.ofNullable(noonItem.get(HOUR_TEMPERATURE_CODE))
                .map(Integer::parseInt)
                .orElse(getDefaultTemperature(now));

        minTemperature = noonTemperature;
        maxTemperature = noonTemperature;

        return new Temperature(minTemperature, maxTemperature);
    }

    private int parseTemperatureFieldForShortTermWeather(final List<ShortTermWeatherResponse.Item> filteredItems, final String category, final int orElseValue) {
        return filteredItems.stream()
                .filter(item -> category.equals(item.getCategory()))
                .map(item -> (int) Double.parseDouble(item.getFcstValue()))
                .findFirst()
                .orElse(orElseValue);
    }

    private int getDefaultTemperature(final LocalDate now) {
        final int nowMonth = now.getMonthValue();

        return switch(nowMonth) {
            case 1 -> -2;
            case 2 -> 0;
            case 3 -> 6;
            case 4 -> 12;
            case 5 -> 18;
            case 6 -> 22;
            case 7 -> 25;
            case 8 -> 26;
            case 9 -> 21;
            case 10 -> 15;
            case 11 -> 7;
            case 12 -> 0;
            default -> DEFAULT_TEMPERATURE;
        };
    }

    private int parseRainPercentFieldForShortTermWeather(final Map<String, String> noonItem) {
        return Optional.ofNullable(noonItem.get(RAIN_PERCENT_CODE))
                .map(Integer::parseInt)
                .orElse(DEFAULT_RAIN_PERCENT);
    }

    private String parseWeatherConditionFieldForShortTermWeather(final Map<String, String> noonItem) {
        return Optional.ofNullable(noonItem.get(WEATHER_CONDITION_CODE))
                .map(this::mapWeatherConditionCodeToString)
                .orElse(DEFAULT_WEATHER_CONDITION);
    }

    private String mapWeatherConditionCodeToString(final String skyCode) {
        return switch(skyCode) {
            case "6", "7", "8" -> "구름 많음";
            case "9", "10" -> "흐림";
            default -> "맑음";
        };
    }

    private Weather getMidtermWeather(final LocalDate now, final LocalDate targetTime, final String targetPlace) {
        final RegId regId = getRegIdForMidtermWeather(targetPlace);

        final MidtermTemperatureResponse temperatureResponse = midtermWeatherApiClient.getTemperature(regId.tempRegId());
        final MidtermWeatherConditionResponse weatherConditionResponse = midtermWeatherApiClient.getWeatherCondition(regId.condRegId());

        return parseMidtermWeatherResponse(now, targetTime, temperatureResponse, weatherConditionResponse);
    }

    private RegId getRegIdForMidtermWeather(final String targetPlace) {
        final GeocodingResponse geocodingResponse = geocodingApiClient.getCoordinateAndAddress(targetPlace);

        String address = DEFAULT_ADDRESS;

        if (geocodingResponse == null) {
            return MidtermWeatherRegIdMapper.map(address.split(" ")[0]);
        }

        final List<GeocodingResponse.Document> documents = geocodingResponse.getDocuments();

        if (!documents.isEmpty()) {
            address = geocodingResponse.getDocuments().getFirst().getAddress_name();
        }

        final String city = address.split(" ")[0];

        return MidtermWeatherRegIdMapper.map(city);
    }

    private Weather parseMidtermWeatherResponse(final LocalDate now, final LocalDate targetTime, final MidtermTemperatureResponse temperatureResponse, final MidtermWeatherConditionResponse weatherConditionResponse) {
        if (temperatureResponse == null || weatherConditionResponse == null) {
            return new Weather(getDefaultTemperature(now), getDefaultTemperature(now), DEFAULT_RAIN_PERCENT, DEFAULT_WEATHER_CONDITION_STRING);
        }

        final int dayDiff = (int) ChronoUnit.DAYS.between(now, targetTime);

        final MidtermTemperatureResponse.Item temperatureItems = temperatureResponse.getResponse().getBody().getItems().getItem().getFirst();
        final MidtermWeatherConditionResponse.Item weatherConditionItems = weatherConditionResponse.getResponse().getBody().getItems().getItem().getFirst();

        final Temperature temperature = parseTemperatureFieldForMidtermWeather(temperatureItems, dayDiff);
        final int rainPercent = parseRainPercentFieldForMidtermWeather(weatherConditionItems, dayDiff);
        final String weatherCondition = parseWeatherConditionFieldForMidtermWeather(weatherConditionItems, dayDiff);

        return new Weather(temperature.minTemperature, temperature.maxTemperature, rainPercent, weatherCondition);
    }

    private Temperature parseTemperatureFieldForMidtermWeather(final MidtermTemperatureResponse.Item item, final int dayDiff) {
        return switch(dayDiff) {
            case 4 -> new Temperature(item.getTaMin4(), item.getTaMax4());
            case 5 -> new Temperature(item.getTaMin5(), item.getTaMax5());
            case 6 -> new Temperature(item.getTaMin6(), item.getTaMax6());
            case 7 -> new Temperature(item.getTaMin7(), item.getTaMax7());
            case 8 -> new Temperature(item.getTaMin8(), item.getTaMax8());
            case 9 -> new Temperature(item.getTaMin9(), item.getTaMax9());
            case 10 -> new Temperature(item.getTaMin10(), item.getTaMax10());
            default -> new Temperature(DEFAULT_TEMPERATURE, DEFAULT_TEMPERATURE);
        };
    }

    private int parseRainPercentFieldForMidtermWeather(final MidtermWeatherConditionResponse.Item item, final int dayDiff) {
        return switch(dayDiff) {
            case 4 -> item.getRnSt4Pm();
            case 5 -> item.getRnSt5Pm();
            case 6 -> item.getRnSt6Pm();
            case 7 -> item.getRnSt7Pm();
            case 8 -> item.getRnSt8();
            case 9 -> item.getRnSt9();
            case 10 -> item.getRnSt10();
            default -> DEFAULT_RAIN_PERCENT;
        };
    }

    private String parseWeatherConditionFieldForMidtermWeather(final MidtermWeatherConditionResponse.Item item, int dayDiff) {
        return switch(dayDiff) {
            case 4 -> item.getWf4Pm();
            case 5 -> item.getWf5Pm();
            case 6 -> item.getWf6Pm();
            case 7 -> item.getWf7Pm();
            case 8 -> item.getWf8();
            case 9 -> item.getWf9();
            case 10 -> item.getWf10();
            default -> DEFAULT_WEATHER_CONDITION_STRING;
        };
    }

    public record Weather(int minTemperature, int maxTemperature, int rainPercent, String weatherCondition) {}

    public record Temperature(int minTemperature, int maxTemperature) {}
}
