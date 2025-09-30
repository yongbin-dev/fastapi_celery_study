import React from 'react';

interface ModalProps {
  isOpen: boolean;
  onClose: () => void;
  children: React.ReactNode;
}

const Modal: React.FC<ModalProps> = ({ isOpen, onClose, children }) => {
  if (!isOpen) return null;

  return (
    <div className="fixed inset-0 bg-black bg-opacity-50 z-50 flex justify-center items-center">
      <div className="bg-white p-4 rounded-lg shadow-lg max-w-4xl max-h-full overflow-auto">
        <div className="flex justify-end">
          <button onClick={onClose} className="text-black font-bold">
            X
          </button>
        </div>
        {children}
      </div>
    </div>
  );
};

export default Modal;
