import React from 'react';

const HomePage: React.FC = () => {
  return (
    <div className="min-h-screen flex items-center justify-center">
      <div className="text-center">
        <h1 className="text-4xl font-bold text-gray-900 mb-4">
          Welcome to React App
        </h1>
        <p className="text-lg text-gray-600">
          프론트엔드 프로젝트가 준비되었습니다!
        </p>
      </div>
    </div>
  );
};

export default HomePage;