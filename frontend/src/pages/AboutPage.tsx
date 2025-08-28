import React from 'react';

const AboutPage: React.FC = () => {
  return (
    <div className="min-h-screen flex items-center justify-center">
      <div className="text-center">
        <h1 className="text-4xl font-bold text-gray-900 mb-4">
          About
        </h1>
        <p className="text-lg text-gray-600">
          이 페이지는 About 페이지입니다.
        </p>
      </div>
    </div>
  );
};

export default AboutPage;