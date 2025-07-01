// 전신 이미지 유효성 검사 API
export const analyzeBodyImage = async (imageFile) => {
    const formData = new FormData();

    formData.append("bodyImage", imageFile);

    const response = await fetch(`${import.meta.env.VITE_API_URL}/user/profile/image-analysis`, {
        method: "POST",
        body: formData,
    });

    if (!response.ok) {
        throw new Error();
    }

    return await response.json();
};

// 프로필 조회 API
export const fetchProfile = async (userId) => {
    const response = await fetch(`${import.meta.env.VITE_API_URL}/user/profile`, {
        method: "GET",
        headers: { "Fitu-User-UUID": userId },
    });

    if (!response.ok) {
        throw new Error();
    }
    

    const result = await response.json();
    return result;
};

// 프로필 수정 API
export const updateProfile = async (userId, updateData) => {
    const response = await fetch(`${import.meta.env.VITE_API_URL}/user/profile`, {
        method: "PATCH",
        headers: {
            "Content-Type": "application/json",
            "Fitu-User-UUID": userId,
        },
        body: JSON.stringify(updateData),
    });

    if (!response.ok) {
        throw new Error(`프로필 수정 실패: ${response.status}`);
    }

    const result = await response.json();
    return result.data;
};