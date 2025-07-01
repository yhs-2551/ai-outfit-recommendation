import React from "react";
import "./Footer.styles.css";

const Footer = () => {
  const currentYear = new Date().getFullYear();

  return (
    <footer className="footer">
      <div className="footer-inner flex flex-col items-center py-6">
        <img src="/logo-white.png" className="w-16 h-16" alt="FitU Logo" />
        <div className="footer-slogan text-white text-base opacity-90 ">
          Find Your Perfect Style, <b>FitU</b>
        </div>
        <div className="footer-desc text-xs text-white opacity-70">
          AI가 추천하는 나만의 코디, FitU 에서 경험하세요.
        </div>
        <div className="footer-copy text-xs text-white opacity-60">
          &copy; {currentYear} FitU. All rights reserved.
        </div>
      </div>
    </footer>
  );
};

export default Footer;