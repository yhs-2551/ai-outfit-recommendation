import { Link } from "react-router-dom";
import Header from "../components/Header";
import ProgressBar from "../components/ProgressBar/ProgressBar";

const CompletePage = () => {
    return (
        <div className="min-h-screen bg-[#fafafa]">
            <Header />
            <h1 className="pt-[7.5rem] text-[2rem] font-bold text-center">FitU</h1>

            <ProgressBar activeStep={3} />

            <div className="flex flex-col items-center">
                <img
                    src="/logo.png"
                    alt="logo"
                    className="h-[150px] mt-[30px]"
                />
                <p className="text-[1.25rem] text-center mb-[100px]">
                    <span className="font-semibold">FitU</span>에 오신 것을 환영합니다! <br />
                    당신만을 위한 스타일, <span className="font-semibold">FitU</span>에서 시작하세요.
                </p>
                {/* TODO 상황 입력 페이지로 이동 */}
                <Link
                    to="/set-situation"
                    className="shadow cursor-pointer h-[43px] px-[1.375rem] py-[11px] bg-black text-[1rem] text-white rounded-lg text-center flex items-center justify-center"
                >
                    상황 입력하고 코디 추천 받기
                </Link>
            </div>
        </div>
    );
}

export default CompletePage;