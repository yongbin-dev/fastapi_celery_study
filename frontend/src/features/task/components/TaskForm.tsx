import React, { useState } from 'react';

interface TaskFormProps {
  title: string;
  onSubmit: (data: any) => void;
  isLoading: boolean;
  fields: {
    name: string;
    label: string;
    type: 'text' | 'number' | 'email';
    placeholder?: string;
    defaultValue?: string | number;
    required?: boolean;
  }[];
}

export const TaskForm: React.FC<TaskFormProps> = ({
  title,
  onSubmit,
  isLoading,
  fields,
}) => {
  const [formData, setFormData] = useState<Record<string, any>>(() => {
    const initial: Record<string, any> = {};
    fields.forEach(field => {
      initial[field.name] = field.defaultValue || (field.type === 'number' ? 0 : '');
    });
    return initial;
  });

  const handleChange = (name: string, value: string | number) => {
    setFormData(prev => ({ ...prev, [name]: value }));
  };

  const handleSubmit = (e: React.FormEvent) => {
    e.preventDefault();
    onSubmit(formData);
  };

  return (
    <div className="bg-white p-6 rounded-lg shadow-md">
      <h3 className="text-lg font-semibold mb-4">{title}</h3>
      <form onSubmit={handleSubmit} className="space-y-4">
        {fields.map((field) => (
          <div key={field.name}>
            <label className="block text-sm font-medium text-gray-700 mb-1">
              {field.label}
            </label>
            <input
              type={field.type}
              value={formData[field.name]}
              onChange={(e) => handleChange(field.name, field.type === 'number' ? Number(e.target.value) : e.target.value)}
              placeholder={field.placeholder}
              required={field.required}
              className="w-full px-3 py-2 border border-gray-300 rounded-md focus:outline-none focus:ring-2 focus:ring-blue-500 focus:border-transparent"
            />
          </div>
        ))}
        <button
          type="submit"
          disabled={isLoading}
          className="w-full bg-blue-600 text-white py-2 px-4 rounded-md hover:bg-blue-700 focus:outline-none focus:ring-2 focus:ring-blue-500 disabled:opacity-50 disabled:cursor-not-allowed"
        >
          {isLoading ? '생성 중...' : '태스크 생성'}
        </button>
      </form>
    </div>
  );
};