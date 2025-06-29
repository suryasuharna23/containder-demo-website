// src/components/Kamera.jsx

"use client";

import { useEffect, useRef, useState } from 'react';

const Kamera = () => {
  const videoRef = useRef(null);
  const canvasRef = useRef(null);
  const [captured, setCaptured] = useState(null);
  const [isDropdownOpen, setDropdownOpen] = useState(false);
  const [result, setResult] = useState(null)

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
      // Dropdown tidak terbuka otomatis, sesuai permintaan
    }
  };

  const toggleDropdown = () => {
    setDropdownOpen(!isDropdownOpen);
  };

  useEffect(()=> {
    if (captured === null) return
    const fetchData = async () => {
      const res = await fetch('http://127.0.0.1:8000',{
        method: "POST",
        headers: {"Content-Type":"application/json"},
        body: JSON.stringify({image : captured})
      });
      const data = await res.json();
      setResult(data); 
    }
    fetchData();
  }, [captured]);

  return (
    <div className="flex flex-col items-center">
      {/* Kotak kamera */}
      <div className="relative w-[320px] h-[427px] bg-black rounded-xl overflow-hidden flex items-center justify-center shadow-lg border-4 border-white">
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

      {/* Dropdown untuk hasil foto, diletakkan di bawah kamera */}
      <div className="w-full max-w-xs mt-4">
        <button
          onClick={toggleDropdown}
          className="w-full px-4 py-2 bg-gray-200 text-left text-black rounded-md shadow-sm flex justify-between items-center"
        >
          <span>Hasil Foto</span>
          <svg
            className={`w-5 h-5 transform transition-transform ${
              isDropdownOpen ? 'rotate-180' : ''
            }`}
            fill="none"
            stroke="currentColor"
            viewBox="0 0 24 24"
            xmlns="http://www.w3.org/2000/svg"
          >
            <path
              strokeLinecap="round"
              strokeLinejoin="round"
              strokeWidth="2"
              d="M19 9l-7 7-7-7"
            ></path>
          </svg>
        </button>
        {isDropdownOpen && (
          <div className="mt-2 p-2 border border-gray-200 rounded-md shadow-lg bg-white">
            {captured ? (
              <img
                src={captured}
                alt="Hasil Capture"
                className="rounded-md w-full"
              />
            ) : (
              <p className="text-center text-gray-500 p-4">
                Anda belum mengambil gambar.
              </p>
            )}
          </div>
        )}
        {result && (
          <p className='text-red-600'>
            {JSON.stringify(result)}
          </p>
        )}
      </div>
    </div>
  );
};

export default Kamera;