package com.fitu.fitu.domain.clothes.dto.request;

import java.util.List;

public record NewClothesRequest(
        List<ClothesRequest> clothesItems
) {

}
