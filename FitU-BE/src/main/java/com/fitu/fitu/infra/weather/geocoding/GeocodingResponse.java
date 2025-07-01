package com.fitu.fitu.infra.weather.geocoding;


import lombok.Getter;

import java.util.List;

@Getter
public class GeocodingResponse {
    private List<Document> documents;
    private Meta meta;

    @Getter
    public static class Document {
        private String address_name;
        private String category_group_code;
        private String category_group_name;
        private String category_name;
        private String distance;
        private String id;
        private String phone;
        private String place_name;
        private String place_url;
        private String road_address_name;
        private String x;
        private String y;
    }

    @Getter
    public static class Meta {
        private boolean is_end;
        private int pageable_count;
        private SameName same_name;
        private int total_count;
    }

    @Getter
    public static class SameName {
        private String keyword;
        private List<String> region;
        private String selected_region;
    }
}
