import React, { useState, useRef, useEffect } from "react";

const SkinTonePopover = () => {
    const [open, setOpen] = useState(false);
    const buttonRef = useRef(null);
    const popoverRef = useRef(null);

    useEffect(() => {
        if (!open) return;

        const handleClick = (e) => {
            if (
                buttonRef.current &&
                !buttonRef.current.contains(e.target) &&
                popoverRef.current &&
                !popoverRef.current.contains(e.target)
            ) {
                setOpen(false);
            }
        };

        document.addEventListener("mousedown", handleClick);

        return () => document.removeEventListener("mousedown", handleClick);
    }, [open]);

    return (
        <div className="relative flex items-center">
            <button
                type="button"
                ref={buttonRef}
                onClick={() => setOpen((v) => !v)}
                className="ml-2"
            >
                <svg className="w-5 h-5 text-black hover:text-gray-500" aria-hidden="true" fill="currentColor" viewBox="0 0 20 20">
                    <path fillRule="evenodd" d="M18 10a8 8 0 11-16 0 8 8 0 0116 0zm-8-3a1 1 0 00-.867.5 1 1 0 11-1.731-1A3 3 0 0113 8a3.001 3.001 0 01-2 2.83V11a1 1 0 11-2 0v-1a1 1 0 011-1 1 1 0 100-2zm0 8a1 1 0 100-2 1 1 0 000 2z" clipRule="evenodd"></path>
                </svg>
            </button>
            <div
                ref={popoverRef}
                className={`
                    absolute z-10 inline-block bg-white border border-gray-200 rounded-lg shadow-xs
                    transition-all duration-500 
                    ${open ? "opacity-100 scale-100 pointer-events-auto" : "opacity-0 scale-95 pointer-events-none"}
                    left-1/2 -translate-x-2/3 bottom-full mb-3
                    sm:w-[300px] sm:left-[200px] sm:bottom-auto sm:mb-0 sm:-translate-x-1/2
                `}
                style={{ minWidth: "16rem" }}
            >
                <div className="p-3 space-y-2 font-semibold text-[1rem]">
                    <p className="font-semibold">웜톤</p>
                    <p className="text-[14px] text-gray-500">피부에 노란빛이 도는 따뜻한 느낌의 톤</p>
                    <p className="font-semibold">쿨톤</p>
                    <p className="text-[14px] text-gray-500">피부에 푸른빛이 도는 차가운 느낌의 톤</p>
                    <p className="font-semibold">뉴트럴톤</p>
                    <p className="text-[14px] text-gray-500">웜톤과 쿨톤의 특징이 모두 섞여 있거나,<br />어느 한 쪽으로도 치우치지 않은 중립적인 피부톤</p>
                </div>
            </div>
        </div>
    );
}

export default SkinTonePopover;