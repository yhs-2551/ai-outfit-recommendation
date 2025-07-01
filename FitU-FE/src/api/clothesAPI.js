// ai 의류 분석 API
export const analyzeClothingImage = async (imageFile) => {
    const formData = new FormData();
    formData.append("clothesImage", imageFile);

    const serverResponse = await fetch(`${import.meta.env.VITE_API_URL}/clothes/image-analysis`, {
        method: "POST",
        body: formData,
    });

    if (!serverResponse.ok) {
        throw new Error(`의류 이미지 분석 API 호출 실패: ${serverResponse.status}`);
    }

    const response = await serverResponse.json();
    
    return response.data;
};

// 사용자 프로필, 옷장 등록 api
export const registerUserWithCloset = async (profileData, clothingItems) => {

    const formData = new FormData();

    const { bodyImageUrl, ...profileWithoutBodyImageUrl } = profileData;

    if (bodyImageUrl) {
        formData.append("userProfileInfo.bodyImageUrl", bodyImageUrl);
    }

    // DTO 바인딩을 쉽게 처리하기 위해
    formData.append("userProfileInfo.age", profileWithoutBodyImageUrl.age);
    formData.append("userProfileInfo.gender", profileWithoutBodyImageUrl.gender);
    formData.append("userProfileInfo.height", profileWithoutBodyImageUrl.height);
    formData.append("userProfileInfo.weight", profileWithoutBodyImageUrl.weight);
    formData.append("userProfileInfo.skinTone", profileWithoutBodyImageUrl.skinTone);

    clothingItems.forEach((item, index) => {
        if (item.file) {
            formData.append(`clothesItems[${index}].clothesImageFile`, item.file);
        }

        if (item.s3Url) {
            formData.append(`clothesItems[${index}].clothesImageUrl`, item.s3Url);
        }
        // 속성들, 주의 사항: 프론트에서 type, category는 백엔드에서 category, type으로 매핑
        formData.append(`clothesItems[${index}].type`, item.attributes.category);
        formData.append(`clothesItems[${index}].category`, item.attributes.type);
        formData.append(`clothesItems[${index}].pattern`, item.attributes.pattern);
        formData.append(`clothesItems[${index}].color`, item.attributes.tone);
    });

    const response = await fetch(`${import.meta.env.VITE_API_URL}/clothes/registration`, {
        method: "POST",
        body: formData,
    });

    if (!response.ok) {
        throw new Error();
    }
    const result = await response.json();
    return result.data; // 사용자 uuid값 반환
};

// 새롭게 옷 추가할때
export const registerNewClosetItems = async (clothingItems, userId) => {
    const formData = new FormData();

    clothingItems.forEach((item, index) => {
        if (item.file) {
            formData.append(`clothesItems[${index}].clothesImageFile`, item.file);
        }

        // 의류 이미지
        formData.append(`clothesItems[${index}].clothesImageUrl`, item.s3Url);
        // 속성들, 주의 사항: 프론트에서 type, category는 백엔드에서 category, type으로 매핑
        formData.append(`clothesItems[${index}].type`, item.attributes.category);
        formData.append(`clothesItems[${index}].category`, item.attributes.type);
        formData.append(`clothesItems[${index}].pattern`, item.attributes.pattern);
        formData.append(`clothesItems[${index}].color`, item.attributes.tone);
    });

    const response = await fetch(`${import.meta.env.VITE_API_URL}/clothes`, {
        method: "POST",
        headers: {
            "Fitu-User-UUID": userId,
        },
        body: formData,
    });

    if (!response.ok) {
        throw new Error();
    }
    const result = await response.json();
    return result.data;
};

// 초기 옷장 조회 API
export const fetchClosetItems = async (userId) => {
    const response = await fetch(`${import.meta.env.VITE_API_URL}/clothes`, {
        method: "GET",
        headers: { "Fitu-User-UUID": userId },
    });

    if (!response.ok) {
        throw new Error();
    }

    const result = await response.json();
    return result.data;
};

// 필터링 조회 api
export const fetchFilteredClothes = async (userId, filters) => {
    const category = filters.category || [];
    const type = filters.type || [];
    const pattern = filters.pattern || [];
    const tone = filters.tone || [];

    // 백엔드에서 type -> categories, category -> types로 받음 또한 tone 대신 colors로 받음
    const requestBody = {
        categories: type,
        types: category,
        patterns: pattern,
        colors: tone,
    };
    const response = await fetch(`${import.meta.env.VITE_API_URL}/clothes/filter`, {
        method: "POST",
        headers: {
            "Content-Type": "application/json",
            "Fitu-User-UUID": userId,
        },
        body: JSON.stringify(requestBody),
    });

    if (!response.ok) {
        throw new Error(`필터링 실패: ${response.status}`);
    }

    const result = await response.json();
    return result.data;
};

// 업데이트 api
export const updateClothesItem = async (userId, clothesId, updateData) => {
    const formData = new FormData();

    if (updateData.prevImage) {
        formData.append("prevImage", updateData.prevImage);
    }

    if (updateData.newImage) {
        formData.append("newImage", updateData.newImage);
    }

    formData.append("type", updateData.category);
    formData.append("category", updateData.type);
    formData.append("pattern", updateData.pattern);
    formData.append("color", updateData.tone);

    const response = await fetch(`${import.meta.env.VITE_API_URL}/clothes/${clothesId}`, {
        method: "PATCH",
        headers: {
            // FormData를 사용하면 Content-Type은 자동으로 multipart/form-data로 설정됨
            // Content-Type을 명시적으로 설정하지 않음
            "Fitu-User-UUID": userId,
        },
        body: formData,
    });

    if (!response.ok) {
        throw new Error(`의류 수정 실패: ${response.status}`);
    }

    const result = await response.json();
    return result.data;
};

export const deleteClothesItem = async (userId, clothesId) => {
    const response = await fetch(`${import.meta.env.VITE_API_URL}/clothes/${clothesId}`, {
        method: "DELETE",
        headers: {
            "Fitu-User-UUID": userId,
        },
    });

    if (!response.ok) {
        throw new Error(`의류 삭제 실패: ${response.status}`);
    }

    const result = await response.json();
    return result.data;
};
