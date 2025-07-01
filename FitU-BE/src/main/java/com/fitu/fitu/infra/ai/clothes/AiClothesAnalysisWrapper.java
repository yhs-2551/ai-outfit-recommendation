package com.fitu.fitu.infra.ai.clothes;

import java.util.List;

public record AiClothesAnalysisWrapper(
        String status, List<AiClothesAnalysisResult> analyses
) {

}
