import { Link, useLocation } from 'react-router-dom';

const Header: React.FC = () => {
  const location = useLocation();

  const isActive = (path: string) => location.pathname === path;

  return (
    <header className="bg-white shadow-sm border-b sticky top-0 z-50">
      <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8">
        <div className="flex justify-between items-center h-16">
          <div className="flex items-center">
            <Link to="/" className="text-xl font-bold text-gray-900">
              React App
            </Link>
          </div>

          <nav className="flex items-center space-x-8">
            <Link
              to="/"
              className={`px-3 py-2 text-sm font-medium rounded-md transition-colors ${isActive('/')
                ? 'text-blue-600 bg-blue-50'
                : 'text-gray-700 hover:text-blue-600 hover:bg-gray-50'
                }`}
            >
              Home
            </Link>
            <Link
              to="/about"
              className={`px-3 py-2 text-sm font-medium rounded-md transition-colors ${isActive('/about')
                ? 'text-blue-600 bg-blue-50'
                : 'text-gray-700 hover:text-blue-600 hover:bg-gray-50'
                }`}
            >
              About
            </Link>
            <Link
              to="/pipelines"
              className={`px-3 py-2 text-sm font-medium rounded-md transition-colors ${isActive('/pipelines')
                ? 'text-blue-600 bg-blue-50'
                : 'text-gray-700 hover:text-blue-600 hover:bg-gray-50'
                }`}
            >
              Tasks
            </Link>
            <Link
              to="/ocr"
              className={`px-3 py-2 text-sm font-medium rounded-md transition-colors ${isActive('/ocr')
                ? 'text-blue-600 bg-blue-50'
                : 'text-gray-700 hover:text-blue-600 hover:bg-gray-50'
                }`}
            >
              ocr
            </Link>
            <Link
              to="/ocr-comparison"
              className={`px-3 py-2 text-sm font-medium rounded-md transition-colors ${isActive('/ocr-comparison')
                ? 'text-blue-600 bg-blue-50'
                : 'text-gray-700 hover:text-blue-600 hover:bg-gray-50'
                }`}
            >
              ocr-comparison
            </Link>
            <Link
              to="/contact"
              className={`px-3 py-2 text-sm font-medium rounded-md transition-colors ${isActive('/contact')
                ? 'text-blue-600 bg-blue-50'
                : 'text-gray-700 hover:text-blue-600 hover:bg-gray-50'
                }`}
            >
              Contact
            </Link>
          </nav>
        </div>
      </div>
    </header>
  );
};

export default Header;