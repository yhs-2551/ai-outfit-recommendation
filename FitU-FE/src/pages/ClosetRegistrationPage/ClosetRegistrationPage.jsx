import React, { useState, useEffect, useRef } from "react";
import { useLocation, useNavigate } from "react-router-dom";
import { RingLoader } from "react-spinners";

import ImageUploader from "./ImageUploader";
import AttributeSelectors from "./AttributeSelectors";
import Waitlist from "./Waitlist";
import Header from "../../components/Header";
import useUserStore from "../../store/userStore";
import ProgressBar from "../../components/ProgressBar/ProgressBar";
import { analyzeClothingImage, registerNewClosetItems, registerUserWithCloset } from "../../api/clothesAPI";

const requiredFields = ["age", "gender", "height", "weight", "skinTone"];

const ClosetRegistrationPage = ({ showProgress = true, title = "FitU" }) => {
    const [uploadedImage, setUploadedImage] = useState(null);
    const [attributes, setAttributes] = useState({
        category: "",
        type: "",
        pattern: "",
        tone: "",
    });
    const [isAnalyzed, setIsAnalyzed] = useState(false);
    const [isAnalysisInProgress, setIsAnalysisInProgress] = useState(false);
    const [isAnalysisSuccess, setIsAnalysisSuccess] = useState(false);
    const [isRegistering, setIsRegistering] = useState(false);
    const [waitlistItems, setWaitlistItems] = useState([]);
    const [isWaitlistExpanded, setIsWaitlistExpanded] = useState(true);

    const imageUploaderRef = useRef(null);

    const { profile } = useUserStore();

    const navigate = useNavigate();
    const location = useLocation();

    useEffect(() => {
        // 프로필 정보가 없으면 프로필 페이지로 리다이렉트
        const hasAllRequiredFields = requiredFields.every((field) => profile[field]);
        const userId = localStorage.getItem("userId");

        if (!hasAllRequiredFields && !userId) {
            alert("프로필 정보가 누락되었습니다. 프로필 페이지로 이동합니다.");
            navigate("/set-profile");
        }

        if (location.pathname === "/closet-registration" && userId) {
            navigate("/closet-add");
        }
    }, []);

    const handleImageUpload = async (file, preview) => {
        setUploadedImage({ file, preview });
        setIsAnalyzed(false); // 새 이미지 업로드 시 분석 상태 초기화
        setIsAnalysisInProgress(true); // 버튼에 분석 중 상태 표시

        try {
            const result = await analyzeClothingImage(file);

            if (result) {
                setUploadedImage({
                    file: null,
                    preview: result.imageUrl,
                });

                setAttributes({
                    category: result.type || "",
                    type: result.category || "",
                    pattern: result.pattern || "",
                    tone: result.color || "",
                });
            }

            setIsAnalyzed(true);
            setIsAnalysisSuccess(true);
        } catch (error) {
            console.error("이미지 분석 오류:", error);
            setIsAnalyzed(true);
            setIsAnalysisSuccess(false);

            if (String(error).includes("400")) {
                setTimeout(() => {
                    alert("이미지 파일 형식/크기가 올바르지 않습니다. 다시시도 하거나 수동으로 선택해주세요.");
                }, 500);
            } else {
                setTimeout(() => {
                    alert("의상 분석에 실패했습니다. 다시시도 하거나 수동으로 선택해주세요.");
                }, 500);
            }
        } finally {
            setIsAnalysisInProgress(false); // 분석 완료 상태
        }
    };

    const handleImageRemove = () => {
        if (uploadedImage?.preview) {
            URL.revokeObjectURL(uploadedImage.preview);
        }
        setUploadedImage(null);
        setIsAnalyzed(false);
        setAttributes({
            category: "",
            type: "",
            pattern: "",
            tone: "",
        });
    };

    const handleAttributeChange = (name, value) => {
        setAttributes((prev) => ({
            ...prev,
            [name]: value,
        }));
    };

    const handleAddToWaitlist = async () => {
        if (!uploadedImage) return;

        // 속성 유효성 검사
        const isAttributesValid = Object.values(attributes).every((value) => value && value.trim() !== "");

        if (!isAttributesValid) {
            alert("모든 의류 속성(카테고리, 타입, 패턴, 톤)을 선택해주세요.");
            return;
        }

        // // 이미지 URL에서 Blob으로 가져오기 -> 분석에 실패했을경우 미리보기로 사용
        const response = await fetch(uploadedImage.preview);
        const blob = await response.blob();
        const analysisFailureUrl = URL.createObjectURL(blob);

        // 새로운 대기 목록 항목 생성
        const newItem = {
            id: Date.now().toString(),
            image: !isAnalysisSuccess ? analysisFailureUrl : null, // 분석에 실패했을 경우 대기 목록에서 프론트 미리 보여주기 용도
            file: !isAnalysisSuccess ? uploadedImage.file : null, //  분석에 실패했을 경우 백엔드로 보내줄 파일
            attributes: { ...attributes },
            s3Url: isAnalysisSuccess ? uploadedImage.preview : null,
        };

        setWaitlistItems((prevItems) => [...prevItems, newItem]);

        // 대기 목록에 이미지 추가 후, 입력 초기화
        if (imageUploaderRef.current) {
            imageUploaderRef.current.resetFileInput();
        }

        // 입력 필드 초기화
        handleImageRemove();
    };

    const handleRemoveFromWaitlist = (itemId) => {
        setWaitlistItems((prevItems) => {
            // 삭제하기 전에 해당 아이템의 이미지 URL을 해제
            const itemToRemove = prevItems.find((item) => item.id === itemId);
            if (itemToRemove && itemToRemove.image) {
                URL.revokeObjectURL(itemToRemove.image);
            }
            return prevItems.filter((item) => item.id !== itemId);
        });
    };

    const checkClothingRequirements = () => {
        const topItems = waitlistItems.filter((item) => item.attributes.category === "TOP");
        const bottomItems = waitlistItems.filter((item) => item.attributes.category === "BOTTOM");

        const possiblePairs = Math.min(topItems.length, bottomItems.length);

        return {
            isValid: possiblePairs >= 3,
        };
    };

    const handleNavigation = async (path) => {
        // 기존 사용자 내 옷장 -> 추가하기시에는 하나만 있으면 등록
        const userId = localStorage.getItem("userId");

        if (userId && waitlistItems.length !== 0) {
            setIsRegistering(true);
            await registerNewClosetItems(waitlistItems, userId);
            navigate(path);
            return;
        } else if (userId && waitlistItems.length === 0) {
            alert("옷을 추가해주세요.");
            return;
        }

        // '이전' 버튼은 유효성 검사 없이 이동
        if (path === "/set-profile") {
            navigate(path);
            return;
        }

        // '다음' 또는 '추가하기' 버튼은 유효성 검사 후 이동
        const { isValid } = checkClothingRequirements();

        if (isValid) {
            try {
                // 로딩 상태 시작
                setIsRegistering(true);
                // 백엔드로 프로필 및 의류 정보 전송
                const userId = await registerUserWithCloset(profile, waitlistItems);
                // 등록 완료 시 로컬 스토리지에 사용자 UUID 저장
                localStorage.setItem("userId", userId);
                // 등록 완료 후 완료 페이지로 이동
                navigate(path);
            } catch (error) {
                console.error("등록 중 오류 발생:", error);
                alert("등록 중 오류가 발생했습니다. 다시 시도해 주세요.");
            } finally {
                setIsRegistering(false);
            }
        } else {
            alert("스타일 제안을 위해 상의 3개와 하의 3개 이상 등록해 주세요.");
        }
    };

    return (
        <div className='bg-[#F7F7F7] flex flex-col min-h-screen overflow-x-hidden relative'>
            {isAnalysisInProgress && (
                <div className='absolute top-0 left-0 right-0 bottom-0 backdrop-blur-sm bg-white/60 flex flex-col items-center justify-center z-20 rounded-xl'>
                    {/* <ClipLoader color='#8B5CF6' size={50} /> */}
                    <RingLoader color='#000' size={50} />
                    <p className='mt-3 font-medium text-zinc-700'>의상 분석 중...</p>
                </div>
            )}

            {/* 전체 화면 로딩 오버레이 - 등록 중일 때만 표시 */}
            {isRegistering && (
                <div className='absolute top-0 left-0 right-0 bottom-0 backdrop-blur-sm bg-white/60 flex flex-col items-center justify-center z-20 rounded-xl'>
                    <RingLoader color='#000' size={50} />
                    <p className='mt-3 font-medium text-zinc-700'>의상 등록 중...</p>
                </div>
            )}

            <Header />

            <main className='mb-max-w-4xl mx-auto flex flex-col w-full flex-1 mt-[7.5rem]'>
                {/* 헤더 밑부분 영역 - props에 따라 조건부 렌더링 */}
                <div>
                    <h1 className={`text-[2rem] font-bold text-center text-black`}>{title}</h1>
                    {showProgress && <ProgressBar activeStep={2} />}
                </div>

                <div className='mt-[4.375rem]'></div>
                {/* 옷 등록 영역 - 단일 컨테이너로 구성 */}
                <div className='bg-white shadow-lg rounded-xl pt-8 max-sm:w-[25rem] sm:w-[30rem] md:w-[45rem] 2xl:w-1/2 mx-auto transition-all duration-500 ease-in-out '>
                    {/* 이미지 분석 중 로딩 오버레이 */}

                    {/* 내용 영역: 이미지 업로더와 속성 선택기를 포함한 그리드 */}
                    <div className='addCloset-main__div grid grid-cols-1 md:grid-cols-2 sm:gap-15 xl:gap-35 lg:gap-20 items-stretch'>
                        {/* 왼쪽: 이미지 업로더 */}
                        <div className='flex justify-center md:justify-end max-sm:mb-8 mb-8 md:mb-0'>
                            <div className='max-w-xs'>
                                <ImageUploader
                                    ref={imageUploaderRef}
                                    uploadedImage={uploadedImage}
                                    onImageUpload={handleImageUpload}
                                    onImageRemove={handleImageRemove}
                                />
                            </div>
                        </div>

                        {/* 오른쪽: 속성 선택기 */}
                        <div className='flex flex-col justify-center sm:items-center max-sm:items-center md:items-start'>
                            <AttributeSelectors attributes={attributes} onAttributeChange={handleAttributeChange} isAnalyzed={isAnalyzed} />
                        </div>
                    </div>

                    {/* "대기 목록에 추가하기" 버튼 - 가운데 배치 */}
                    <div className='flex justify-center'>
                        <button
                            type='button'
                            onClick={handleAddToWaitlist}
                            disabled={isAnalysisInProgress || !uploadedImage}
                            className='w-[200px] h-[2.8125rem] text-[1rem] bg-black hover:bg-gray-800 mb-8 mt-8 text-white font-semibold py-2 px-4 rounded-md  
                            disabled:bg-gray-300 disabled:text-gray-500 disabled:cursor-not-allowed cursor-pointer
                            transition-colors duration-150 ease-in-out'
                        >
                            {isAnalysisInProgress ? "분석 중..." : "대기 목록에 추가하기"}
                        </button>
                    </div>
                </div>
                {/* 대기 목록 제목 */}
                <div
                    className='flex items-center justify-center my-6 cursor-pointer group py-2 px-4 rounded-lg transition-all duration-200'
                    onClick={() => setIsWaitlistExpanded(!isWaitlistExpanded)}
                >
                    <h2 className='text-base font-semibold text-gray-700 mr-2 hover:bg-gray-100  group-hover:text-black transition-colors duration-200'>
                        대기 목록 ({waitlistItems.length})
                    </h2>
                    {/* 화살표 SVG 아이콘 - 토글 상태에 따라 회전 */}
                    <svg
                        className={`w-5 h-5 text-gray-700 group-hover:text-black transition-all duration-300 ease-in-out transform ${
                            isWaitlistExpanded ? "rotate-180" : "rotate-0"
                        }`}
                        fill='none'
                        stroke='currentColor'
                        viewBox='0 0 24 24'
                        xmlns='http://www.w3.org/2000/svg'
                    >
                        <path strokeLinecap='round' strokeLinejoin='round' strokeWidth='2' d='M19 9l-7 7-7-7'></path>
                    </svg>
                </div>
                {/* 대기 목록 표시 영역 - 토글 상태에 따라 표시/숨김 */}
                <div
                    className={`max-sm:w-[25rem] sm:w-[30rem] md:w-[45rem] 2xl:w-1/2 mx-auto bg-white shadow-lg rounded-xl flex items-start justify-center overflow-hidden transition-all duration-500 ease-in-out ${
                        isWaitlistExpanded
                            ? `opacity-100 pt-8 pb-8 ${waitlistItems.length > 8 ? "max-h-[420px]" : ""}`
                            : "max-h-0 opacity-0 mb-0 pt-0 pb-0 border-t-0 border-b-0"
                    }`}
                >
                    <div className='w-full h-full flex-1 px-2'>
                        <Waitlist items={waitlistItems} onRemoveItem={handleRemoveFromWaitlist} />
                    </div>
                </div>
                {/* 하단 네비게이션 버튼 - showProgress에 따라 다른 버튼 표시 */}
                {showProgress ? (
                    <div className={`flex justify-center space-x-4 ${isWaitlistExpanded ? "my-6" : ""}`}>
                        <button
                            onClick={() => handleNavigation("/set-profile")}
                            className='h-[2.8125rem] text-[1rem] px-8 py-2 border border-[#828282] rounded text-xs font-medium text-black cursor-pointer hover:bg-gray-100 focus:outline-none flex items-center justify-center'
                        >
                            이전
                        </button>
                        <button
                            onClick={() => handleNavigation("/completion")}
                            className='h-[2.8125rem] text-[1rem] px-8 py-2 bg-black hover:bg-gray-800 text-white cursor-pointer rounded text-xs font-medium focus:outline-none flex items-center justify-center'
                        >
                            다음
                        </button>
                    </div>
                ) : (
                    <div className={`flex justify-center space-x-4 ${isWaitlistExpanded ? "my-6" : ""}`}>
                        <button
                            onClick={() => handleNavigation("/my-closet")}
                            className='h-[2.8125rem] text-[1rem] px-8 py-2 bg-black hover:bg-gray-800 text-white cursor-pointer rounded text-xs font-medium focus:outline-none flex items-center justify-center'
                        >
                            등록
                        </button>
                    </div>
                )}
            </main>
        </div>
    );
};

export default ClosetRegistrationPage;
