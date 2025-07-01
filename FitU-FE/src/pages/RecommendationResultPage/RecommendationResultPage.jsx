import React from "react";
import { useLocation } from "react-router-dom";
import Header from "../../components/Header";
import Slider from "react-slick";
import "slick-carousel/slick/slick.css";
import "slick-carousel/slick/slick-theme.css";
import "./RecommendationResultPage.styles.css";

const settings = {
    className: "center",
    centerMode: true,
    infinite: true,
    centerPadding: "0px",
    slidesToShow: 3,
    speed: 500,
};

const RecommendationResultPage = () => {
    const location = useLocation();

    const recommendationData = location.state?.recommendationData;

    const { summary, weather, contents } = recommendationData;

    const [currentSlideIndex, setCurrentSlideIndex] = React.useState(0);

    const duplicatedContents = [...contents, ...contents];
  
    const currentContent = duplicatedContents[currentSlideIndex % contents.length];
  
    const updatedSettings = {
      ...settings,
      afterChange: (current) => setCurrentSlideIndex(current),
    };

  return (
    <div className="min-h-screen flex flex-col bg-[#F7F7F7]">
        <Header />
        <main className="flex flex-1 justify-center">
            <div className="w-full max-w-xl">
                <h1 className="font-bold text-[32px] text-black text-center mt-[70px] mb-[70px]">
                    추천 코디
                </h1>
                <h2 className="text-[22px] text-black text-center mb-[70px]">
                    {summary}
                </h2>
                <div className="slider-wrapper">
                    <Slider {...updatedSettings}>
                        {duplicatedContents.map((contentItem, index) => (
                            <div key={index} data-index={index + 1} className="book-cover">
                                <img src={contentItem.imageUrl} alt={`Outfit Combination ${index + 1}`}/>
                            </div>
                        ))}
                    </Slider>
                </div>
                <div className="rounded bg-white border border-gray-100 w-full h-[415px] p-6 text-base overflow-y-auto mt-[70px]">
                    <p className="whitespace-pre-line text-black mb-[10px]">
                        ✨ {weather}
                    </p>
                    <p className="whitespace-pre-line text-black mb-[10px]">
                        {currentContent.clothesCombination}
                    </p>
                    <p className="whitespace-pre-line text-black mb-[30px]">
                        {currentContent.description}
                    </p>
                    {currentContent.clothesImageUrls && currentContent.clothesImageUrls.length > 0 && (
                        <div className="flex flex-wrap gap-2 mb-4 justify-center">
                            {currentContent.clothesImageUrls.map((imgUrl, idx) => (
                                <img
                                    key={idx}
                                    src={imgUrl}
                                    alt={`Recommended piece ${idx + 1}`}
                                    className="w-24 h-24 object-cover rounded-md border border-gray-200"
                                />
                            ))}
                        </div>
                    )}
                </div>
            </div>
        </main>
    </div>
  );
};

export default RecommendationResultPage;