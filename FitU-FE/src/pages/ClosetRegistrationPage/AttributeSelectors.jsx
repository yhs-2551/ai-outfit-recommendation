import React from "react";
import Select from "react-select";
import { CLOTHING_CATEGORIES, CLOTHING_TYPES, PATTERN_TYPES, COLOR_TONES } from "../../constants/clothingAttributes";

const createSelectOptions = (optionsObj) =>
    Object.entries(optionsObj).map(([key, label]) => ({
        value: key, // 백엔드로 보낼 영문 키(TOP, BOTTOM 등)
        label: label, // 화면에 표시할 한글 값(상의, 하의 등)
    }));

// 객체 자체를 전달
const categorySelectOptions = createSelectOptions(CLOTHING_CATEGORIES);
const typeSelectOptions = createSelectOptions(CLOTHING_TYPES);
const patternSelectOptions = createSelectOptions(PATTERN_TYPES);
const toneSelectOptions = createSelectOptions(COLOR_TONES);

const AttributeSelectors = ({ attributes, onAttributeChange, isAnalyzed }) => {
    // 모든 드롭다운에 동일한 너비, 높이, 패딩, 폰트 크기 적용
    const commonLabelClasses = "text-xs font-medium text-gray-700 whitespace-nowrap pt-2.5 self-start w-16"; // 고정 너비 추가
    const dropdownContainerClasses = "flex-1 w-[160px] relative"; // 드롭다운 컨테이너 상대 위치 설정
    const groupClasses = "flex items-start space-x-3"; // 각 그룹에 공통 클래스 적용

    // React-Select 커스텀 스타일 정의
    const customStyles = {
        control: (provided, state) => ({
            ...provided,
            width: "100%",
            padding: "0.25rem 0",
            borderRadius: "0.375rem",
            borderColor: "#e5e7eb",
            boxShadow: "none",
            fontSize: "0.75rem",
            minHeight: "unset",
            textAlign: "center",
            cursor: "pointer",
            "&:hover": {
                borderColor: "#e5e7eb",
            },
        }),
        valueContainer: (provided) => ({
            ...provided,
            textAlign: "center",
            display: "flex",
            justifyContent: "center",
            padding: "2px 8px",
        }),
        singleValue: (provided) => ({
            ...provided,
            textAlign: "center",
            margin: "0 auto",
            fontSize: "0.75rem",
            color: "#374151",
        }),
        indicatorSeparator: () => ({
            display: "none",
        }),
        dropdownIndicator: (provided) => ({
            ...provided,
            color: "#9ca3af",
            padding: "0 8px",
            "&:hover": {
                color: "#9ca3af",
            },
        }),
        menu: (provided) => ({
            ...provided,
            borderRadius: "0.375rem",
            width: "100%",
            overflow: "hidden",
            zIndex: 10,
        }),
        menuList: (provided) => ({
            ...provided,
            padding: "0.25rem 0",
            maxHeight: "150px", // 드롭다운 리스트 최대 높이 제한
        }),
        option: (provided, state) => ({
            ...provided,
            fontSize: "0.75rem",
            textAlign: "center",
            cursor: "pointer",
            // 선택된 옵션의 배경색과 글자색
            backgroundColor: state.isFocused ? "black" : "white",
            color: state.isFocused ? "white" : "#374151",
            // 아래 부분이 드랍다운 옵션 호버 시 배경색 검정색, 글자색 흰색으로 변경
            "&:hover": {
                backgroundColor: "black",
                color: "white",
            },
        }),
        placeholder: (provided) => ({
            ...provided,
            fontSize: "0.75rem",
            color: "#9ca3af",
            textAlign: "center",
        }),
    };
  
    return (
        <div className='flex flex-col justify-center h-[12.5rem] max-sm:w-[13.75rem] w-[15rem] max-w-[15rem] space-y-5'>
            {/* 카테고리 & 종류 그룹 */}{" "}
            <div className={groupClasses}>
                <label htmlFor='category' className={commonLabelClasses}>
                    카테고리 <span className='text-red-500'>*</span>
                </label>
                <div className={`${dropdownContainerClasses} ${!isAnalyzed ? "cursor-not-allowed" : "cursor-pointer"}`}>
                    <Select
                        inputId='category'
                        name='category'
                        options={categorySelectOptions}
                        // value={
                        //     // 분석 전이면 null 표시, 분석 후에는 선택된 값 또는 null. 추후 AI 분석 후 주석 해제 예정
                        //     !isAnalyzed ? null : categorySelectOptions.find((opt) => opt.value === attributes.category) || null
                        // }
                        value={categorySelectOptions.find((opt) => opt.value === attributes.category) || null}
                        onChange={(selectedOption) => {
                            // 명시적으로 "분석 전"을 선택하면 undefined가 아닌 빈 문자열 저장
                            const value = selectedOption ? selectedOption.value : "";
                            onAttributeChange("category", value);
                        }}
                        styles={customStyles}
                        isSearchable={false}
                        placeholder={!isAnalyzed && "분석 전"}
                        isDisabled={!isAnalyzed} // 분석 전에는 비활성화 추후 AI 분석할 때때 주석 해제 예정
                    />
                </div>
            </div>
            {/* 상세 종류 그룹 */}
            <div className={`${groupClasses} ${!isAnalyzed ? "cursor-not-allowed" : "cursor-pointer"}`}>
                <div className={commonLabelClasses}>{/* 빈 div로 레이블 공간 확보 */}</div>
                <div className={dropdownContainerClasses}>
                    <Select
                        inputId='type'
                        name='type'
                        options={typeSelectOptions}
                        // 추후 AI 분석 후 주석 해제 예정
                        // value={
                        //     !isAnalyzed
                        //         ? { value: "분석 전", label: "분석 전" }
                        //         : typeSelectOptions.find((opt) => opt.value === attributes.type) || null
                        // }
                        value={typeSelectOptions.find((opt) => opt.value === attributes.type) || null}
                        onChange={(selectedOption) => onAttributeChange("type", selectedOption ? selectedOption.value : "")}
                        styles={customStyles}
                        isSearchable={false}
                        placeholder={!isAnalyzed && "분석 전"}
                        isDisabled={!isAnalyzed} // 분석 전에는 비활성화 추후 AI 분석할 때때 주석 해제 예정
                    />
                </div>
            </div>
            {/* 패턴 그룹 */}
            <div className={`${groupClasses} ${!isAnalyzed ? "cursor-not-allowed" : "cursor-pointer"}`}>
                <label htmlFor='pattern' className={commonLabelClasses}>
                    패턴 <span className='text-red-500'>*</span>
                </label>
                <div className={dropdownContainerClasses}>
                    <Select
                        inputId='pattern'
                        name='pattern'
                        options={patternSelectOptions}
                        // 추후 AI 분석 후 주석 해제 예정
                        // value={
                        //     !isAnalyzed
                        //         ? { value: "분석 전", label: "분석 전" }
                        //         : patternSelectOptions.find((opt) => opt.value === attributes.pattern) || null
                        // }
                        value={patternSelectOptions.find((opt) => opt.value === attributes.pattern) || null}
                        onChange={(selectedOption) => onAttributeChange("pattern", selectedOption ? selectedOption.value : "")}
                        styles={customStyles}
                        isSearchable={false}
                        placeholder={!isAnalyzed && "분석 전"}
                        isDisabled={!isAnalyzed} // 분석 전에는 비활성화 추후 AI 분석할 때때 주석 해제 예정
                    />
                </div>
            </div>
            {/* 톤 그룹 */}
            <div className={`${groupClasses} ${!isAnalyzed ? "cursor-not-allowed" : "cursor-pointer"}`}>
                <label htmlFor='tone' className={commonLabelClasses}>
                    톤 <span className='text-red-500'>*</span>
                </label>
                <div className={dropdownContainerClasses}>
                    <Select
                        inputId='tone'
                        name='tone'
                        options={toneSelectOptions}
                        // 추후 AI 분석 후 주석 해제 예정
                        // value={

                        //     !isAnalyzed
                        //         ? { value: "분석 전", label: "분석 전" }
                        //         : toneSelectOptions.find((opt) => opt.value === attributes.tone) || null
                        // }
                        value={toneSelectOptions.find((opt) => opt.value === attributes.tone) || null}
                        onChange={(selectedOption) => onAttributeChange("tone", selectedOption ? selectedOption.value : "")}
                        styles={customStyles}
                        isSearchable={false}
                        placeholder={!isAnalyzed && "분석 전"}
                        isDisabled={!isAnalyzed} // 분석 전에는 비활성화 추후 AI 분석할 때때 주석 해제 예정
                    />
                </div>
            </div>
        </div>
    );
};

export default AttributeSelectors;
