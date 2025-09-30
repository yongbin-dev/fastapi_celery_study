import React, { useRef, useEffect } from 'react';
import type { TextBox } from '../types/ocr';

interface OcrImageProps {
  imageUrl: string;
  textBoxes: TextBox[];
}

const OcrImage: React.FC<OcrImageProps> = ({ imageUrl, textBoxes }) => {
  const canvasRef = useRef<HTMLCanvasElement>(null);

  useEffect(() => {
    const canvas = canvasRef.current;
    if (!canvas) return;

    const context = canvas.getContext('2d');
    if (!context) return;

    const image = new Image();
    image.src = imageUrl;
    image.onload = () => {
      canvas.width = image.width;
      canvas.height = image.height;
      context.drawImage(image, 0, 0);

      textBoxes.forEach((box) => {
        context.beginPath();
        context.lineWidth = 2;
        context.strokeStyle = 'rgba(255, 99, 71, 0.8)'; // Tomato color with opacity
        context.fillStyle = 'rgba(255, 99, 71, 0.3)'; // Lighter tomato with more opacity

        const [[x1, y1], [x2, y2], [x3, y3], [x4, y4]] = box.bbox;
        context.moveTo(x1, y1);
        context.lineTo(x2, y2);
        context.lineTo(x3, y3);
        context.lineTo(x4, y4);
        context.closePath();
        context.stroke();
        context.fill();
      });
    };
  }, [imageUrl, textBoxes]);

  return <canvas ref={canvasRef} className="max-w-full border" />;
};

export default OcrImage;
