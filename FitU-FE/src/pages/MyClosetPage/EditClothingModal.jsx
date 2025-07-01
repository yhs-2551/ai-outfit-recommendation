import React, { useState, useRef, useEffect } from "react";
import { XMarkIcon } from "@heroicons/react/24/outline"; // X 아이콘 가져오기
import ImageUploader from "../ClosetRegistrationPage/ImageUploader";
import AttributeSelectors from "../ClosetRegistrationPage/AttributeSelectors";
import { analyzeClothingImage } from "../../api/clothesAPI";
import { RingLoader } from "react-spinners";

const EditClothingModal = ({ isOpen, onClose, clothingData, onSave }) => {
    const [uploadedImage, setUploadedImage] = useState(null);
    const [attributes, setAttributes] = useState({
        category: "",
        type: "",
        pattern: "",
        tone: "",
    });
    const [isAnalyzed, setIsAnalyzed] = useState(true); // 수정 시에는 이미 분석된 상태
    const [isAnalysisSuccess, setIsAnalysisSuccess] = useState(true);
    const [isAnalysisInProgress, setIsAnalysisInProgress] = useState(false);

    const imageUploaderRef = useRef(null);

    // 모달이 열릴 때 기존 데이터 로드
    useEffect(() => {
        if (isOpen && clothingData) {
            // 기존 이미지 설정
            setUploadedImage({
                file: null, // 파일 객체는 없지만
                preview: clothingData.imageUrl, // 초기 모달에 접근 시 추후 aws URL 사용 예정
            });

            // 기존 속성 설정
            setAttributes({
                category: clothingData.tags[1] || "",
                type: clothingData.tags[0] || "",
                pattern: clothingData.tags[2] || "",
                tone: clothingData.tags[3] || "",
            });
        }
    }, [isOpen, clothingData]);

    const handleImageUpload = async (file, preview) => {
        setUploadedImage({ file, preview });
        setIsAnalyzed(false); // 새 이미지 업로드 시 분석 상태 초기화
        setIsAnalysisInProgress(true); // 버튼에 분석 중 상태 표시
        try {
            // 이미지 분석 API 호출
            const result = await analyzeClothingImage(file);

            // 분석 결과로 속성 업데이트, 분석에 성공하면 분석 결과 url만 존재
            if (result) {

                setIsAnalysisSuccess(true);

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
        setIsAnalyzed(false);
        setUploadedImage(null);
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

    const handleSave = () => {
 
        // 수정시에도 모든 데이터가 필수
        onSave({
            id: clothingData.id,
            prevImage: isAnalysisSuccess ? uploadedImage?.preview : null,
            newImage: !isAnalysisSuccess ? uploadedImage?.file : null,
            tags: [
                { type: "category", value: attributes.category },
                { type: "type", value: attributes.type },
                { type: "pattern", value: attributes.pattern },
                { type: "tone", value: attributes.tone },
            ].filter((tag) => tag.value), // 빈 값 필터링은 일단 보류
        });
    };

    if (!isOpen) return null;

    return (
        <div className='edit-modal-container fixed inset-0 bg-gray-500/75 transition-opacity z-40 flex items-center justify-center p-4 backdrop-blur-[2px]'>
            {isAnalysisInProgress && (
                <div className='absolute top-0 left-0 right-0 bottom-0 backdrop-blur-sm bg-white/60 flex flex-col items-center justify-center z-20 rounded-xl'>
                    <RingLoader color='#6366F1' size={50} />
                    <p className='mt-3 font-medium text-zinc-700'>의상 분석 중...</p>
                </div>
            )}
            <div className='edit-modal-container__div bg-white rounded-xl shadow-xl w-full max-w-3xl h-[31.25rem] overflow-y-auto flex '>
                <div className='p-6 flex flex-col flex-grow'>
                    {/* 헤더 영역 */}
                    <div className='flex items-center justify-center relative mb-6'>
                        <h2 className='text-2xl font-bold text-center'>의상 수정</h2>
                        <button onClick={onClose} className='absolute right-0 top-0 text-gray-500 hover:text-black cursor-pointer' aria-label='닫기'>
                            <XMarkIcon className='h-6 w-6' />
                        </button>
                    </div>
                    <div className='edit-modal-container__text text-center'>
                        <p>이미지 또는 의상 속성을 변경할 수 있습니다.</p>
                        <p>AI 분석 결과는 이미지를 변경할 경우 재분석될 수 있습니다.</p>
                    </div>

                    <div className='flex flex-col md:flex-row items-center justify-center flex-grow'>
                        {/* 이미지 업로더 - 왼쪽 */}
                        <div className='edit-modal-imgUploader-container w-full md:w-5/12 flex justify-start items-center'>
                            <ImageUploader
                                ref={imageUploaderRef}
                                uploadedImage={uploadedImage}
                                onImageUpload={handleImageUpload}
                                onImageRemove={handleImageRemove}
                            />
                        </div>

                        {/* 속성 선택기 - 오른쪽 */}
                        <div className=''>
                            <AttributeSelectors attributes={attributes} onAttributeChange={handleAttributeChange} isAnalyzed={isAnalyzed} />
                        </div>
                    </div>

                    {/* 버튼 영역 */}
                    <div className='edit-modal__btn flex justify-center space-x-4 '>
                        <button
                            onClick={onClose}
                            className='px-6 py-2.5  border border-[#828282]rounded text-sm font-medium cursor-pointer hover:bg-gray-100'
                        >
                            취소
                        </button>
                        <button
                            onClick={handleSave}
                            disabled={!isAnalyzed}
                            className='px-6 py-2.5 bg-black text-white rounded text-sm font-medium cursor-pointer hover:bg-gray-800 disabled:opacity-50 disabled:cursor-not-allowed'
                        >
                            저장
                        </button>
                    </div>
                </div>
            </div>
        </div>
    );
};

export default EditClothingModal;
