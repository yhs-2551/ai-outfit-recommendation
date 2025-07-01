package com.fitu.fitu.infra.ai.recommendation;

import lombok.Getter;

import java.util.List;

@Getter
public class AiRecommendationApiResponse {
    private Header header;
    private Body body;

    @Getter
    public static class Header {
        private String resultCode;
        private String resultMsg;
    }

    @Getter
    public static class Body {
        private String summary;
        private String weather;
        private List<RecommendationItem> result;
    }

    @Getter
    public static class RecommendationItem {
        private String combination;
        private String selected;
        private String reason;
        private String virtualTryonImage;
        private String virtualTryonError;
        private List<ClothesItem> clothing_links;
    }

    @Getter
    public static class ClothesItem {
        private String id;
        private String category;
        private String image_url;
    }
}
