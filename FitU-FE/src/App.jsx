import { BrowserRouter, Route, Routes } from "react-router-dom";
import { Toaster } from "react-hot-toast";
import "./App.css";
import SetSituationPage from './pages/SetSituationPage/SetSituationPage.jsx';
import RecommendationResultPage from './pages/RecommendationResultPage/RecommendationResultPage.jsx';
import ClosetRegistrationPage from "./pages/ClosetRegistrationPage/ClosetRegistrationPage.jsx";
import MyClosetPage from "./pages/MyClosetPage/MyClosetPage.jsx";
import SetProfilePage from "./pages/SetProfilePage";
import HomePage from "./pages/HomePage/HomePage.jsx";
import MyProfilePage from "./pages/MyProfilePage";
import CompletePage from "./pages/CompletePage.jsx";

function App() {
    return (
        <>
        <Toaster/>
            <BrowserRouter>
                <Routes>
                    <Route path='/' element={<HomePage />} />
                    <Route path='/set-profile' element={<SetProfilePage />} />
                    <Route path='/my-profile' element={<MyProfilePage />} />
                    <Route path='/my-closet' element={<MyClosetPage />} />
                    <Route path='/closet-add' element={<ClosetRegistrationPage showProgress={false} title='의상 등록' />} />
                    <Route path='/closet-registration' element={<ClosetRegistrationPage showProgress={true} title='FitU' />} />
                    <Route path='/completion' element={<CompletePage />} />
                    <Route path="/set-situation" element={<SetSituationPage />} />
                    <Route path="/recommendation-result" element={<RecommendationResultPage />} />
                </Routes>
            </BrowserRouter>
        </>
    );
}

export default App;