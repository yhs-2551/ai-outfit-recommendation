import { motion } from "framer-motion";

const GuideSection = () => {
  return (
    <section
      className="h-screen bg-white flex flex-col items-center justify-center"
    >
      <motion.div
        initial={{ opacity: 0, y: 50 }}
        whileInView={{ opacity: 1, y: 0 }}
        viewport={{ once: false, amount: 0.3 }}
        transition={{
          ease: "easeInOut",
          duration: 2.5,
          y: { duration: 2.5 },
        }}
        className="w-full flex flex-col items-center"
      >
        <img src="/logo.png" alt="FitU Logo" className="w-40 mb-4" />

        <h1 className="text-3xl md:text-4xl font-bold text-gray-900 mb-4">
          당신만을 위한 스타일 가이드
        </h1>
        <p className="text-center text-gray-500 mb-20 px-4">
          날짜, 장소, 상황만 입력하면 <br className="md:hidden" />
          FitU가 당신의 코디를 완성해드려요.
        </p>

        <div className="w-full max-w-5xl grid grid-cols-1 md:grid-cols-3 gap-8 text-center px-4">
          <div className="flex flex-col items-center">
            <h2 className="text-2xl font-semibold mb-3 tracking-wide">TIME</h2>
            <p className="text-base text-gray-600 leading-relaxed">
              원하는 날짜에 맞는 코디를 <br />찾고 계신가요?
            </p>
          </div>

          <div className="flex flex-col items-center border-l-2 border-r-2 border-gray-200 px-4">
            <h2 className="text-2xl font-semibold mb-3 tracking-wide">PLACE</h2>
            <p className="text-base text-gray-600 leading-relaxed">
              어디에서 입을 코디를<br />원하시나요?
            </p>
          </div>

          <div className="flex flex-col items-center">
            <h2 className="text-2xl font-semibold mb-3 tracking-wide">OCCASION</h2>
            <p className="text-base text-gray-600 leading-relaxed">
              데이트, 여행 등 상황에 맞는 <br />
              코디를 고민하고 계신가요?
            </p>
          </div>
        </div>
      </motion.div>
    </section>
  );
};

export default GuideSection;