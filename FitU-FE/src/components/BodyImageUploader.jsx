import React, { useRef, useState, useImperativeHandle, forwardRef } from "react";

const BodyImageUploader = forwardRef(({ uploadedImage, onImageUpload, onImageRemove, isAnalyzing }, ref) => {
    const fileInputRef = useRef(null);

    useImperativeHandle(ref, () => ({
        resetFileInput: () => {
            if (fileInputRef.current) {
                fileInputRef.current.value = "";
            }
        },
    }));

    const handleFileChange = (event) => {
        if (event.target.files && event.target.files[0]) {
            const file = event.target.files[0];

            if (uploadedImage?.preview) {
                URL.revokeObjectURL(uploadedImage.preview);
            }
            const previewUrl = URL.createObjectURL(file);
            onImageUpload(file, previewUrl);
        }
    };

    const handleRemoveClick = (e) => {
        e.stopPropagation();

        onImageRemove();

        if (fileInputRef.current) {
            fileInputRef.current.value = "";
        }
    };

    const handleDrop = async (e) => {
        e.preventDefault();
        e.stopPropagation();

        if (uploadedImage || isAnalyzing) return;

        if (!uploadedImage && !isAnalyzing && e.dataTransfer.files && e.dataTransfer.files[0]) {
            const file = e.dataTransfer.files[0];

            if (!file) return;

            if (!file.type.startsWith('image/')) {
                alert('이미지 파일만 업로드할 수 있습니다.');
                return;
            }

            if (uploadedImage?.preview) {
                URL.revokeObjectURL(uploadedImage.preview);
            }

            const previewUrl = URL.createObjectURL(file);

            onImageUpload(file, previewUrl);
            
            // AI 분석 시 isAnalyzing을 부모 컴포넌트에서 true로 설정
        }
    };

    return (
        <div className="flex items-center justify-center w-full relative">
            <label
                htmlFor="dropzone-file"
                className={`flex flex-col items-center justify-center w-[13.375rem] h-[17.8125rem] border-1 border-gray-300 border-dashed rounded-lg bg-white
                    ${uploadedImage ? "" : "hover:bg-gray-100"}`}
                onDragOver={uploadedImage ? undefined : (e) => e.preventDefault()}
                onDrop={uploadedImage ? undefined : handleDrop}
            >
                {uploadedImage ? (
                    <div className='w-full h-full relative'>
                        <img
                            src={uploadedImage.preview}
                            alt='미리보기'
                            className='w-full h-full object-contain rounded-md'
                            style={{ objectFit: "contain", objectPosition: "center" }}
                        />

                        <button
                            type="button"
                            tabIndex={-1}
                            className="absolute top-2 right-2 bg-black bg-opacity-70 font-bold text-white border-white rounded-full p-1 hover:bg-white hover:text-black hover:border-black focus:outline-none transition-colors duration-200"
                            onClick={e => {
                                e.preventDefault();
                                e.stopPropagation();
                                if (window.confirm("전신 사진을 삭제하시겠습니까?")) {
                                    handleRemoveClick(e);
                                }
                            }}
                            aria-label="이미지 삭제"
                        >
                            <svg className="w-4 h-4" fill="none" stroke="currentColor" strokeWidth="2" viewBox="0 0 24 24">
                                <path strokeLinecap="round" strokeLinejoin="round" d="M6 18L18 6M6 6l12 12" />
                            </svg>
                        </button>
                    </div>
                ) : (
                    <div className="flex flex-col items-center justify-center pt-5 pb-6 cursor-pointer">
                        <svg className="w-8 h-8 mb-4 text-[#828282] " aria-hidden="true" xmlns="http://www.w3.org/2000/svg" fill="none" viewBox="0 0 20 16">
                            <path stroke="currentColor" strokeLinecap="round" strokeLinejoin="round" strokeWidth="2" d="M13 13h3a3 3 0 0 0 0-6h-.025A5.56 5.56 0 0 0 16 6.5 5.5 5.5 0 0 0 5.207 5.021C5.137 5.017 5.071 5 5 5a4 4 0 0 0 0 8h2.167M10 15V6m0 0L8 8m2-2 2 2" />
                        </svg>
                        {/* TODO 이미지 파일 용량 제한 문구 출력 */}
                        <p className="mb-2 text-[#828282] text-center">
                            <span className="font-semibold text-[16px]">[선택] 전신 사진 업로드</span><br />
                            <span className="font-base text-[12px]">클릭하거나 이미지를 끌어다 놓으세요</span>
                        </p>
                    </div>
                )}

                <input
                    id="dropzone-file"
                    type="file"
                    className="hidden"
                    accept="image/*"
                    ref={fileInputRef}
                    name="file"
                    disabled={isAnalyzing || !!uploadedImage}
                    onChange={handleFileChange}
                />
            </label>
        </div>
    );
});

export default BodyImageUploader;