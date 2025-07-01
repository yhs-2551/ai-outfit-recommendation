import React from "react";
import { motion } from "framer-motion";
import MOCKUP_IMAGE from "../../assets/mock-up-profile.png";

const ProfileGuideSection = () => (
  <section className="w-full h-screen flex flex-col md:flex-row items-center justify-center bg-black">
    <motion.div
      initial={{ opacity: 0, y: 40 }}
      whileInView={{ opacity: 1, y: 0 }}
      transition={{ duration: 1.3, ease: "easeOut" }}
      className="px-4 flex-1 flex flex-col justify-center items-start md:items-start md:justify-center md:pl-24 md:pr-8 w-full h-full"
      style={{ minWidth: 320 }}
    >
      <h2 className="text-3xl md:text-4xl font-bold mb-8 leading-tight text-white">
        프로필,<br />
        <span className="text-gray-300 font-bold">딱 맞게 추천받으려면</span>
      </h2>
      <div className="text-lg md:text-xl text-gray-200 mb-8 leading-relaxed space-y-6">
        <p>
          나만의 신체 정보와 피부톤을<br />
          <b>입력해 주세요.</b>
        </p>
        <p>
          전신사진을 업로드하면<br />
          <b>내 사진 위에 직접 코디를 입혀볼 수 있어요.</b>
        </p>
      </div>
    </motion.div>
    <div className="flex-1 flex justify-center items-center h-full">
      <img
        src={MOCKUP_IMAGE}
        className="w-auto h-[80vh] max-h-full object-contain drop-shadow-xl"
      />
    </div>
  </section>
);

export default ProfileGuideSection;