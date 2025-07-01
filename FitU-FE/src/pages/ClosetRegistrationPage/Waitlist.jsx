import WaitlistItem from "./WaitlistItem";

const Waitlist = ({ items, onRemoveItem }) => {
    return (
        <div className='w-full h-full'>
            {items.length === 0 ? (
                <div className='h-full w-full flex items-center justify-center '>
                    <p className='text-center text-[1rem] text-[#828282]'>아직 옷장에 넣을 옷이 없어요.</p>
                </div>
            ) : (
                <div
                    className={`
          grid grid-cols-2 sm:grid-cols-2 md:grid-cols-3 lg:grid-cols-4 gap-4 px-2
          ${items.length > 8 ? "h-[360px] overflow-y-auto" : ""}
        `}
                >
                    {/* 8개(2줄)까지는 스크롤 없이, 9개(3줄)부터 스크롤 생김 */}
                    {items.map((item) => (
                        <WaitlistItem key={item.id} item={item} onRemove={onRemoveItem}/>
                    ))}
                </div>
            )}
        </div>
    );
};

export default Waitlist;
