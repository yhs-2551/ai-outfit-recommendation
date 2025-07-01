import React, { useState } from "react";
import { UNSAFE_SingleFetchRedirectSymbol, useNavigate } from "react-router-dom";
import Header from "../../components/Header";
import { recommendOutfit } from "../../api/recommendationAPI";
import { RingLoader } from "react-spinners";

const SetSituationPage = () => {
  const navigate = useNavigate();

  const [formData, setFormData] = useState({
    occasion: "",
    time: "",
    place: "",
    onlyCloset: true,
  });

  const [errors, setErrors] = useState({});
  const [isLoading, setIsLoading] = useState(false);

  const handleChange = (e) => {
    const { name, value, type, checked } = e.target;
    setFormData((prevData) => ({
      ...prevData,
      [name]: type === "checkbox" ? checked : value,
    }));
  };

  const validateForm = () => {
    let newErrors = {};
    const today = new Date();
    today.setHours(0, 0, 0, 0);

    if (!formData.occasion.trim()) {
      newErrors.occasion = "상황을 입력해주세요.";
    }

    if (!formData.time) {
      newErrors.time = "날짜를 선택해주세요.";
    } else {
      const selectedDate = new Date(formData.time);
      selectedDate.setHours(0, 0, 0, 0);

      const tenDaysFromNow = new Date(today);
      tenDaysFromNow.setDate(today.getDate() + 10);

      if (selectedDate < today) {
        newErrors.time = "오늘 이전의 날짜는 선택할 수 없습니다.";
      } else if (selectedDate > tenDaysFromNow) {
        newErrors.time = "오늘로부터 10일 이내의 날짜만 선택할 수 있습니다.";
      }
    }

    if (!formData.place.trim()) {
      newErrors.place = "장소를 입력해주세요.";
    }

    setErrors(newErrors);
    return Object.keys(newErrors).length === 0;
  };

  const handleSubmit = async (e) => {
    e.preventDefault();

    if (validateForm()) {
      setIsLoading(true);
      console.log("Form data is valid:", formData);

      const userId = localStorage.getItem("userId");
      const response = await recommendOutfit(userId, formData);

      setIsLoading(false);
      navigate("/recommendation-result", { state: { recommendationData: response } });
    } else {
      console.log("Form validation failed", errors);
    }
  };

  if (isLoading) {
    return (
      <div className="min-h-screen flex flex-col bg-[#F7F7F7] items-center justify-center">
        <RingLoader color='#000' size={50} />
        <p className="text-black text-[20px] font-bold">코디를 추천하는 중입니다...</p>
        <p className="text-[#828282] text-[14px] mt-2">잠시만 기다려 주세요.</p>
      </div>
    );
  }

  return (
    <div className="min-h-screen flex flex-col bg-[#F7F7F7]">
      <Header />
      <main className="flex flex-1 justify-center">
        <div className="w-full max-w-xl">
          <h1 className="font-bold text-[32px] text-black text-center mt-[70px] mb-[70px]">
            FitU
          </h1>
          <form onSubmit={handleSubmit} className="flex flex-col space-y-[100px]">
            <div>
              <label htmlFor="occasion" className="block font-bold text-[20px] text-black text-center mb-[15px]">
                  어떤 상황에서 입을 예정인가요? <span className="text-[#828282]">*</span>
              </label>
              <input
                type="text"
                id="occasion"
                name="occasion"
                placeholder="코디를 입을 상황(여행, 데이트 등)을 입력해주세요."
                className={`w-full h-[45px] rounded bg-white border border-[#828282] px-[10px] text-[14px] focus:outline-none ${
                  errors.occasion ? "border-red-500" : "border-[#828282] focus:border-black"
                }`}
                value={formData.occasion}
                onChange={handleChange}
              />
              {errors.occasion && (
                <p className="text-[12px] text-red-500 mt-1">{errors.occasion}</p>
              )}
            </div>
            <div>
              <label htmlFor="time" className="block font-bold text-[20px] text-black text-center mb-[15px]">
                  언제 입을 예정인가요? <span className="text-[#828282]">*</span>
              </label>
              <input
                  type="date"
                  id="time"
                  name="time"
                  className={`w-full h-[45px] rounded bg-white border px-[10px] text-[14px] focus:outline-none ${
                    errors.time ? "border-red-500" : "border-[#828282] focus:border-black"
                  }`}
                  value={formData.time}
                  onChange={handleChange}
                />
                {errors.time && (
                <p className="text-[12px] text-red-500 mt-1">{errors.time}</p>
              )}
            </div>
            <div>
              <label htmlFor="place" className="block font-bold text-[20px] text-black text-center mb-[15px]">
                  어디에서 입을 예정인가요? <span className="text-[#828282]">*</span>
              </label>
              <input
                type="text"
                id="place"
                name="place"
                placeholder="코디를 입을 장소(롯데월드, 경포대 등)을 입력해주세요."
                className={`w-full h-[45px] rounded bg-white border px-[10px] text-[14px] focus:outline-none ${
                  errors.place ? "border-red-500" : "border-[#828282] focus:border-black"
                }`}
                value={formData.place}
                onChange={handleChange}
              />
              {errors.place && (
                <p className="text-[12px] text-red-500 mt-1">{errors.place}</p>
              )}
            </div>
            <div>
              <div className="block font-bold text-[20px] text-black text-center">
                옷장 속 의상만 추천할까요? <span className="text-[#828282]">*</span>
              </div>
              <div className="block text-[14px] text-[#828282] text-center mb-[15px]">
                체크 박스 해제 시, 나의 옷장에 없는 옷도 추천될 수 있습니다.
              </div>
              <label className="flex items-center justify-center gap-[10px]">
                <input
                  type="checkbox"
                  id="onlyCloset"
                  name="onlyCloset"
                  className="w-[20px] h-[20px] border-[#828282] accent-black"
                  checked={formData.onlyCloset}
                  onChange={handleChange}
                />
                <span className="text-[14px] text-black">옷장 속 의상만 추천받기</span>
              </label>
            </div>
            <button type="submit" className="h-[45px] rounded bg-black text-[16px] text-white mb-12">
              코디 추천 받기
            </button>
          </form>
        </div>
      </main>
    </div>
  );
};

export default SetSituationPage;