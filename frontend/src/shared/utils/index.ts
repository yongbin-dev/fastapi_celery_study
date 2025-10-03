export const cn = (...classes: (string | undefined | null | false)[]): string => {
  return classes.filter(Boolean).join(' ');
};

/**
 * 날짜를 한국 시간대 형식으로 포맷팅
 * 백엔드에서 이미 서울 시간대로 변환된 값이지만 Z가 붙어있어서 제거 후 포맷팅
 */
export const formatDate = (dateString: string): string => {
  if (!dateString) return '-';
  // Z를 제거하여 로컬 시간으로 처리
  const cleanDateString = dateString.replace('Z', '');
  return new Date(cleanDateString).toLocaleString('ko-KR', {
    year: 'numeric',
    month: '2-digit',
    day: '2-digit',
    hour: '2-digit',
    minute: '2-digit',
    second: '2-digit'
  });
};

export const debounce = <T extends (...args: any[]) => void>(
  fn: T,
  delay: number
): ((...args: Parameters<T>) => void) => {
  let timeoutId: NodeJS.Timeout;
  return (...args: Parameters<T>) => {
    clearTimeout(timeoutId);
    timeoutId = setTimeout(() => fn(...args), delay);
  };
};

export const sleep = (ms: number): Promise<void> => {
  return new Promise((resolve) => setTimeout(resolve, ms));
};

export * from './api';