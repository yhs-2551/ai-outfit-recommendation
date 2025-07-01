import React, { useState, useRef, useEffect } from "react";
import { useNavigate } from "react-router-dom";
import Header from "../components/Header";
import ProfileForm from "../components/ProfileForm";
import BodyImageUploader from "../components/BodyImageUploader";
import useUserStore from "../store/userStore";
import { analyzeBodyImage, fetchProfile, updateProfile } from "../api/profileAPI";
import toast from "react-hot-toast";
import { RingLoader } from "react-spinners";

const MyProfilePage = () => {
    const [uploadedImage, setUploadedImage] = useState(null);
    const [isAnalyzed, setIsAnalyzed] = useState(false);
    const [isAnalysisInProgress, setIsAnalysisInProgress] = useState(false);
    const imageUploaderRef = useRef(null);

    const { profile, setProfile, setBodyImageUrl } = useUserStore();

    const [isLoading, setIsLoading] = useState(false);

    const navigate = useNavigate();

    const handleImageUpload = async (file, preview) => {
        setIsLoading(true);
        setUploadedImage({ file, preview });
        setIsAnalyzed(false);
        setIsAnalysisInProgress(true);

        try {
            const response = await analyzeBodyImage(file);

            if (Array.isArray(response.warnings) && response.warnings.length > 0) {
                alert(response.warnings.join("\n"));

                handleImageRemove();
            } else {
                setBodyImageUrl(response.s3Url);

                setIsAnalyzed(true);

                toast.success("전신 사진 업로드 및 검증 성공!");
            }
        }
        catch (error) {
            console.error("전신 사진 유효성 검증 오류:", error);
            toast.error("전신 사진 유효성 검증에 실패했습니다.");
        } finally {
            setIsLoading(false);
            setIsAnalysisInProgress(false);
        };
    }

    const handleImageRemove = () => {
        if (uploadedImage?.preview) {
            URL.revokeObjectURL(uploadedImage.preview);
        }

        setUploadedImage(null);

        setBodyImageUrl(null);

        setIsAnalyzed(false);
    };

    useEffect(() => {
        getProfile();
    }, []);

    const getProfile = async () => {
        try {
            const userId = localStorage.getItem("userId");

            if (!userId) {
                alert("사용자 정보가 없습니다. 프로필을 설정해주세요.");
                navigate("/set-profile");
                return;
            }

            const response = await fetchProfile(userId);

            if (response) {
                setProfile({
                    age: response.age || "",
                    gender: response.gender || "",
                    height: response.height || "",
                    weight: response.weight || "",
                    skinTone: response.skinTone || "",
                    bodyImageUrl: response.bodyImageUrl || null,
                });

                if (response.bodyImageUrl) {
                    setUploadedImage({
                        file: null,
                        preview: response.bodyImageUrl,
                    });
                } else {
                    setUploadedImage(null);
                }
            }
        } catch (e) {
            console.error("프로필 정보를 가져오는데 실패했습니다:", e);
        }
    };

    const handleSubmit = async (e) => {
        e.preventDefault();
        try {
            const userId = localStorage.getItem("userId");

            if (!userId) {
                alert("사용자 정보가 없습니다. 프로필을 설정해주세요.");
                navigate("/set-profile");
                return;
            }

            await updateProfile(userId, profile);
            toast.success("프로필 업데이트 성공!");
        } catch (e) {
            console.error("프로필 업데이트를 실패했습니다:", e);
        }
    };

    return (
        <>
            <div className="min-h-screen bg-[#F7F7F7] relative">
                {isAnalysisInProgress && (
                    <div className='absolute top-0 left-0 right-0 bottom-0 backdrop-blur-sm bg-white/60 flex flex-col items-center justify-center z-20 rounded-xl'>
                        <RingLoader color='#000' size={50} />
                        <p className='mt-3 font-medium text-[#828282] text-[14px]'>전신 사진 여부를 확인 중...</p>
                        <p className="font-medium text-[#828282] text-[14px]">잠시만 기다려 주세요.</p>
                    </div>
                )}
                <Header />
                <h1 className="pt-[7.5rem] text-[2rem] font-bold text-center">내 프로필</h1>

                <div className="flex flex-col items-center mt-[3.75rem]">
                    <BodyImageUploader
                        ref={imageUploaderRef}
                        uploadedImage={uploadedImage}
                        onImageUpload={handleImageUpload}
                        onImageRemove={handleImageRemove}
                    />
                    <p className="text-[12px] text-[#828282] mt-1 text-center">
                        전신 사진을 등록하면<br />추천 코디를 착용한 모습을 볼 수 있어요.
                    </p>
                    <div className="mt-[3.75rem]">
                        <ProfileForm
                            profile={profile}
                            setProfile={setProfile}
                            handleSubmit={handleSubmit}
                            isEdit={true}
                            disabled={isLoading}
                        />
                    </div>
                </div>
            </div>
        </>
    );
}

export default MyProfilePage;