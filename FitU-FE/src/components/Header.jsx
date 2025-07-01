import { Link, useLocation } from "react-router-dom";
import { useState } from "react";

const Header = () => {
    const userId = localStorage.getItem("userId");
    const [menuOpen, setMenuOpen] = useState(false);

    const location = useLocation();
    const isHomePage = location.pathname === "/";

    return (
        <>
            <nav className='shadow w-full bg-white h-[50px] fixed top-0 left-0 z-20'>
                <div className='h-[50px] w-full flex flex-wrap items-center justify-between px-[25px]'>
                    <Link to='/' className='px-2 flex items-center space-x-3'>
                        <img src='/logo-large.png' className='h-10 md:h-9' alt='FitU Logo' />
                    </Link>
                    <div className='flex md:order-2'>
                        {userId ? (
                            <>
                                <Link
                                    to='/my-profile'
                                    className='hidden md:flex text-black hover:bg-gray-100 font-medium rounded-lg text-sm px-4 py-2 text-center'
                                >
                                    내 프로필
                                </Link>
                                <Link
                                    to='/my-closet'
                                    className='hidden md:flex text-black hover:bg-gray-100 font-medium rounded-lg text-sm px-4 py-2 text-center'
                                >
                                    내 옷장
                                </Link>
                                <Link
                                    to='/set-situation'
                                    className='hidden md:flex text-black hover:bg-gray-100 font-medium rounded-lg text-sm px-4 py-2 text-center'
                                >
                                    추천 받기
                                </Link>
                            </>
                        ) : (
                            isHomePage && (
                                <Link
                                    to='/set-profile'
                                    className='hidden md:flex text-black hover:bg-gray-100 font-medium rounded-lg text-sm px-4 py-2 text-center'
                                >
                                    시작하기
                                </Link>
                            )
                        )}
                        <button
                            type='button'
                            className='inline-flex items-center p-2 w-10 h-10 justify-center text-sm text-gray-500 rounded-lg md:hidden hover:bg-gray-100 focus:outline-none focus:ring-2 focus:ring-gray-200'
                            onClick={() => setMenuOpen((v) => !v)}
                        >
                            <svg className='w-5 h-5' aria-hidden='true' fill='none' viewBox='0 0 17 14'>
                                <path stroke='currentColor' strokeLinecap='round' strokeLinejoin='round' strokeWidth='2' d='M1 1h15M1 7h15M1 13h15' />
                            </svg>
                        </button>
                    </div>
                </div>
            </nav>

            {menuOpen && (
                <div className='fixed top-14 left-0 w-full z-30 md:hidden px-2'>
                    <ul className='flex flex-col p-4 font-medium border border-gray-100 rounded-lg bg-gray-50 w-full'>
                        {userId ? (
                            <>
                                <li>
                                    <a href='/my-profile' className='block py-2 px-3 text-gray-900 rounded-lg hover:bg-black hover:text-white'>
                                        내 프로필
                                    </a>
                                </li>
                                <li>
                                    <a href='/my-closet' className='block py-2 px-3 text-gray-900 rounded-lg hover:bg-black hover:text-white'>
                                        내 옷장
                                    </a>
                                </li>
                            </>
                        ) : (
                            <li>
                                <a href='/set-profile' className='block py-2 px-3 text-gray-900 rounded-lg hover:bg-black hover:text-white'>
                                    시작하기
                                </a>
                            </li>
                        )}
                    </ul>
                </div>
            )}
        </>
    );
};

export default Header;
