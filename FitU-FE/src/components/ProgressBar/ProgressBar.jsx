import "./ProgressBar.styles.css";

const steps = [
  { label: "프로필 등록", step: 1 },
  { label: "의상 등록", step: 2 },
  { label: "완료", step: 3 }
];

const ProgressBar = ({ activeStep }) => {
  const totalSteps = steps.length;
  const width = `${(100 / (totalSteps - 1)) * (activeStep - 1)}%`;

  return (
    <div className="progress-steps">
      <div className="progress-steps__container">
        {steps.map(({ step, label }) => (
          <div className="progress-steps__item" key={step}>
            <div
              className={`progress-steps__circle ${activeStep >= step ? 'progress-steps__circle--completed' : ''}`}>
              {activeStep > step || (activeStep === step && step === steps.length) ? (
                <div className="progress-steps__checkmark">L</div>
              ) : (
                <span className="relative flex size-2">
                  <span className="absolute inline-flex h-full w-full animate-ping rounded-full bg-white opacity-75"></span>
                  <span className="relative inline-flex size-2 rounded-full bg-white"></span>
                </span>
              )}
            </div>
            <div className="progress-steps__label-container">
              <span className="progress-steps__label" key={step}>
                {label}
              </span>
            </div>
          </div>
        ))}
        <div className="progress-steps__filled-line" style={{ width: width }}></div>
      </div>
    </div>
  )
};

export default ProgressBar;