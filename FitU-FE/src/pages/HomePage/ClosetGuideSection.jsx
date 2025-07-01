import React from "react";
import { motion } from "framer-motion";
import GUIDE_IMAGE from "../../assets/mock-up-closet.png";

const ClosetGuideSection = () => (
  <section className="w-full h-screen flex flex-col md:flex-row items-center justify-center bg-white px-4">
    <div className="flex-1 flex justify-center items-center h-full md:pl-24">
      <img
        src={GUIDE_IMAGE}
        className="w-auto max-h-full drop-shadow-xl object-cover"
        alt="의상 등록 목업"
      />
    </div>
    <motion.div
      initial={{ opacity: 0, y: 40 }}
      whileInView={{ opacity: 1, y: 0 }}
      transition={{ duration: 1.3, ease: "easeOut" }}
      className="flex-1 flex flex-col justify-center items-start md:items-start md:justify-center md:pl-8 md:pr-24 w-full h-full"
      style={{ minWidth: 320 }}
    >
      <h2 className="text-3xl md:text-4xl font-bold mb-8 leading-tight text-gray-900">
        옷장 등록,<br />
        <span className="text-[#828282] font-bold">AI가 분석해드려요</span>
      </h2>
      <div className="text-lg md:text-xl text-gray-800 mb-8 leading-relaxed space-y-6">
        <p>
          의상을 등록하면<br />
          <b>AI가 종류, 패턴, 색상까지 분석</b>해드려요.
        </p>
        <p>
          <b>최소 상/하의 3세트</b>를 등록해 주세요.<br />
        </p>
      </div>
    </motion.div>
  </section>
);

export default ClosetGuideSection; 