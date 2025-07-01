package com.fitu.fitu.infra.weather;

import lombok.Getter;

import java.util.List;

@Getter
public class ShortTermWeatherResponse {
    private Response response;

    @Getter
    public static class Response {
        private Header header;
        private Body body;
    }

    @Getter
    public static class Header {
        private String resultCode;
        private String resultMsg;
    }

    @Getter
    public static class Body {
        private String dataType;
        private Items items;
        private int pageNo;
        private int numOfRows;
        private int totalCount;
    }

    @Getter
    public static class Items {
        private List<Item> item;
    }

    @Getter
    public static class Item {
        private String baseDate;
        private String baseTime;
        private String fcstDate;
        private String fcstTime;
        private String category;
        private String fcstValue;
        private int nx;
        private int ny;
    }
}
