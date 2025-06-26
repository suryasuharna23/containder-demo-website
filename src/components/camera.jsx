// src/components/Kamera.jsx

"use client"; // Ini SANGAT PENTING!

import { useEffect, useRef, useState } from 'react';

const Kamera = () => {
  const videoRef = useRef(null);
  const canvasRef = useRef(null);
  const [captured, setCaptured] = useState(null);
  const [showView, setShowView] = useState(false);
  const [showImage, setShowImage] = useState(false);

  useEffect(() => {
    const getCameraStream = async () => {
      try {
        const stream = await navigator.mediaDevices.getUserMedia({ video: true });
        if (videoRef.current) {
          videoRef.current.srcObject = stream;
        }
      } catch (err) {
        console.error("Error accessing camera: ", err);
        alert("Tidak dapat mengakses kamera. Pastikan Anda memberikan izin dan kamera terpasang.");
      }
    };

    getCameraStream();

    return () => {
      if (videoRef.current && videoRef.current.srcObject) {
        const stream = videoRef.current.srcObject;
        const tracks = stream.getTracks();
        tracks.forEach(track => track.stop());
      }
    };
  }, []);

  const handleCapture = () => {
    const video = videoRef.current;
    const canvas = canvasRef.current;
    if (video && canvas) {
      canvas.width = video.videoWidth;
      canvas.height = video.videoHeight;
      const ctx = canvas.getContext('2d');
      ctx.drawImage(video, 0, 0, canvas.width, canvas.height);
      const imageData = canvas.toDataURL('image/png');
      setCaptured(imageData);
      setShowView(true);
      setShowImage(false);
    }
  };

  const handleShowImage = () => {
    setShowImage(true);
  };

  return (
    <div className="flex flex-col items-center">
      {/* Kamera box */}
      <div className="relative w-[320px] h-[427px] bg-black rounded-xl overflow-hidden flex items-center justify-center">
        <video
          ref={videoRef}
          autoPlay
          playsInline
          muted
          className="w-full h-full object-cover"
        />
        {/* Tombol capture bulat */}
        <button
          onClick={handleCapture}
          className="absolute left-1/2 -translate-x-1/2 bottom-4 w-14 h-14 bg-white border-4 border-gray-400 rounded-full shadow-lg flex items-center justify-center active:scale-95 transition"
          aria-label="Capture"
        >
          <span className="block w-8 h-8 bg-red-500 rounded-full"></span>
        </button>
        <canvas ref={canvasRef} style={{ display: 'none' }} />
      </div>
      {/* Tombol lihat hasil di bawah kamera */}
      {showView && (
        <button
          onClick={handleShowImage}
          className="mt-8 px-6 py-2 bg-blue-600 text-white rounded-full shadow hover:bg-blue-700 transition"
        >
          Lihat Hasil
        </button>
      )}
      {/* Gambar hasil capture */}
      {showImage && captured && (
        <img
          src={captured}
          alt="Hasil Capture"
          className="mt-4 rounded-xl shadow-lg max-w-xs"
        />
      )}
    </div>
  );
};

export default Kamera;