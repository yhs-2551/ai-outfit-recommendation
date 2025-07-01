import "./MyClosetPage.styles.css";

import React, { useState, useEffect, useCallback } from "react";
import { Link, useNavigate } from "react-router-dom";
import { ClipLoader } from "react-spinners";
import debounce from "lodash/debounce";

import ClosetFilter from "./ClosetFilter";
import ClosetItemCard from "./ClosetItemCard";
import { PlusIcon } from "@heroicons/react/20/solid";
import EditClothingModal from "./EditClothingModal";
import Header from "../../components/Header";
import { deleteClothesItem, fetchClosetItems, fetchFilteredClothes, updateClothesItem } from "../../api/clothesAPI";
import { set } from "lodash";
import { CLOTHING_CATEGORIES, CLOTHING_TYPES, COLOR_TONES, PATTERN_TYPES } from "../../constants/clothingAttributes";

const MyClosetPage = () => {
    const [closetItems, setClosetItems] = useState([]);

    const [filters, setFilters] = useState({});
    const [isLoading, setIsLoading] = useState(true);

    // 수정 모달 관련 상태
    const [isEditModalOpen, setIsEditModalOpen] = useState(false);
    const [currentEditItem, setCurrentEditItem] = useState(null);

    const navigate = useNavigate();

    useEffect(() => {
        const getClosetItems = async () => {
            try {
                // 로컬 스토리지에서 userId(UUDI)를 가져온다.
                const userId = localStorage.getItem("userId");

                if (!userId) {
                    alert("사용자 정보가 없습니다. 프로필을 설정해주세요.");
                    navigate("/set-profile"); // userId가 없으면 프로필 설정 페이지로 이동
                }

                setIsLoading(true);

                const response = await fetchClosetItems(userId);

                if (response) {
                    // 백엔드 응답 구조에 맞게 데이터 변환
                    const formattedItems = response.map((item) => ({
                        id: item.clothesId,
                        imageUrl: item.clothesImageUrl,
                        tags: [item.category, item.type, item.pattern, item.color].filter(Boolean), // null/undefined 제거
                    }));

                    setClosetItems(formattedItems);
                } else {
                    setClosetItems([]);
                }
            } catch (e) {
                console.error("옷장 데이터를 가져오는데 실패했습니다:", e);
                alert("옷장 정보를 불러오는 중 오류가 발생했습니다. 다시 시도해주세요.");
                setClosetItems([]);
            } finally {
                setIsLoading(false);
            }
        };

        getClosetItems();
    }, []);

    // 태그 영어 -> 한글 변환, 카테고리, 타입 위치 변경
    const translateTag = (tag, index) => {
        if (!tag) return null;

        if (index === 1) {
            return CLOTHING_CATEGORIES[tag] || tag;
        } else if (index === 0) {
            return CLOTHING_TYPES[tag] || tag;
        } else if (index === 2) {
            return PATTERN_TYPES[tag] || tag;
        }
        // index 3: color
        else if (index === 3) {
            return COLOR_TONES[tag] || tag;
        }

        return tag;
    };

    const debouncedFilter = debounce(async (newFilters) => {
        const userId = localStorage.getItem("userId");

        try {
            const response = await fetchFilteredClothes(userId, newFilters);
            if (response) {
                const formattedItems = response.map((item) => ({
                    id: item.clothesId,
                    imageUrl: item.clothesImageUrl,
                    tags: [item.category, item.type, item.pattern, item.color].filter(Boolean),
                }));

                setClosetItems(formattedItems);
            } else {
                setClosetItems([]);
            }
        } catch (error) {
            console.error("필터링된 옷장 아이템을 가져오기 실패", error);
            alert("필터링된 옷장 정보를 불러오는 중 오류가 발생했습니다. 다시 시도해주세요.");
        }
    }, 300);

    const handleFilterChange = (filterName, value) => {
        let newFilters;

        if (filterName === "allFilters") {
            // allFilters 타입으로 모든 필터가 한 번에 전달된 경우
            newFilters = value;
        } else {
            // 기존처럼 개별 필터가 전달된 경우
            newFilters = {
                ...filters,
                [filterName]: value,
            };
        }

        setFilters(newFilters);
        debouncedFilter(newFilters);
    };

    const handleEditItem = (itemId) => {
        const itemToEdit = closetItems.find((item) => item.id === itemId);

        setCurrentEditItem(itemToEdit);
        setIsEditModalOpen(true);
    };

    const handleSaveEdit = async (editedItem) => {
        try {
            const hasImage = editedItem.prevImage || editedItem.newImage;

            // 이미지가 없을 경우 경고
            if (!hasImage) {
                alert("의류 이미지는 필수입니다. 이미지를 업로드해주세요.");
                return;
            }

            //  태그 속성 검사 (모든 태그가 값을 가지고 있어야 함)
            if (!editedItem.tags || editedItem.tags.length < 4) {
                alert("모든 의류 속성(카테고리, 패턴, 톤)을 입력해주세요.");
                return;
            }

            const userId = localStorage.getItem("userId");

            const updateData = {
                prevImage: editedItem.prevImage,
                newImage: editedItem.newImage,
                category: editedItem.tags[0].value,
                type: editedItem.tags[1].value,
                pattern: editedItem.tags[2].value,
                tone: editedItem.tags[3].value,
            };

            const response = await updateClothesItem(userId, editedItem.id, updateData);

            if (response) {
                alert("의류 정보가 성공적으로 수정되었습니다.");

                setIsEditModalOpen(false);
                setCurrentEditItem(null);

                // 상태 업데이트
                setClosetItems((prevItems) =>
                    prevItems.map((item) =>
                        item.id === editedItem.id
                            ? {
                                  ...item,
                                  imageUrl: response.clothesImageUrl || item.imageUrl,
                                  tags: [response.category, response.type, response.pattern, response.color].filter(Boolean),
                              }
                            : item
                    )
                );
            }
        } catch (error) {
            console.error("의류 수정 중 오류 발생:", error);
            alert("의류 수정에 실패했습니다. 다시 시도해주세요.");
        }
    };

    const handleDeleteItem = async (itemId) => {
        if (window.confirm("정말로 이 의류를 삭제하시겠습니까?")) {
            try {
                const userId = localStorage.getItem("userId");
                await deleteClothesItem(userId, itemId);
                setClosetItems((prevItems) => prevItems.filter((item) => item.id !== itemId));
                alert("의류가 성공적으로 삭제되었습니다.");
            } catch (error) {
                console.error("의류 삭제 중 오류 발생:", error);
                alert("의류 삭제에 실패했습니다. 다시 시도해주세요.");
            }
        }
    };

    return (
        <div className='min-h-screen bg-[#F7F7F7]'>
            <Header />

            <main className='myCloset-main xl:max-w-7xl mx-auto flex flex-col'>
                <div className='mb-4 w-full'>
                    <h1 className='text-[2rem] font-bold text-center text-black mb-[4.375rem] mt-[7.5rem]'>내 옷장😊</h1>
                    {/* 필터와 옷 추가하기 */}
                    <div className='myCloset-main__div flex flex-col sm:flex-row justify-between items-center sm:space-x-4'>
                        {/* 필터는 왼쪽에 */}
                        <div className='w-full sm:w-auto mb-4 sm:mb-0'>
                            <ClosetFilter onFilterChange={handleFilterChange} />
                        </div>
                        {/* 옷 추가하기 버튼은 오른쪽에 */}

                        <Link
                            to='/closet-add'
                            className='flex items-center bg-black text-white  h-[2.5rem] text-[1rem] font-semibold px-3 py-2 rounded-md hover:bg-gray-800 transition-colors whitespace-nowrap cursor-pointer'
                        >
                            <PlusIcon className='w-4 h-4 mr-1 fill-white stroke-white' />옷 추가하기
                        </Link>
                    </div>
                </div>

                {/* 옷 목록, 조회 시 ClipLoader 대신 다른걸로 변경 고려*/}
                {isLoading ? (
                    <div className='flex justify-center items-center p-12'>
                        <ClipLoader color='#666666' size={50} />
                    </div>
                ) : closetItems.length > 0 ? (
                    <div className='bg-white p-4 sm:p-6 shadow-lg rounded-xl w-full'>
                        {/* 카드의 높이를 일정하게 유지하기 위해 grid에 aspect-ratio 또는 고정 높이 설정 */}
                        <div className='grid grid-cols-2 sm:grid-cols-3 md:grid-cols-4 lg:grid-cols-5 gap-4'>
                            {closetItems.map((item) => (
                                // 각 카드가 일정한 높이를 갖도록 aspect-ratio 클래스 추가
                                <div key={item.id} className='aspect-[3/4] sm:aspect-[4/5]'>
                                    <ClosetItemCard
                                        imageUrl={item.imageUrl}
                                        tags={[
                                            translateTag(item.tags[1], 1), // 카테고리 먼저
                                            translateTag(item.tags[0], 0), // 그 다음 타입
                                            translateTag(item.tags[2], 2), // 패턴
                                            translateTag(item.tags[3], 3), // 색상
                                        ].filter(Boolean)}
                                        onEdit={() => handleEditItem(item.id)}
                                        onDelete={() => handleDeleteItem(item.id)}
                                    />
                                </div>
                            ))}
                        </div>
                    </div>
                ) : (
                    <div className='bg-white p-12 text-center text-gray-500 shadtow-lg rounded-xl'>
                        <p className='text-gray-500 text-lg mb-2'>옷장이 비어있습니다.</p>
                        <p className='text-gray-400 text-sm mb-4'>옷을 추가하여 나만의 옷장을 채워보세요!</p>
                    </div>
                )}
            </main>

            {/* 수정 모달  */}
            <EditClothingModal
                isOpen={isEditModalOpen}
                onClose={() => setIsEditModalOpen(false)}
                clothingData={currentEditItem}
                onSave={handleSaveEdit}
            />
        </div>
    );
};

export default MyClosetPage;
