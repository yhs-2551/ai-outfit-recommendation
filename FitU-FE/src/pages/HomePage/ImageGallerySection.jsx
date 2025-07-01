import React, { useState } from "react";
import { motion, AnimatePresence } from "framer-motion";
import "./ImageGallerySection.styles.css";
import MODEL_IMG1 from "../../assets/model1.jpg";
import MODEL_IMG2 from "../../assets/model2.png";
import MODEL_IMG3 from "../../assets/model3.png";

const imageGroup = [
    {
        src: MODEL_IMG1,
        keyword: "데이트",
        title: "로맨틱한 무드의 플라워 롱 원피스",
        description: "은은한 플라워 패턴이 돋보이는 롱 원피스예요. 야외 데이트에 부담 없이 착용할 수 있고, 자연스러운 퍼프 소매가 러블리한 분위기를 더해줍니다. "
    },
    {
        src: MODEL_IMG2,
        keyword: "캠핑",
        title: "활동은 자유롭게, 관리도 손쉽게",
        description: "선선한 바람. 흡습속건 티셔츠라 땀에 금방 마르고 구김 걱정도 적어요. 조거 팬츠와 바로 매치하면 깔끔한 캠핑룩 완성."
    },
    {
        src: MODEL_IMG3,
        keyword: "여름 데일리",
        title: "시원하고 깔끔한 반팔 셔츠 스타일",
        description: "산뜻한 화이트 반팔 셔츠와 네이비 팬츠의 조합으로 누구나 부담 없이 입을 수 있는 데일리룩이에요."
    }
];

const ImageGallerySection = () => {
    const [selectedImage, setSelectedImage] = useState(null);

    return (
        <>
            <section className="relative w-full h-screen bg-white">
                <h2 className="text-black text-[2rem] p-[4rem] font-bold text-center">
                    나만의 추천 코디, FitU
                </h2>
                <p className="text-center text-[#828282] text-base font-medium -mt-8 mb-8">
                    AI가 추천한 코디예요.<br />
                    이미지를 클릭하면 자세히 볼 수 있어요!
                </p>
                <div className="image-gallery-container w-full">
                    {imageGroup.map((item, idx) => (
                        <motion.div
                            className="image-gallery-card"
                            key={idx}
                            onClick={() => setSelectedImage(item)}
                            whileHover={{ scale: 1.03 }}
                            transition={{ type: "tween", duration: 0.3 }}
                            layoutId={`image-${idx}`}
                        >
                            <img
                                src={item.src}
                                alt={item.description}
                            />
                        </motion.div>
                    ))}
                </div>

                <AnimatePresence>
                    {selectedImage && (
                        <motion.div
                            className="backdrop"
                            onClick={() => setSelectedImage(null)}
                            initial={{ opacity: 0 }}
                            animate={{ opacity: 1 }}
                            exit={{ opacity: 0 }}
                        >
                            <motion.div
                                className="modal-content"
                                onClick={(e) => e.stopPropagation()}
                                initial={{ y: 50, opacity: 0 }}
                                animate={{ y: 0, opacity: 1 }}
                                exit={{ y: 50, opacity: 0 }}
                            >
                                <img src={selectedImage.src} alt={selectedImage.description} />

                                <div className="modal-description">
                                    <p className="text-m font-bold">{selectedImage.keyword}</p>
                                    <p className="text-2xl font-bold mb-2">{selectedImage.title}</p>
                                    <p className="text-lg">
                                        {selectedImage.description}
                                    </p>
                                </div>
                            </motion.div>
                        </motion.div>
                    )}
                </AnimatePresence>
            </section>
        </>
    );
};

export default ImageGallerySection;