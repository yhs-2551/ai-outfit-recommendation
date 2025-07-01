import React, { useState } from "react";
import { Swiper, SwiperSlide } from "swiper/react";
import { Navigation, Autoplay } from "swiper/modules";
import "swiper/css";
import "swiper/css/navigation";
import "./RecommendationCarousel.styles.css";
import MODEL_IMG from "../../assets/model1.jpg";

const recommendations = [
  {
    image: MODEL_IMG,
    title: "캠핑",
    subtitle: "활동은 자유롭게, 관리도 손쉽게",
    description: "선선한 바람, 흡습속건 블랙 티셔츠와 ...",
  },
  {
    image: MODEL_IMG,
    title: "러닝",
    subtitle: "가볍고 쾌적하게",
    description: "땀 걱정 없는 기능성 소재와 ...",
  },
  {
    image: MODEL_IMG,
    title: "데이트",
    subtitle: "스타일과 편안함 모두",
    description: "트렌디한 디자인과 편안한 착용감 ...",
  },
  {
    image: MODEL_IMG,
    title: "데이트",
    subtitle: "스타일과 편안함 모두",
    description: "트렌디한 디자인과 편안한 착용감 ...",
  },
  {
    image: MODEL_IMG,
    title: "데이트",
    subtitle: "스타일과 편안함 모두",
    description: "트렌디한 디자인과 편안한 착용감 ...",
  },
  {
    image: MODEL_IMG,
    title: "데이트",
    subtitle: "스타일과 편안함 모두",
    description: "트렌디한 디자인과 편안한 착용감 ...",
  },
];

const RecommendationCarouselSection = () => {
  const [activeIndex, setActiveIndex] = useState(0);

  return (
    <section className="carousel-bg">
      <h1 className="carousel-title">나만의 추천 코디, FitU</h1>
      <div className="carousel-outer">
        <Swiper
          modules={[Navigation, Autoplay]}
          slidesPerView="auto"
          centeredSlides
          spaceBetween={32}
          navigation
          autoplay={{ delay: 3500, disableOnInteraction: false }}
          loop
          grabCursor
          className="recommendation-swiper"
          onSlideChange={swiper => setActiveIndex(swiper.realIndex)}
        >
          {recommendations.map((item, idx) => (
            <SwiperSlide
              key={idx}
              className={`recommendation-slide${activeIndex === idx ? " active" : ""}`}
            >
              <div className={`carousel-card${activeIndex === idx ? " active" : ""}`}>
                <img src={item.image} alt={item.title} />
                {activeIndex === idx && (
                  <div className="carousel-desc">
                    <b>{item.title}</b>
                    <h3>{item.subtitle}</h3>
                    <p>{item.description}</p>
                  </div>
                )}
              </div>
            </SwiperSlide>
          ))}
        </Swiper>
      </div>
    </section>
  );
};

export default RecommendationCarouselSection;