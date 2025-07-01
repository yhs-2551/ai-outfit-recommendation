import React, { useRef, useState, useEffect } from "react";
import { useNavigate } from "react-router-dom";
import Header from "../components/Header";
import ProgressBar from "../components/ProgressBar/ProgressBar";
import ProfileForm from "../components/ProfileForm";
import BodyImageUploader from "../components/BodyImageUploader";
import useUserStore from "../store/userStore";
import { analyzeBodyImage } from "../api/profileAPI";
import toast from "react-hot-toast";
import { RingLoader } from "react-spinners";

const SetprofilePage = () => {
  const [uploadedImage, setUploadedImage] = useState(null);
  const [isAnalyzed, setIsAnalyzed] = useState(false);
  const [isAnalysisInProgress, setIsAnalysisInProgress] = useState(false);
  const imageUploaderRef = useRef(null);

  const [isLoading, setIsLoading] = useState(false);

  const { profile, setProfile, setBodyImageUrl } = useUserStore();

  const navigate = useNavigate();

  useEffect(() => {
    if (profile.bodyImageUrl != null) {
      setUploadedImage({
        file: null,
        preview: profile.bodyImageUrl,
      });
    }
  }, []);

  const handleImageUpload = async (file, preview) => {
    setIsLoading(true);
    setUploadedImage({ file, preview });
    setIsAnalyzed(false);
    setIsAnalysisInProgress(true);

    try {
      const response = await analyzeBodyImage(file);

      if (Array.isArray(response.warnings) && response.warnings.length > 0) {
        alert(response.warnings.join("\n"));

        setIsAnalysisInProgress(false);

        handleImageRemove();

        return;
      }

      setBodyImageUrl(response.s3Url);

      setIsAnalyzed(true);

      toast.success("전신 사진 업로드 및 검증 성공!");
    }
    catch (error) {
      console.error("전신 사진 유효성 검증 오류:", error);
      handleImageRemove();
      toast.error("전신 사진 유효성 검증에 실패했습니다.");
    } finally {
      setIsAnalysisInProgress(false);
      setIsLoading(false);
    };
  }

  const handleImageRemove = () => {
    if (uploadedImage?.preview) {
      URL.revokeObjectURL(uploadedImage.preview);
    }

    setUploadedImage(null);

    setBodyImageUrl(null); // 전역 상태에서도 제거

    setIsAnalyzed(false);
  };

  const handleSubmit = (e) => {
    e.preventDefault();

    // 전역 상태에 프로필 정보 저장
    setProfile(profile);

    // 의상 등록 페이지로 이동
    navigate('/closet-registration');
  };

  return (
    <div className="min-h-screen bg-[#F7F7F7] relative">
      {isAnalysisInProgress && (
        <div className='absolute top-0 left-0 right-0 bottom-0 backdrop-blur-sm bg-white/60 flex flex-col items-center justify-center z-20 rounded-xl'>
          <RingLoader color='#000' size={50} />
          <p className='mt-3 font-medium text-[#828282] text-[14px]'>전신 사진 여부를 확인 중...</p>
          <p className="font-medium text-[#828282] text-[14px]">잠시만 기다려 주세요.</p>
        </div>
      )}
      <Header />
      <h1 className="pt-[7.5rem] text-[2rem] font-bold text-center">FitU</h1>
      <ProgressBar activeStep={1} />

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
            isEdit={false}
            disabled={isLoading}
          />
        </div>
      </div>
    </div>
  );
}

export default SetprofilePage;