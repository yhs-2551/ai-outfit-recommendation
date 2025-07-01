package com.fitu.fitu.infra.weather;

import lombok.Getter;

import java.util.List;

@Getter
public class MidtermWeatherConditionResponse {
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
        private String regId;
        private int rnSt4Am;
        private int rnSt4Pm;
        private int rnSt5Am;
        private int rnSt5Pm;
        private int rnSt6Am;
        private int rnSt6Pm;
        private int rnSt7Am;
        private int rnSt7Pm;
        private int rnSt8;
        private int rnSt9;
        private int rnSt10;
        private String wf4Am;
        private String wf4Pm;
        private String wf5Am;
        private String wf5Pm;
        private String wf6Am;
        private String wf6Pm;
        private String wf7Am;
        private String wf7Pm;
        private String wf8;
        private String wf9;
        private String wf10;
    }
}
