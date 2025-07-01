import Header from "../../components/Header";
import MAIN_BG from "../../assets/main-bg.jpg";
import { useNavigate } from "react-router-dom";
import GuideSection from "./GuideSection";
import ImageGallerySection from "./ImageGallerySection";
import Footer from "../../components/Footer/Footer";
import { motion } from "framer-motion";
import ProfileGuideSection from "./ProfileGuideSection";
import ClosetGuideSection from "./ClosetGuideSection";
import SituationGuideSection from "./SituationGuideSection";

const HomePage = () => {

  const navigate = useNavigate();

  const handleStartClick = () => {
    const userId = localStorage.getItem("userId");
    if (userId) {
      navigate("/set-situation");
    } else {
      navigate("/set-profile");
    }
  };

  return (
    <div>
      <Header />

      <section className="relative w-full h-screen">
        <img
          src={MAIN_BG}
          alt="home"
          className="absolute inset-0 w-full h-full object-cover z-0 brightness-75"
        />
        <motion.div
          className="absolute inset-0 flex flex-col items-center justify-center z-10"
          initial={{ opacity: 0 }}
          whileInView={{ opacity: 1 }}
          transition={{ duration: 3 }}
        >
          <h1 className="text-white text-4xl md:text-5xl font-bold text-center leading-tight mb-5">
            고민할 필요 없이<br />
            FitU로 간편하게
          </h1>
          <p className="text-white text-base md:text-xl mb-10 text-center">
            어디에서든 완벽한 순간을 찾다.
          </p>
          <button
            onClick={handleStartClick}
            className="cursor-pointer shadow px-10 py-2 bg-white text-black text-base font-bold rounded mt-2 text-center"
          >
            시작하기
          </button>
        </motion.div>
      </section>


      <GuideSection />
      <ProfileGuideSection />
      <ClosetGuideSection />
      <SituationGuideSection />
      <ImageGallerySection />


      <Footer />
    </div>
  );
}

export default HomePage;