import React from "react";
import { XMarkIcon } from "@heroicons/react/24/solid";
import { CLOTHING_CATEGORIES, CLOTHING_TYPES, PATTERN_TYPES, COLOR_TONES } from "../../constants/clothingAttributes";

const WaitlistItem = ({ item, onRemove }) => {
    // 키로부터 한글 레이블 가져오기
    const getLabelFromKey = (type, key) => {
        const categoryMap = {
            category: CLOTHING_CATEGORIES,
            type: CLOTHING_TYPES,
            pattern: PATTERN_TYPES,
            tone: COLOR_TONES,
        };

        return categoryMap[type]?.[key] || key;
    };

    // 속성 키-값 쌍을 한글 레이블로 변환
    const attributeLabels = Object.entries(item.attributes)
        .filter(([_, value]) => value) // 빈 값 제외
        .map(([type, key]) => getLabelFromKey(type, key)); // 키를 해당 타입의 한글 레이블로 변환
 
     return (
        <div className='relative border border-gray-300 rounded-lg overflow-hidden flex flex-col bg-white w-full h-[180px] shadow-sm'>
            {/* 삭제 버튼 */}
            <button
                type='button'
                onClick={() => onRemove(item.id)}
                className='absolute top-1 right-1 bg-black bg-opacity-70 text-white rounded-full p-0.5 hover:bg-gray-700 focus:outline-none z-10'
                aria-label='목록에서 삭제'
            >
                <XMarkIcon className='w-3.5 h-3.5 cursor-pointer' />
            </button>

            {/* 이미지 영역 (70%) */}
            <div className='w-full h-[70%] overflow-hidden'>
                <img src={item.s3Url || item.image} alt='의류 이미지' className='w-full h-full object-contain' />
            </div>

            {/* 구분선 */}
            <div className='w-full h-[1px] bg-gray-200'></div>

            {/* 태그 영역 (30%) */}
            <div className='flex flex-wrap gap-1 p-1.5 justify-center items-center h-[30%] bg-gray-50'>
                {attributeLabels.map((label, index) => (
                    <span key={index} className='px-2 py-0.5 bg-black text-white text-[9px] rounded-full whitespace-nowrap'>
                        {label}
                    </span>
                ))}
            </div>
        </div>
    );
};

export default WaitlistItem;
