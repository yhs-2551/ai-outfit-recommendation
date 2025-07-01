import React, { useRef, useState, useEffect, useImperativeHandle, forwardRef } from "react";
import { PhotoIcon, XMarkIcon } from "@heroicons/react/24/solid";

const ImageUploader = forwardRef(({ uploadedImage, onImageUpload, onImageRemove, isAnalyzing }, ref) => {
    const fileInputRef = useRef(null);
    const [isDragging, setIsDragging] = useState(false);

    // 부모 컴포넌트에서 접근할 수 있는 메소드 노출
    useImperativeHandle(ref, () => ({
        resetFileInput: () => {
            if (fileInputRef.current) {
                fileInputRef.current.value = "";
            }
        },
    }));

    const handleFileChange = async (event) => {
        if (event.target.files && event.target.files[0]) {
            const file = event.target.files[0];
            // 이미 있는 URL이 있으면 해제
            if (uploadedImage?.preview) {
                URL.revokeObjectURL(uploadedImage.preview);
            }
            const previewUrl = URL.createObjectURL(file);
            onImageUpload(file, previewUrl);
        }
    };

    const handleBoxClick = () => {
        if (!uploadedImage && !isAnalyzing) {
            fileInputRef.current?.click();
        }
    };

    const handleRemoveClick = (e) => {
        e.stopPropagation();
        onImageRemove();
        // 파일 입력 엘리먼트 초기화
        //(같은 파일을 다시 선택할 수 있도록, 즉 이미지를 삭제할 때 파일 입력(input) 값을 초기화하여 같은 파일이 다시 선택되어도 변경 이벤트가 발생)
        if (fileInputRef.current) {
            fileInputRef.current.value = "";
        }
    };

    // 드래그 앤 드롭 기능
    const handleDragEnter = (e) => {
        e.preventDefault();
        e.stopPropagation();
        if (!uploadedImage && !isAnalyzing) setIsDragging(true);
    };

    const handleDragLeave = (e) => {
        e.preventDefault();
        e.stopPropagation();
        setIsDragging(false);
    };

    const handleDragOver = (e) => {
        e.preventDefault();
        e.stopPropagation();
        if (!uploadedImage && !isAnalyzing && !isDragging) setIsDragging(true);
    };
    const handleDrop = async (e) => {
        e.preventDefault();
        e.stopPropagation();
        setIsDragging(false);

        if (!uploadedImage && !isAnalyzing && e.dataTransfer.files && e.dataTransfer.files[0]) {
            const file = e.dataTransfer.files[0];
            // 이미 있는 URL이 있으면 해제 (handleFileChange와 동일하게 처리)
            if (uploadedImage?.preview) {
                URL.revokeObjectURL(uploadedImage.preview);
            }
            const previewUrl = URL.createObjectURL(file);
            onImageUpload(file, previewUrl);
            // AI 분석 시 isAnalyzing을 부모 컴포넌트에서 true로 설정
        }
    };

    return (
        <div
            className={`img-uploader-container relative h-[12.5rem] max-sm:w-[13.75rem] w-[15rem] border-2 border-dashed rounded-lg flex flex-col items-center justify-center text-center
                            ${
                                uploadedImage
                                    ? "border-gray-300 bg-white"
                                    : isDragging
                                    ? "border-black bg-gray-100"
                                    : "border-gray-400 bg-gray-50 hover:bg-gray-100 cursor-pointer"
                            }
                            ${isAnalyzing ? "cursor-wait" : ""}`}
            onClick={handleBoxClick}
            onDragEnter={handleDragEnter}
            onDragLeave={handleDragLeave}
            onDragOver={handleDragOver}
            onDrop={handleDrop}
        >
            <input type='file' accept='image/*' ref={fileInputRef} onChange={handleFileChange} className='hidden' disabled={isAnalyzing} />

            {uploadedImage ? (
                <>
                    <div className='w-full h-full relative'>
                        <img
                            src={uploadedImage.preview}
                            alt='업로드된 의상'
                            className='w-full h-full object-cover rounded-md'
                            style={{ objectFit: "contain", objectPosition: "center" }}
                        />
                    </div>

                    <button
                        type='button'
                        onClick={handleRemoveClick}
                        className='absolute top-1.5 right-1.5 bg-black text-white rounded-full p-1 hover:bg-gray-700 focus:outline-none'
                        aria-label='이미지 삭제'
                        disabled={isAnalyzing}
                    >
                        {/* 추후 AI분석 중에 X ICon 비활성화 시각적 효과 확인 필요  */}
                        <XMarkIcon className={`w-4 h-4 ${isAnalyzing ? "text-gray-400 cursor-not-allowed" : "cursor-pointer"}`} />
                    </button>
                </>
            ) : (
                <>
                    <PhotoIcon className='w-10 h-10 text-gray-400 mb-2' />
                    {/* <p className='text-xs text-gray-600 font-medium mb-1'>의상 이미지 업로드</p> */}
                    <p className='text-[10.5px] text-gray-500 leading-tight mb-2'>
                        클릭 또는 의상 이미지를 여기로 끌어오면
                        <br />
                        AI가 자동으로 분석해요.
                    </p>
                    {/* <div className='w-24 h-6 bg-gray-100 rounded-md flex items-center justify-center text-[10px] text-gray-500 border border-gray-300'>
                        파일 선택
                    </div> */}
                </>
            )}
        </div>
    );
});

export default ImageUploader;
