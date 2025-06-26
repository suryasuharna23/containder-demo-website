// src/components/Kamera.jsx

"use client"; // Ini SANGAT PENTING!

import { useEffect, useRef } from 'react';

const Kamera = () => {
  // useRef digunakan untuk mendapatkan referensi langsung ke elemen <video> di DOM
  const videoRef = useRef(null);

  // useEffect akan berjalan setelah komponen di-render
  useEffect(() => {
    // Fungsi async untuk meminta akses kamera
    const getCameraStream = async () => {
      try {
        // Meminta izin pengguna untuk mengakses video (kamera)
        const stream = await navigator.mediaDevices.getUserMedia({
          video: { facingMode: { exact: "environment" } } // gunakan kamera belakang
        });

        // Jika ada elemen video dan kita berhasil mendapatkan stream
        if (videoRef.current) {
          // Setel stream dari kamera sebagai sumber video
          videoRef.current.srcObject = stream;
        }
      } catch (err) {
        // Tangani error jika pengguna menolak izin atau tidak ada kamera
        console.error("Error accessing camera: ", err);
        alert("Tidak dapat mengakses kamera. Pastikan Anda memberikan izin dan kamera terpasang.");

        // fallback ke kamera depan jika kamera belakang tidak tersedia
        navigator.mediaDevices.getUserMedia({ video: true }).then((stream) => {
          if (videoRef.current) {
            videoRef.current.srcObject = stream;
          }
        });
      }
    };

    getCameraStream();

    // Fungsi cleanup untuk mematikan kamera saat komponen di-unmount
    return () => {
      if (videoRef.current && videoRef.current.srcObject) {
        const stream = videoRef.current.srcObject;
        const tracks = stream.getTracks();
        tracks.forEach(track => track.stop()); // Matikan setiap track (video)
      }
    };
  }, []); // Array dependensi kosong berarti useEffect hanya berjalan sekali saat komponen mount

  return (
    <div className="w-full h-screen bg-black flex items-center justify-center">
      {/* Elemen video untuk menampilkan feed kamera */}
      <video
        ref={videoRef}
        autoPlay // Memulai video secara otomatis
        playsInline // Diperlukan untuk beberapa browser mobile
        muted // Mute video untuk menghindari feedback audio yang tidak diinginkan
        className="w-full h-full object-cover" // Styling dengan Tailwind CSS
      />
    </div>
  );
};

export default Kamera;