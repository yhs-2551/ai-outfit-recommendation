import { create } from "zustand";

const useUserStore = create((set) => ({
    // 초기 방문 시 프로필 정보
    profile: {
        age: "",
        gender: "",
        height: "",
        weight: "",
        skinTone: "",
        bodyImageUrl: null,
    },

    // 프로필 정보 업데이트
    setProfile: (profileData) =>
        set((state) => ({
            profile: { ...state.profile, ...profileData },
        })),

    // 전신 사진 업데이트
    setBodyImageUrl: (imageDataUrl) =>
        set((state) => ({
            profile: { ...state.profile, bodyImageUrl: imageDataUrl },
        })),

    // 프로필 초기화 (완료 후 정리)
    resetProfile: () =>
        set({
            profile: {
                age: "",
                gender: "",
                height: "",
                weight: "",
                skinTone: "",
                bodyImageUrl: null,
            },
        }),
}));

export default useUserStore;
