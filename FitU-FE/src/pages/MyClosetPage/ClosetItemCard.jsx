import React, { useState, useRef, useEffect } from "react";
import { PencilIcon, TrashIcon } from "@heroicons/react/24/solid";

const ClosetItemCard = ({ imageUrl, tags = [], onEdit, onDelete }) => {
    const [showMenu, setShowMenu] = useState(false);
    const menuRef = useRef(null);
    const buttonRef = useRef(null);

    const displayTags = tags.slice(0, 4);
 
    // 외부 클릭 감지를 위한 이벤트 리스너
    useEffect(() => {
        function handleClickOutside(event) {
            // 메뉴가 열려있고, 클릭이 메뉴 외부 및 버튼 외부에서 발생한 경우 메뉴 닫기
            if (
                showMenu &&
                menuRef.current &&
                !menuRef.current.contains(event.target) &&
                buttonRef.current &&
                !buttonRef.current.contains(event.target)
            ) {
                setShowMenu(false);
            }
        }

        // 이벤트 리스너 추가
        document.addEventListener("mousedown", handleClickOutside);

        // 컴포넌트가 언마운트될 때 이벤트 리스너 제거
        return () => {
            document.removeEventListener("mousedown", handleClickOutside);
        };
    }, [showMenu]);

    return (
        <div className='relative border border-gray-200 rounded-lg bg-white shadow-sm hover:shadow-md transition-shadow flex flex-col overflow-hidden h-full'>
            <button
                ref={buttonRef}
                onClick={() => setShowMenu(!showMenu)}
                className='absolute top-2 right-2 bg-white bg-opacity-80 text-gray-700 hover:text-black p-1.5 rounded-full hover:bg-opacity-100 shadow-sm z-20  cursor-pointer'
                aria-label='옵션 더보기'
            >
                <PencilIcon className='w-4 h-4' />
            </button>
            {/* 수정/삭제 드롭다운 메뉴 */}
            {showMenu && (
                <div ref={menuRef} className='absolute top-8 right-2 mt-1 w-32 bg-white rounded-md shadow-lg py-1 z-20 border border-gray-200'>
                    <button
                        onClick={() => {
                            onEdit();
                            setShowMenu(false);
                        }}
                        className='w-full text-left px-3 py-1.5 text-xs text-gray-700 hover:bg-gray-100 flex items-center cursor-pointer'
                    >
                        <PencilIcon className='w-3.5 h-3.5 mr-2 text-gray-500' />
                        의상 수정
                    </button>
                    <button
                        onClick={() => {
                            onDelete();
                            setShowMenu(false);
                        }}
                        className='w-full text-left px-3 py-1.5 text-xs text-gray-700 hover:bg-gray-100  flex items-center  cursor-pointer'
                    >
                        <TrashIcon className='w-3.5 h-3.5 mr-2 text-gray-500' />
                        의상 삭제
                    </button>
                </div>
            )}
            <div className='flex flex-col h-full'>
                <div className='w-full relative bg-gray-100' style={{ height: "70%" }}>
                    {/* 높이 70% */}
                    <img
                        src={imageUrl || "https://via.placeholder.com/200/f0f0f0/cccccc?text=No+Image"}
                        alt='옷 이미지'
                        className='absolute inset-0 w-full h-full object-contain p-1'
                    />
                </div>
                {/* 태그 영역 - 나머지 공간(30%) 차지 */}
                <div className='flex-grow flex flex-wrap gap-1 justify-center items-center p-2 border-t border-gray-100' style={{ minHeight: "30%" }}>
                    {displayTags.map((tag, index) => (
                        <span key={index} className='px-2 py-0.5 bg-black text-white text-[10.5px] leading-tight rounded-full'>
                            {tag}
                        </span>
                    ))}
                </div>
            </div>
        </div>
    );
};

export default ClosetItemCard;
